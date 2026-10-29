# Memory: Mini Drummer

- **Audience is a 3.5-year-old** (Carlos, 2026-10-29). Real kit at home is a toy drum (head = snare, rim = hi-hat) and a red metal cup (crash). Design for big targets and no reading.
- **Songs come from MIDI**, converted at build time like the guitar pipeline (Carlos: "same as the guitar with node, and synth is fine"). Backing is a built-in synth, not samples.
- **Kick has no target**: it plays in the backing only. Open hat goes to the cup (accent), ride to the rim.
- **Easy/Medium/Busy** thinning places accents first (cup, head, rim); an earlier time-ordered pass dropped crashes behind snare hits.
- **Source files are the owner's:** Carlos owns the CDs of the songs he'll convert. A CD rip is audio, not MIDI; a MIDI has to be supplied or made from the audio.
- Headless Chrome's audio clock stays at 0 under `--virtual-time-budget`, so timing can't be tested that way; test by ear in a real browser.
- **Public repo, private songs** (Carlos, 2026-10-29): repo `moralec/Personal-Drums` is public; copyrighted songs live in `midi/private/` and `songs-private.js` (gitignored) and are deployed to Netlify only by `./deploy.sh`. Never link the Netlify site to GitHub (it would deploy without them) and never commit those files.
- **Netlify CLI takes the project id, not the name**, for `--site` (`drums-ag-insights` -> a341d2f6-…). ag-insights.co.uk DNS is at IONOS, not Netlify: a new subdomain needs a CNAME added by hand.
