# 2026-10-30 — real recording aligned to the MIDI

- Carlos asked for the real song (voices, other instruments) in place of the synth. Source: `~/Downloads/01 Livin' On A Prayer.m4a` (his iTunes purchase, 4:11).
- `tools/align.py <slug> <recording>` (needs ffmpeg, numpy, scipy, librosa): first version fitted a straight line on drums + a drum-only correction every 10 s; Carlos heard it off, mostly at the start (intro has no drums; the +-150 ms search found nothing and fell back to 0; the true drift was ~200 ms). Rewritten as DTW on harmony (coarse) + per-bar onset/chroma search with Viterbi smoothing, fade-in/out handled; 43% -> 91% of drum hits within 40 ms of a recording onset. It also writes `audio/<slug>.m4a` and `-slow.m4a` (96k AAC, 0.6x atempo) and `audio` into `midi/songs.json`.
- `build.js` moves every time in the song onto the recording's clock (`audio.a/b/map`), adds `beat`, `beat0`, `audio`, `audioSlow`; `--raw-notes <slug>` prints MIDI-time notes for the tool.
- `index.html`: `startSong` is async, loads the file (decoded with an OfflineAudioContext, preloaded on song view), starts a BufferSource at `t0`; `schedule()` skips the synth when the recording plays; falls back to the synth if the file fails to load. Timeline uses `song.beat`/`beat0`.
- `deploy.sh` ships `audio/`; `audio/` is gitignored (public repo).
- NOT tested in a browser (Chrome extension not connected): sync by ear, Slow (0.6x file), loading state (⏳ on the play button), offline cache of the audio.
- Last MIDI drum hit maps ~1.5 s past the end of the file (outro); harmless.
- Second pass (same day): per-bar map, `beats` array for the timeline grid, `audio.end` (recording fades out, MIDI continues: later events dropped, `dur` = end + 1.5 s). Lessons recorded in MEMORY.md as general rules. Not redeployed yet; not heard in a browser.
