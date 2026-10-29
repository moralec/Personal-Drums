# Mini Drummer

Single-file HTML play-along for a 3.5-year-old (Carlos's son). Three things to hit: a small drum head (snare), the drum's rim (hi-hat) and a red metal cup (crash / metal). They light up in time with a song.

Sister project of `~/claude/guitar` (same shape: one `index.html`, Node build step, no CDN). Member of the Memory Palace (`.palace`: dashboard-app / personal). Open a session with `memory brief`. Decisions and gotchas go in `MEMORY.md`, session history in `logs/`.

## How a song gets in

`midi/<name>.mid` -> `node build.js` -> the generated `SONGS` block in `index.html` (between `/* SONGS:BEGIN */` and `/* SONGS:END */`; never hand-edit it). `node build.js --dry` prints the summary and writes nothing. Optional `midi/songs.json` gives `{ "<slug>": { "title", "emoji" } }`.

`build.js` has its own SMF parser (no dependencies). It maps General MIDI drum notes to the three targets (head: snare, toms, side stick; rim: closed/pedal hat, ride; cup: crash, splash, china, open hat). The kick has no target and stays in the backing. Every hit gets a minimum level: Easy / Medium / Busy (about 1 / 3.5 / 4.4 hits per second on the test song). Accents are placed first (cup, then head, then rim), and a hit kept at one level is kept at every level above it.

The backing is a built-in Web Audio synth: all non-drum notes plus the kick. "Hear drums" adds the original drum track. Tapping a target on screen plays its sound.

## Rules of thumb

- Tuned for a toddler: big targets, no reading needed, count-in 1-2-3-4. Adult controls (level, slow, hear drums) stay small.
- Progress is `localStorage` key `drumsProgress` (plays, starred, level). Per browser.
- Don't rename a song's file once in use: the slug is the progress key.
