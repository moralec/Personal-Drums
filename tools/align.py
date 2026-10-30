#!/usr/bin/env python3
"""Align a song's MIDI to the real recording bar by bar and prepare the audio files.

    python3 tools/align.py <slug> "<recording>.m4a"

Needs ffmpeg and  pip install numpy scipy librosa.  The band is not a click track: it drifts by 100-300 ms and speeds up in places,
so no straight line fits. And drums alone cannot tell a beat or a bar apart (the groove repeats), so:
  1. coarse map: DTW of the MIDI bass+lead harmony against the recording's chroma (gaps allowed, so a different ending would show up),
     smoothed into a MIDI-time -> recording-time curve;
  2. per bar: slide that bar's notes (drum, bass and lead onsets against the recording's onset strength, plus harmony) +-0.3 s around
     the curve, then pick one offset per bar with a smoothness penalty (Viterbi), so quiet bars (the drum-less intro) follow their neighbours;
  3. write the knots (one per bar) to midi/songs.json -> audio.map, plus audio/<slug>.m4a and audio/<slug>-slow.m4a (0.6x, pitch kept).
Then run  node build.js  to put every time in the song on the recording's clock. The report at the end says how many drum hits land
on a recording onset (within 40 ms) with the straight line and with the bar map: that is the number to watch.
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, librosa
from scipy.ndimage import gaussian_filter1d, maximum_filter1d, uniform_filter1d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug, src = sys.argv[1], sys.argv[2]
SLOW = 0.6          # keep in step with `speed` in index.html
SR, HOP = 22050, 256
fps = SR / HOP

with tempfile.TemporaryDirectory() as tmp:
    wav = os.path.join(tmp, 'a.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', str(SR), wav], check=True)
    y, _ = librosa.load(wav, sr=SR, mono=True)
dur = len(y) / SR

raw = subprocess.run(['node', os.path.join(ROOT, 'build.js'), '--raw-notes', slug], capture_output=True, text=True, check=True).stdout
notes = json.loads(raw)
beat = notes['beat']; bar = notes['countIn'] * beat       # MIDI seconds
end = max(n[0] / 1000 + n[1] / 1000 for n in notes['bass'] + notes['lead'])
nb = int(np.ceil(end / bar))

# features: onset strength (normalised against the loudest thing nearby, so a soft intro counts) and chroma
env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
envn = env / (uniform_filter1d(maximum_filter1d(env, int(3 * fps)), int(3 * fps)) + 1e-6)
QUIET = -45        # dB; the fade-in at the start of a song is noise to a chroma match, so those frames are left neutral
C = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
C = C - C.mean(0, keepdims=True); C = C / (np.linalg.norm(C, axis=0, keepdims=True) + 1e-9)
C[:, 20 * np.log10(librosa.feature.rms(y=y, hop_length=HOP)[0] + 1e-9)[:C.shape[1]] < QUIET] = 0

def midi_chroma(fps_, frames):
    M = np.zeros((12, frames))
    for tr in ('bass', 'lead'):
        for ms, d, nt, v in notes[tr]:
            i0 = int(ms / 1000 * fps_); i1 = max(i0 + 1, int((ms + d) / 1000 * fps_))
            if i0 < frames: M[nt % 12, i0:i1] += v / 127
    return M

# --- 1. coarse map by DTW on a coarser chroma ---
cfps = SR / 1024
Cc = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=1024)
Cc[:, 20 * np.log10(librosa.feature.rms(y=y, hop_length=1024)[0] + 1e-9)[:Cc.shape[1]] < QUIET] = 0
Mc = midi_chroma(cfps, int((end + 1) * cfps))      # no silent padding: the path has to end where the music ends
nz = lambda X: (X + 1e-3) / np.linalg.norm(X + 1e-3, axis=0, keepdims=True)
_, wp = librosa.sequence.dtw(X=nz(Mc), Y=nz(Cc), metric='cosine', step_sizes_sigma=np.array([[1, 1], [1, 0], [0, 1]]),
                             weights_add=np.array([0, 0.35, 0.35]), weights_mul=np.array([1, 1, 1]))
wp = wp[::-1]
mt, at = wp[:, 0] / cfps, wp[:, 1] / cfps
um, inv = np.unique(wp[:, 0], return_inverse=True)       # several recording frames can match one MIDI frame: take their mean
ua = np.bincount(inv, weights=wp[:, 1]) / np.bincount(inv) / cfps
tt = np.arange(0, end + 1, 0.05)
g = np.interp(tt, um / cfps, ua)
g = gaussian_filter1d(g, 5 / 0.05, mode='nearest')         # ~5 s smoothing: the bar search handles the detail
# before the music is audible (the fade-in) a chroma match only sees noise: carry the first reliable offset backwards at slope 1
rms_db = 20 * np.log10(librosa.feature.rms(y=y, hop_length=HOP)[0] + 1e-9)
loud = rms_db[np.clip((g * fps).astype(int), 0, len(rms_db) - 1)] > QUIET + 5
t_rel = float(tt[loud.argmax()])
g_rel = float(g[loud.argmax()])
g = np.where(tt < t_rel, g_rel + (tt - t_rel), g)
# the same at the end: the recording fades out while the MIDI plays on. Hold the last reliable offset through the fade, and note where
# the recording becomes inaudible (build.js drops every hit and note after that: nothing should light in silence)
rms1 = uniform_filter1d(rms_db, int(fps))
fade_from = float(np.nonzero(rms1 >= np.percentile(rms1, 75) - 8)[0][-1] / fps)    # recording seconds
audible_end = float(np.nonzero(rms1 > QUIET)[0][-1] / fps)
t_fade = float(tt[np.argmax(g >= fade_from)])
g = np.where(tt > t_fade, g[np.argmax(g >= fade_from)] + (tt - t_fade), g)
coarse = lambda t: np.interp(t, tt, g)
print(f'fade-out: starts at {fade_from:.1f}s in the recording (MIDI {t_fade:.1f}s), inaudible after {audible_end:.1f}s; the MIDI runs to {end:.1f}s')
print(f'intro: the recording is faded in until MIDI {t_rel:.1f}s; before that the offset is held at {g_rel - t_rel:+.2f}s')
slope = (coarse(end * 0.9) - coarse(end * 0.1)) / (end * 0.8)
print(f'coarse: {nb} bars, MIDI {end:.1f}s -> recording {coarse(0):.2f}s .. {coarse(end):.2f}s (mean slope {slope:.4f}, recording is {dur:.1f}s)')

# --- 2. per bar: onsets + harmony, Viterbi over offsets ---
Mf = midi_chroma(fps, int((end + 20) * fps)); act = Mf.any(0)
Mf = Mf - Mf.mean(0, keepdims=True) * act; Mf = Mf / (np.linalg.norm(Mf, axis=0, keepdims=True) + 1e-9)
ons = np.array([(ms / 1000, 1.0 if nt in (35, 36, 38, 40) else 0.5) for ms, nt, v in notes['drums']] +
               [(ms / 1000, 0.4) for tr in ('bass', 'lead') for ms, d, nt, v in notes[tr]])
RANGE, STEP = 0.30, 0.005
offs = np.arange(-RANGE, RANGE + 1e-9, STEP)
S_on = np.full((nb, len(offs)), np.nan); S_ch = np.full((nb, len(offs)), np.nan)
for k in range(nb):
    lo, hi = k * bar - 0.1, (k + 1) * bar + 0.1
    sel = ons[(ons[:, 0] >= lo) & (ons[:, 0] < hi)]
    if len(sel) >= 3:
        base = coarse(sel[:, 0])
        for j, o in enumerate(offs):
            idx = np.round((base + o) * fps).astype(int); ok = (idx > 1) & (idx < len(envn) - 2)
            if ok.any():
                v = np.maximum.reduce([envn[idx[ok] - 1], envn[idx[ok]], envn[idx[ok] + 1]])
                S_on[k, j] = (v * sel[ok, 1]).sum() / sel[ok, 1].sum()
    fr = np.arange(max(0, int(lo * fps)), int(hi * fps)); fr = fr[(fr < Mf.shape[1])]; fr = fr[act[fr]]
    if len(fr) >= 5:
        base = coarse(fr / fps)
        for j, o in enumerate(offs):
            ai = np.round((base + o) * fps).astype(int); ok = (ai >= 0) & (ai < C.shape[1])
            if ok.any(): S_ch[k, j] = (C[:, ai[ok]] * Mf[:, fr[ok]]).sum() / ok.sum()
def z(S):
    ok = np.isfinite(S).any(1)
    out = np.zeros_like(S)
    mu = np.nanmean(S[ok], 1, keepdims=True); sd = np.nanstd(S[ok], 1, keepdims=True) + 1e-9
    out[ok] = np.nan_to_num((S[ok] - mu) / sd)
    return out
Z = z(S_on) + z(S_ch)
LAM = 0.35                                                  # cost per 5 ms step between neighbouring bars
jj = np.arange(len(offs)); pen = LAM * np.abs(jj[:, None] - jj[None, :])
V = np.zeros_like(Z); P = np.zeros(Z.shape, int); V[0] = Z[0]
for k in range(1, nb):
    tot = V[k - 1][None, :] - pen
    P[k] = tot.argmax(1); V[k] = Z[k] + tot.max(1)
path = [int(V[-1].argmax())]
for k in range(nb - 1, 0, -1): path.append(P[k][path[-1]])
off = offs[path[::-1]]
print('last bars (bar, midi s, final offset vs recording, own onset peak, own chroma peak, ms):')
for k in range(max(0, nb - 12), nb):
    po = offs[np.nanargmax(S_on[k])] * 1000 if np.isfinite(S_on[k]).any() else float('nan')
    pc = offs[np.nanargmax(S_ch[k])] * 1000 if np.isfinite(S_ch[k]).any() else float('nan')
    print(f'  {k:3d} {k * bar:6.1f}  coarse diff {coarse(k * bar + bar / 2) - k * bar - bar / 2:+.2f}  chosen {off[k] * 1000:+5.0f}  onset {po:+5.0f}  chroma {pc:+5.0f}')
if np.abs(off).max() >= RANGE - STEP: print('WARNING: a bar sits at the edge of the search range; the coarse map is off there')

# knots at bar centres, forced to rise
cx = (np.arange(nb) + 0.5) * bar
knots = [[0.0, float(coarse(0) + off[0])]]
for k in range(nb):
    t = float(cx[k]); knots.append([round(t, 3), round(float(coarse(t) + off[k]), 3)])
knots.append([round(end + bar, 3), round(float(coarse(end + bar) + off[-1]), 3)])
K = np.array(knots)
for i in range(1, len(K)): K[i, 1] = max(K[i, 1], K[i - 1, 1] + 0.01)
knots = [[round(float(a), 3), round(float(b), 3)] for a, b in K]

# --- 3. report: do the drum hits land on recording onsets? ---
fine = 128; fp = SR / fine
ef = librosa.onset.onset_strength(y=y, sr=SR, hop_length=fine)
ef = (ef - ef.mean()) / ef.std()
pk = librosa.util.peak_pick(ef, pre_max=4, post_max=4, pre_avg=12, post_avg=12, delta=0.5, wait=5) / fp
dh = np.array([ms / 1000 for ms, nt, v in notes['drums'] if nt in (35, 36, 38, 40)])
dh = dh[coarse(dh) < audible_end]            # hits after the recording has faded out are dropped by build.js
def hit_rate(f, lo, hi):
    m = dh[(dh >= lo) & (dh < hi)]
    if not len(m): return None
    p = f(m); d = np.abs(p[:, None] - pk[None, :]).min(1)
    return (d < 0.04).mean(), np.median(d) * 1000
line = np.polyfit(mt[(mt > 20) & (mt < 190)], at[(mt > 20) & (mt < 190)], 1)
print('drum hits within 40 ms of a recording onset (median distance), per 30 s of the song:')
print('   from   straight line      bar map')
for s0 in range(0, int(end), 30):
    a_, b_ = hit_rate(lambda t: np.polyval(line, t), s0, s0 + 30) or (None, None), hit_rate(lambda t: np.interp(t, K[:, 0], K[:, 1]), s0, s0 + 30)
    if a_[0] is not None: print(f'  {s0:4d}s   {a_[0]*100:3.0f}% ({a_[1]:3.0f} ms)    {b_[0]*100:3.0f}% ({b_[1]:3.0f} ms)')
tot_l = hit_rate(lambda t: np.polyval(line, t), 0, end + 1); tot_b = hit_rate(lambda t: np.interp(t, K[:, 0], K[:, 1]), 0, end + 1)
print(f'  all     {tot_l[0]*100:3.0f}% ({tot_l[1]:3.0f} ms)    {tot_b[0]*100:3.0f}% ({tot_b[1]:3.0f} ms)')

os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
enc = ['-vn', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart']
for name, filt in ((f'{slug}.m4a', []), (f'{slug}-slow.m4a', ['-filter:a', f'atempo={SLOW}'])):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, *filt, *enc, os.path.join(ROOT, 'audio', name)], check=True)

mf = os.path.join(ROOT, 'midi', 'songs.json')
metas = json.load(open(mf))
metas.setdefault(slug, {})['audio'] = {'dur': round(dur, 2), 'end': round(audible_end, 2), 'map': knots}
txt = json.dumps(metas, indent=2, ensure_ascii=False)
txt = re.sub(r'\[\s+(-?[\d.]+),\s+(-?[\d.]+)\s+\]', r'[\1, \2]', txt)      # one knot per line pair, not four lines
open(mf, 'w').write(txt + '\n')
print('wrote audio/ files and midi/songs.json; now run: node build.js')
