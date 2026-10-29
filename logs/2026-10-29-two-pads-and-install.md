# 2026-10-29 · 2 pads, switches, installable and offline

## Goal
"A few tiny changes": 3 instruments is hard for a 3-year-old, so a flip to play with only drum and cup; then settings as switches above the stage, saved; then installable on macOS with an icon, and offline.

## Done
- `index.html`: 2 pads mode (rim filtered out of `laneHits`, hidden and untappable, timeline two rows); Slow / 2 pads / Left-handed as `.sw` switches in a row above the stage; Slow now saved (`prog.slow`); manifest and icon links, Apple web-app meta tags; service worker registration.
- `manifest.webmanifest`, `tools/icon.py` -> `img/icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, `sw.js` (new). `deploy.sh` ships them.
- Commits: `040fc2c` (2 pads, switches, installable), `5e3a225` (offline).

## Decisions
- 2 pads drops the rim rather than merging it. Why: the hat is the busy lane (8ths/16ths); merging it into the drum or the cup makes one pad too dense. The hat is still heard.
- Tapping the old rim spot does nothing in 2 pads (Carlos did not answer the optional "still make a sound?" question; simplest chosen).
- Switches (not pills) for the three on/off settings; Level stays a segmented control beside Play.
- Service worker is network first so a deploy shows immediately; cost is a wait on a hung connection.
- Icon background sampled from the artwork's own corner (`#131313`-ish), not `--bg`, or the crop shows a lighter box. First render had that seam.

## Corrections
- None beyond the requests. Carlos: "I think these setup settings should come above the main screen as switches?" and "they should also be saved to local memory".

## Open
- Nothing here was tested in a browser: the Chrome extension was not connected. Check by ear/eye: the switch row on a phone (wrap), the stage height with the new row, install from Safari/Chrome, and offline (open online once, then wifi off).
- Icon is the drum only; the cup is not in it. Carlos may want to see the icon in the Dock.

## Deployed
`./deploy.sh` -> https://drums.ag-insights.co.uk (deploy 6ae35466745ad3905e41f442). sw.js, manifest and icons answer 200.
