#!/bin/sh
# Deploy index.html (+ songs-private.js if present) to Netlify by CLI. The repo is public and
# never carries private songs, so Netlify is NOT linked to GitHub: only this script publishes.
set -e
cd "$(dirname "$0")"
node build.js
d=$(mktemp -d)
cp index.html "$d/"
[ -f songs-private.js ] && cp songs-private.js "$d/"
netlify deploy --prod --dir "$d" --site "${NETLIFY_SITE:-drums-ag-insights}"
rm -rf "$d"
