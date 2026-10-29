#!/usr/bin/env node
// midi/*.mid -> the SONGS block in index.html.
//   node build.js            convert every midi/*.mid and rewrite index.html
//   node build.js --dry      convert and print the summary, write nothing
// midi/*.mid go into index.html (public). midi/private/*.mid go into songs-private.js instead (gitignored, shipped by deploy.sh only).
// Optional midi/songs.json: { "<slug>": { "title": "...", "emoji": "..." } }

const fs = require('fs');
const path = require('path');

const MIDI_DIR = path.join(__dirname, 'midi');
const HTML = path.join(__dirname, 'index.html');
const DRY = process.argv.includes('--dry');

// ---------- SMF parser ----------

function parseMidi(buf) {
  let p = 0;
  const u32 = () => { const v = buf.readUInt32BE(p); p += 4; return v; };
  const u16 = () => { const v = buf.readUInt16BE(p); p += 2; return v; };
  if (buf.toString('latin1', 0, 4) !== 'MThd') throw new Error('not a MIDI file');
  p = 4;
  const hlen = u32();
  const format = u16(), ntrks = u16(), division = u16();
  p = 8 + hlen;
  if (division & 0x8000) throw new Error('SMPTE time division is not supported');

  const events = []; // { tick, kind, ch, a, b, ord }
  const tempos = [], sigs = [];
  for (let t = 0; t < ntrks; t++) {
    if (buf.toString('latin1', p, p + 4) !== 'MTrk') throw new Error('bad track header');
    p += 4;
    const len = u32();
    const end = p + len;
    let tick = 0, status = 0;
    const vlq = () => { let v = 0, b; do { b = buf[p++]; v = (v << 7) | (b & 0x7f); } while (b & 0x80); return v; };
    while (p < end) {
      tick += vlq();
      let s = buf[p];
      if (s & 0x80) { p++; if (s < 0xf0) status = s; } else s = status; // running status
      if (s === 0xff) {
        const type = buf[p++], len = vlq();
        if (type === 0x51) tempos.push({ tick, us: buf.readUIntBE(p, 3) });
        if (type === 0x58) sigs.push({ tick, num: buf[p], den: 1 << buf[p + 1] });
        p += len;
      } else if (s === 0xf0 || s === 0xf7) {
        p += vlq();
      } else {
        const hi = s & 0xf0, ch = s & 0x0f;
        const a = buf[p++];
        const b = (hi === 0xc0 || hi === 0xd0) ? 0 : buf[p++];
        if (hi === 0x90 && b > 0) events.push({ tick, kind: 'on', ch, a, b, ord: 2 });
        else if (hi === 0x80 || hi === 0x90) events.push({ tick, kind: 'off', ch, a, ord: 1 });
        else if (hi === 0xc0) events.push({ tick, kind: 'prog', ch, a, ord: 0 });
      }
    }
    p = end;
  }
  events.sort((x, y) => x.tick - y.tick || x.ord - y.ord);
  tempos.sort((x, y) => x.tick - y.tick);
  return { format, division, events, tempos, sigs };
}

// ---------- notes + timing ----------

function tickToSecFn(division, tempos) {
  const segs = []; // { tick, sec, us }
  let sec = 0, last = { tick: 0, us: 500000 };
  segs.push({ tick: 0, sec: 0, us: 500000 });
  for (const t of tempos) {
    sec += (t.tick - last.tick) * last.us / division / 1e6;
    if (t.tick === 0) segs[0].us = t.us; else segs.push({ tick: t.tick, sec, us: t.us });
    last = { tick: t.tick, us: t.us };
  }
  return tick => {
    let s = segs[0];
    for (const g of segs) { if (g.tick <= tick) s = g; else break; }
    return s.sec + (tick - s.tick) * s.us / division / 1e6;
  };
}

function extractNotes(midi) {
  const prog = Array(16).fill(0);
  const open = new Map(); // "ch:note" -> [{tick, vel, prog}]
  const notes = [];
  let lastTick = 0;
  for (const e of midi.events) {
    lastTick = Math.max(lastTick, e.tick);
    if (e.kind === 'prog') prog[e.ch] = e.a;
    else if (e.kind === 'on') {
      const k = e.ch + ':' + e.a;
      if (!open.has(k)) open.set(k, []);
      open.get(k).push({ tick: e.tick, vel: e.b, prog: prog[e.ch], ch: e.ch, note: e.a });
    } else if (e.kind === 'off') {
      const st = open.get(e.ch + ':' + e.a);
      if (st && st.length) { const n = st.shift(); notes.push({ ...n, end: e.tick }); }
    }
  }
  for (const st of open.values()) for (const n of st) notes.push({ ...n, end: lastTick });
  return notes;
}

// ---------- drum mapping + "how busy" ----------

// GM drum note -> lane. 0 = drum head (snare, toms), 1 = rim (hi-hat, ride), 2 = cup (crash, open hat).
// The kick (35/36) has no instrument: it stays in the backing only.
const LANE = {
  38: 0, 40: 0, 37: 0, 41: 0, 43: 0, 45: 0, 47: 0, 48: 0, 50: 0,
  42: 1, 44: 1, 51: 1, 53: 1, 59: 1,
  46: 2, 49: 2, 52: 2, 55: 2, 57: 2,
};
const RANK = { 2: 0, 0: 1, 1: 2 };

// Level 1 Easy, 2 Medium, 3 Busy. Hits kept at a level are always kept at the next one up.
// Within a level, hits are placed cup first, then head, then rim, so a crash is never crowded out by a hat.
const LEVELS = [
  { grid: 1,    laneGap: [0.60, 0.60, 4.0], gap: 0.60, simul: false },
  { grid: 0.5,  laneGap: [0.30, 0.30, 2.0], gap: 0.15, simul: true  },
  { grid: 0,    laneGap: [0.10, 0.10, 0.6], gap: 0,    simul: true  },
];

