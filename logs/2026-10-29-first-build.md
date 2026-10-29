# 2026-10-29 · First build: MIDI -> three-target play-along

**Asked:** sister project to guitar, for a 3.5-year-old on a toy drum (head = snare, rim = hi-hat) and a metal cup (crash). On-screen instruments highlight what to play. Vision: scan a song's MIDI, map the drums to the three targets, play the rest of the MIDI as backing; "how busy" levels. Node build step like guitar, synth backing.

**Done:**
- Adopted into the Memory Palace (dashboard-app / personal).
- `build.js`: dependency-free SMF parser, GM drum -> lane map, Easy/Medium/Busy thinning, writes the `SONGS` block.
- `index.html`: library, song view (drum + rim + cup SVG, glow-before-hit, count-in, level/slow/hear-drums, tap-to-sound), Web Audio drum and note synth.
- Test song `midi/twinkle-twinkle.mid` (generated, public domain): 0.97 / 3.5 / 4.4 hits per second.

**Checked:** `node --check` on the page script; headless Chrome screenshots of both views; a headless play run (glow state and hit counts). **Not checked:** actual audio and timing by ear (headless audio clock does not advance); behaviour on a tablet.

**Then:** Carlos supplied `~/Downloads/Bon Jovi - Living on a Prayer.mid`; copied to `midi/livin-on-a-prayer.mid` and built: 123 bpm, 251 s, drum hits Easy/Medium/Busy = 210/691/955 (0.84/2.75/3.81 per s); at Easy head/rim/cup = 167/12/31. First real song, not yet tried by ear.

**Published (Carlos asked for a public GitHub repo and a Netlify deploy):**
- Repo: https://github.com/moralec/Personal-Drums (public). Carries Twinkle only.
- Private songs: `midi/private/*.mid` -> `songs-private.js`, both gitignored. Carlos chose "public repo without it, deploy with it": the Netlify site serves the Bon Jovi data, the repo does not.
- Netlify project `drums-ag-insights` (id a341d2f6-1441-4fc5-bfc1-06142b28f60e), https://drums-ag-insights.netlify.app, custom domain `drums.ag-insights.co.uk` set on the project. NOT linked to GitHub: `./deploy.sh` is the only publisher (it ships `index.html` + `songs-private.js` from a temp dir, so `midi/`, logs and MEMORY are not served).
- DNS for ag-insights.co.uk is at IONOS (ui-dns), so the CNAME `drums` -> `drums-ag-insights.netlify.app` is a manual step for Carlos.

**Second pass (same day):** restyled to match guitar (dark/amber); drums now always play in full and the top level is "Every hit" (all mapped hits, 4.0/s on Livin' on a Prayer); visuals use output-latency compensation. Carlos generated `img/source/scene.png` (2000x1493); `tools/measure.py` measured head/rim/cup outlines (colour segmentation) and the page draws halo, fill, ripple and tap area on those exact paths. Checked in headless Chrome with forced glow states; timing by ear still to do.

**Third pass:** head glow shrunk to the middle of the drumhead (measure.py `g` outline); added the 3-row paged timeline (`drawTimeline`). Checked in headless Chrome with forced states (note: a screenshot capture triggers a resize, which redraws the idle timeline; test copies drop that listener). Not yet played through by ear.

**Fourth pass:** timeline rows reordered (rim, drum, cup). Level logic replaced by note values (quarters / eighths / 16ths+): Livin' on a Prayer 692 / 937 / 1006 hits (2.8 / 3.7 / 4.0 per s); Twinkle 75 / 126 / 129. Discussed 'all snares at Easy plus a few others' first, then Carlos chose the note-value rule instead.

**Fourth pass:** timeline rows reordered (rim, drum, cup). Level logic replaced by note values: Quarters / Eighths / 16ths / All hits. Livin' on a Prayer 692 / 937 / 965 / 1006 hits; Twinkle 75 / 126 / 129 / 129. 'All hits' is the song untouched. Discussed 'all snares at Easy plus a few others' first; Carlos chose the note-value rule instead.

**Fifth pass:** added half notes as the easiest level and renamed the buttons Level 1-5 (note value shown underneath). Livin' on a Prayer 397 / 692 / 937 / 965 / 1006; Twinkle 27 / 75 / 126 / 129 / 129.

**Sixth pass:** levels named Beginner / Easy / Medium / Hard / Expert (caption: Level N and the note value).
