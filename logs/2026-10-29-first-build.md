# 2026-10-29 · First build: MIDI -> three-target play-along

**Asked:** sister project to guitar, for a 3.5-year-old on a toy drum (head = snare, rim = hi-hat) and a metal cup (crash). On-screen instruments highlight what to play. Vision: scan a song's MIDI, map the drums to the three targets, play the rest of the MIDI as backing; "how busy" levels. Node build step like guitar, synth backing.

**Done:**
- Adopted into the Memory Palace (dashboard-app / personal).
- `build.js`: dependency-free SMF parser, GM drum -> lane map, Easy/Medium/Busy thinning, writes the `SONGS` block.
- `index.html`: library, song view (drum + rim + cup SVG, glow-before-hit, count-in, level/slow/hear-drums, tap-to-sound), Web Audio drum and note synth.
- Test song `midi/twinkle-twinkle.mid` (generated, public domain): 0.97 / 3.5 / 4.4 hits per second.

**Checked:** `node --check` on the page script; headless Chrome screenshots of both views; a headless play run (glow state and hit counts). **Not checked:** actual audio and timing by ear (headless audio clock does not advance); behaviour on a tablet.

**Then:** Carlos supplied `~/Downloads/Bon Jovi - Living on a Prayer.mid`; copied to `midi/livin-on-a-prayer.mid` and built: 123 bpm, 251 s, drum hits Easy/Medium/Busy = 210/691/955 (0.84/2.75/3.81 per s); at Easy head/rim/cup = 167/12/31. First real song, not yet tried by ear.
