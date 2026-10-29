# Mini Drummer

Single-file HTML play-along for a 3.5-year-old (Carlos's son). Three things to hit: a small drum head (snare), the drum's rim (hi-hat) and a red metal cup (crash / metal). They light up in time with a song.

Deploy: `./deploy.sh` (Netlify CLI; the site is not linked to GitHub because private songs ship only from there).

Sister project of `~/claude/guitar` (same shape: one `index.html`, Node build step, no CDN). Member of the Memory Palace (`.palace`: dashboard-app / personal). Open a session with `memory brief`. Decisions and gotchas go in `MEMORY.md`, session history in `logs/`.

## How a song gets in

`midi/<name>.mid` -> `node build.js` -> the generated `SONGS` block in `index.html` (between `/* SONGS:BEGIN */` and `/* SONGS:END */`; never hand-edit it). `node build.js --dry` prints the summary and writes nothing. Optional `midi/songs.json` gives `{ "<slug>": { "title", "emoji" } }`.

`build.js` has its own SMF parser (no dependencies). It maps General MIDI drum notes to the three targets (head: snare, toms, side stick; rim: closed/pedal hat, ride; cup: crash, splash, china, open hat). The kick has no target and stays in the backing. Every hit gets a minimum level: Easy / Medium / Busy (about 1 / 3.5 / 4.4 hits per second on the test song). Accents are placed first (cup, then head, then rim), and a hit kept at one level is kept at every level above it.

The whole MIDI plays through a built-in Web Audio synth, drums included. The "Every hit" level lights every mapped hit (the kick has no target and is heard only); Easy and Medium light a simpler subset while the full drums keep playing. Visuals follow what the speaker is playing (audio clock minus `outputLatency`/`baseLatency`). Tapping a target on screen plays its sound.

## The picture and its hit areas

`img/source/scene.png` is the generated artwork (drum, rim, cup). `python3 tools/measure.py` segments it by colour (needs pillow, numpy, opencv-python), writes `img/scene.webp`, and writes the three lane outlines (SVG paths in image pixels) into the `LANES` block of `index.html` (never hand-edit). Each lane gets a halo, a fill, an expanding ring and a tap area. The head's lit area is a smaller outline (`g`, `HEAD_GLOW` = 0.62 of the head in measure.py) so only the middle of the drumhead glows; its tap area is the whole head.

## Timeline

A canvas under the stage: three rows (Rim, Drum, Cup, top to bottom; `TL_ORDER`), one page of 8 beats at a time, an amber playhead sweeping left to right, then the next page. Dots are the hits for the chosen level (faded once played). Drawn by `drawTimeline(now)` from the same `laneHits` and heard-time as the glows. Pages assume the MIDI's first tempo; a song with tempo changes will drift against the beat lines. A new picture means re-running measure.py and checking `img/debug.png` (gitignored). Look and feel follows the guitar app (dark `#0f0f0f`, amber `#f5a623`, Helvetica Neue).

## Rules of thumb

- Tuned for a toddler: big targets, no reading needed, count-in 1-2-3-4. Adult controls (level, slow, hear drums) stay small.
- Progress is `localStorage` key `drumsProgress` (plays, starred, level). Per browser.
- Don't rename a song's file once in use: the slug is the progress key.
