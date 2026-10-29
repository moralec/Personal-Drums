#!/usr/bin/env python3
"""Measure the three play targets in img/source/scene.png and write them into index.html.

  python3 tools/measure.py            -> img/scene.webp, the LANES block in index.html, img/debug.png
Needs: pillow, numpy, opencv-python. Lane 0 head (cream drumhead), 1 rim (blue ring), 2 cup (red mug).
"""
import json, re, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'img' / 'source' / 'scene.png'
img = np.array(Image.open(SRC).convert('RGB'))
H, W = img.shape[:2]
r, g, b = [img[..., i].astype(int) for i in range(3)]

def clean(mask, k=5):
    m = mask.astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

def component(mask, seed):
    n, lab = cv2.connectedComponents(mask)
    return (lab == lab[seed[1], seed[0]]).astype(np.uint8) * 255

def path_of(mask, eps=2.0):
    """SVG path (even-odd) from the outer contour and any holes of a mask."""
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    d = []
    for c in cs:
        if cv2.contourArea(c) < 200: continue
        a = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        d.append('M' + ' L'.join(f'{x} {y}' for x, y in a) + 'Z')
    return ' '.join(d)

# blue rim band (the royal-blue ring and the lip under it)
blue = clean((b > r + 45) & (b > g + 25), 5)
rim = component(blue, (int(W * 0.34), int(H * 0.19)))  # top of the ring

# drumhead: everything enclosed by the blue ring (cream + the thin tan edge)
non_blue = cv2.bitwise_not(blue)
inner = component(non_blue, (680, 560))
# the component must not leak out through the bottom of the ring
assert inner.sum() / 255 < W * H * 0.2, 'head leaked out of the rim ring'
head = inner

# cup: red body + handle, dots filled in
red = clean((r > 150) & (g < 90) & (b < 90), 7)
cup = component(red, (1500, 800))
cs, hier = cv2.findContours(cup, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
filled = np.zeros_like(cup)
for c, hh in zip(cs, hier[0]):
    if hh[3] == -1: cv2.drawContours(filled, [c], -1, 255, -1)      # outer outline
for c, hh in zip(cs, hier[0]):
    if hh[3] != -1 and cv2.contourArea(c) > 6000: cv2.drawContours(filled, [c], -1, 0, -1)  # keep the handle gap open
cup = filled

lanes = {}
for i, (name, m) in enumerate([('head', head), ('rim', rim), ('cup', cup)]):
    ys, xs = np.nonzero(m)
    lanes[name] = {'lane': i, 'd': path_of(m), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                   'center': [int(xs.mean()), int(ys.mean())], 'area': int((m > 0).sum())}
    print(name, lanes[name]['bbox'], 'center', lanes[name]['center'], 'area', lanes[name]['area'], 'path chars', len(lanes[name]['d']))

# debug overlay
dbg = img.copy()
for m, col in [(head, (245, 166, 35)), (rim, (91, 155, 213)), (cup, (255, 107, 129))]:
    over = np.zeros_like(dbg); over[m > 0] = col
    dbg = cv2.addWeighted(dbg, 1, over, 0.55, 0)
Image.fromarray(dbg).resize((W // 2, H // 2)).save(ROOT / 'img' / 'debug.png')

Image.fromarray(img).save(ROOT / 'img' / 'scene.webp', quality=88, method=6)
block = '/* LANES:BEGIN */\nconst SCENE = ' + json.dumps({'w': W, 'h': H, 'lanes': [lanes[n] for n in ('head', 'rim', 'cup')]}, separators=(',', ':')) + ';\n/* LANES:END */'
html = (ROOT / 'index.html').read_text()
rx = re.compile(r'/\* LANES:BEGIN \*/[\s\S]*?/\* LANES:END \*/')
if rx.search(html):
    (ROOT / 'index.html').write_text(rx.sub(lambda m: block, html))
    print('wrote LANES block into index.html')
else:
    print('no LANES markers in index.html yet: block not written'); (ROOT / 'img' / 'lanes.json').write_text(block)
