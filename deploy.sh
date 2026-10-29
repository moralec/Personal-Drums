#!/bin/sh
# Deploy index.html (+ songs-private.js if present) to Netlify by CLI. The repo is public and
# never carries private songs, so Netlify is NOT linked to GitHub: only this script publishes.
set -e
cd "$(dirname "$0")"
node build.js
d=$(mktemp -d)
cp index.html "$d/"
mkdir "$d/img" && cp img/scene.webp "$d/img/"
[ -f songs-private.js ] && cp songs-private.js "$d/"
netlify deploy --prod --dir "$d" --site "${NETLIFY_SITE:-a341d2f6-1441-4fc5-bfc1-06142b28f60e}"  # drums-ag-insights
rm -rf "$d"