function onGrid(beat, grid) {
  if (!grid) return true;
  const r = beat / grid;
  return Math.abs(r - Math.round(r)) * grid < 0.07;
}

function assignLevels(hits) {
  // hits: [{ sec, beat, lane }] sorted by time. Returns minLevel per hit (1..3), or 4 if never shown.
  const minLevel = hits.map(() => 4);
  const kept = []; // indexes kept so far
  LEVELS.forEach((L, li) => {
    const order = hits.map((_, i) => i)
      .sort((a, b) => RANK[hits[a].lane] - RANK[hits[b].lane] || hits[a].sec - hits[b].sec); // accents first, then time
    const accepted = kept.slice();
    for (const i of order) {
      if (minLevel[i] <= li + 1) continue; // already shown at a lower level
      const h = hits[i];
      if (!onGrid(h.beat, L.grid)) continue;
      let ok = true;
      for (const j of accepted) {
        const dt = Math.abs(hits[j].sec - h.sec);
        const same = hits[j].lane === h.lane;
        if (same && dt < L.laneGap[h.lane]) { ok = false; break; }
        if (!same && dt < L.gap && !(L.simul && dt < 0.03)) { ok = false; break; }
      }
      if (ok) { accepted.push(i); minLevel[i] = li + 1; }
    }
    kept.length = 0; kept.push(...accepted);
  });
  return minLevel;
}

// ---------- one song ----------

const r3 = x => Math.round(x * 1000);

function convert(file, meta) {
  const midi = parseMidi(fs.readFileSync(file));
  const tsec = tickToSecFn(midi.division, midi.tempos);
  const notes = extractNotes(midi);
  const slug = path.basename(file, path.extname(file)).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const title = (meta && meta.title) || path.basename(file, path.extname(file)).replace(/[-_]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  const drumsAll = notes.filter(n => n.ch === 9).sort((a, b) => a.tick - b.tick);
  const pitched = notes.filter(n => n.ch !== 9).sort((a, b) => a.tick - b.tick);

  const hits = drumsAll
    .filter(n => LANE[n.note] !== undefined)
    .map(n => ({ sec: tsec(n.tick), beat: n.tick / midi.division, lane: LANE[n.note] }));
  const levels = assignLevels(hits);

  const sig = midi.sigs[0] || { num: 4, den: 4 };
  const bpm = Math.round(60e6 / (midi.tempos[0] ? midi.tempos[0].us : 500000));
  const pack = n => [r3(tsec(n.tick)), r3(tsec(n.end) - tsec(n.tick)), n.note, n.vel];
  const isBass = n => n.prog >= 32 && n.prog <= 39;
  const song = {
    slug, title, emoji: (meta && meta.emoji) || '🎵', bpm,
    countIn: sig.den === 4 ? sig.num : 4,
    dur: Math.round(Math.max(...notes.map(n => tsec(n.end))) * 100) / 100,
    hits: hits.map((h, i) => [r3(h.sec), h.lane, levels[i]]).filter(h => h[2] <= 3),
    drums: drumsAll.map(n => [r3(tsec(n.tick)), n.note, n.vel]),
    bass: pitched.filter(isBass).map(pack),
    lead: pitched.filter(n => !isBass(n)).map(pack),
  };
  const per = [1, 2, 3].map(l => song.hits.filter(h => h[2] <= l).length);
  const perSec = song.dur ? per.map(n => (n / song.dur).toFixed(2)) : [];
  console.log(`${slug}: ${bpm} bpm, ${song.dur}s, drum hits easy/medium/busy = ${per.join('/')} (${perSec.join('/')} per s), ` +
    `${song.bass.length} bass + ${song.lead.length} lead notes, ${song.drums.length} drum notes`);
  if (!per[0]) console.warn(`  WARN ${slug}: no hits survive at Easy (no drum track on channel 10?)`);
  return song;
}

// ---------- main ----------

const metaFile = path.join(MIDI_DIR, 'songs.json');
const metas = fs.existsSync(metaFile) ? JSON.parse(fs.readFileSync(metaFile, 'utf8')) : {};
const slugOf = f => f.replace(/\.midi?$/i, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function convertDir(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const f of fs.readdirSync(dir).filter(f => /\.midi?$/i.test(f)).sort()) {
    try { out.push(convert(path.join(dir, f), metas[slugOf(f)])); }
    catch (err) { console.error(`FAIL ${f}: ${err.message}`); process.exitCode = 1; }
  }
  return out;
}

const songs = convertDir(MIDI_DIR);
const priv = convertDir(path.join(MIDI_DIR, 'private'));
if (!songs.length && !priv.length) { console.error('no .mid files in midi/ or midi/private/'); process.exit(1); }

if (!DRY) {
  const html = fs.readFileSync(HTML, 'utf8');
  const re = /\/\* SONGS:BEGIN \*\/[\s\S]*?\/\* SONGS:END \*\//;
  if (!re.test(html)) { console.error('SONGS markers not found in index.html'); process.exit(1); }
  const block = `/* SONGS:BEGIN */\nconst SONGS = ${JSON.stringify(songs)};\n/* SONGS:END */`;
  fs.writeFileSync(HTML, html.replace(re, () => block));
  const privFile = path.join(__dirname, 'songs-private.js');
  if (priv.length) fs.writeFileSync(privFile, `const SONGS_PRIVATE = ${JSON.stringify(priv)};\n`);
  else if (fs.existsSync(privFile)) fs.unlinkSync(privFile);
  console.log(`wrote ${songs.length} public song(s) into index.html, ${priv.length} private into songs-private.js`);
}
