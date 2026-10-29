# Mini Drummer: a MIDI play-along for a toddler with a toy drum and a cup

> **Area:** Personal · **Runs on:** local file / any static host · **Status:** in development

## What it does

Shows a drum (head and rim) and a red cup on screen. A song plays (the MIDI's non-drum parts, synthesised in the browser) and the drum part is translated to the three real things at home: a small drum, its rim, and a metal cup. Each target glows before a hit and flashes on it. Easy, Medium and Busy thin the pattern to a pace a 3.5-year-old can follow.

## How to use it

    node build.js        # after adding or changing a file in midi/
    python3 -m http.server 7433    # then open http://localhost:7433/index.html

Opening `index.html` directly also works. Songs: drop `<name>.mid` into `midi/`; optional titles and emoji in `midi/songs.json`.

## Where it runs

Nothing resident and not deployed yet. Planned: a static site like the guitar app.

## How it's built

| File | Role |
|---|---|
| `index.html` | The whole app, plus the generated `SONGS` block |
| `build.js` | MIDI parser and converter: drum mapping, the three busy levels, writes `SONGS` |
| `midi/` | Source `.mid` files and optional `songs.json` |

No dependencies and no outside services. Audio is Web Audio, generated in the page.

## Data and secrets

Progress (plays, favourites, level) in `localStorage` key `drumsProgress`. No keys, accounts or network calls. MIDI files are the owner's own.

## Related

Sister project: `~/claude/guitar`. Memory Palace member (`.palace`).
