"""Generate FindText patterns for the 5 fishing buff icons (olr project).

Sources: ~/workspace/user/files/buff-4s-2026-11-26/buff4s_*.png
(32x32 crops from her screenshots, 2026-11-26).

Method: same encoder as fenix gen_recycle_patterns.py.
Threshold 180 (not 120): at 120 the worst pair (0007 vs 0030) had a
false-match limit of only 0.244, barely above the 0.2 tolerance, and the
live animated icon pushed it under, so every buff matched 0007 first
(2026-11-26 bug: only Numpad4 was ever pressed). At 180 the worst pair
is 0.434, nearly double the margin.

Also prints a pairwise separation check (per-class err both directions):
a pair is safe when both err1 and err0 stay above 0.2 for both directions.

Run: python3 gen_buff_patterns.py  (prints AHK lines to paste)
"""
import re
from PIL import Image

def gray(px):
    r, g, b = px[0], px[1], px[2]
    return (r * 38 + g * 75 + b * 15) >> 7

CHARS = "0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
T = 180

def encode(bm, w, name):
    bits = ''.join('1' if bm[y][x] else '0' for y in range(len(bm)) for x in range(w))
    bits += '1'
    while len(bits) % 6:
        bits += '0'
    data = ''.join(CHARS[int(bits[i:i + 6], 2)] for i in range(0, len(bits), 6))
    return f"|<{name}>*{T}${w}.{data}"

def decode(text):
    m = re.search(r'\*(\d+)\$(\d+)\.([\w+/]+)', text)
    t, w, data = int(m.group(1)), int(m.group(2)), m.group(3)
    bits = ''.join(format(CHARS.index(c), '06b') for c in data)
    bits = re.sub(r'10*$', '', bits)
    h = len(bits) // w
    return t, [[int(bits[y * w + x]) for x in range(w)] for y in range(h)]

def load_bm(path):
    im = Image.open(path).convert('RGB')
    px = im.load()
    w, h = im.size
    return [[1 if gray(px[x, y]) <= T else 0 for x in range(w)] for y in range(h)], w, h

def pattern_for(path, name):
    bm, w, h = load_bm(path)
    s = encode(bm, w, name)
    t2, bm2 = decode(s)
    assert bm2 == bm, f'round-trip mismatch for {name}'
    ones = sum(sum(r) for r in bm)
    print(f'; {name}: {w}x{h}, ones={ones}/{w * h} ({ones / (w * h):.2f})')
    return s, bm

def per_class_err(pat, img):
    """err if pattern pat is searched in image img (same size)."""
    ones = sum(sum(r) for r in pat)
    zeros = sum(len(r) for r in pat) - ones
    e1 = sum(1 for y in range(len(pat)) for x in range(len(pat[0]))
             if pat[y][x] == 1 and img[y][x] == 0) / max(ones, 1)
    e0 = sum(1 for y in range(len(pat)) for x in range(len(pat[0]))
             if pat[y][x] == 0 and img[y][x] == 1) / max(zeros, 1)
    return e1, e0

NAMES = ['Buff0001', 'Buff0005', 'Buff0020', 'Buff0007', 'Buff0030']
FILES = {
    'Buff0001': 'buff4s_0001.png',
    'Buff0005': 'buff4s_0005.png',
    'Buff0020': 'buff4s_0020.png',
    'Buff0007': 'buff4s_0007.png',
    'Buff0030': 'buff4s_0030.png',
}
BASE = '/home/hatch/workspace/olr/images/'

bms = {}
lines = []
for name in NAMES:
    s, bm = pattern_for(BASE + FILES[name], name)
    bms[name] = bm
    lines.append(f'    , "{s}"')

print()
print('Pairwise separation (per-class err, both directions; safe if max > 0.2):')
print('(pairs of different sizes cannot match each other in FindText, skipped)')
worst = 0.0
for i in range(len(NAMES)):
    for j in range(i + 1, len(NAMES)):
        a, b = NAMES[i], NAMES[j]
        if len(bms[a]) != len(bms[b]) or len(bms[a][0]) != len(bms[b][0]):
            print(f'  {a} vs {b}: different sizes, skipped')
            continue
        e1, e0 = per_class_err(bms[a], bms[b])
        f1, f0 = per_class_err(bms[b], bms[a])
        m = max(e1, e0, f1, f0)
        worst = max(worst, m)
        print(f'  {a} vs {b}: err1={e1:.3f}/{f1:.3f} err0={e0:.3f}/{f0:.3f} max={m:.3f}')
print(f'  worst same-size pair max err: {worst:.3f} (tolerance 0.2)')

print()
print('AHK lines (paste into olr_fishing.ahk):')
print('BuffText := [')
print('\n'.join(lines))
print(']')
