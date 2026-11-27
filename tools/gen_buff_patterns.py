"""Generate FindText patterns for the 5 fishing buff icons (olr project).

Sources: ~/workspace/olr/images/buff_num*_1.jpg
(fresh 32x32 crops of the live buff bar, 2026-11-26 night, x=619, with the
"1s" countdown text on them -- these are what the script actually sees
in game, so the patterns are made from them instead of the older
buff_num*.png crops).
Each buff has a SECOND pattern from the older images/buff_num*_4.png
(the 2026-11-26 18:05 crops, darker, different countdown digit).
Both at T=80. The script tries both (BuffText + BuffText2, OR logic)
for every buff -- num7 got its second pattern first (2026-11-27 16:00,
it did improve the hit rate), the other four got theirs 2026-11-27
evening. (The _4 files were renamed from buff_num*.png 2026-11-27
evening; the pattern labels stay buff_num*_png, so the script is
byte-identical -- renaming the source files does not change the
patterns, because the script carries the pattern strings, not the
files.)

Second-pattern check (T=80, per-buff tolerance: 4/6 = 0.1, 5/7/8 = 0.2):
- png pattern vs own jpg image: num5 0.167, num7 0.162, num8 0.111
  (all under their tolerance, full overlap); num4 0.108, num6 0.115
  (just over 0.1 -- the png pattern does NOT also match the jpg image,
  but the jpg pattern DOES match the png image (0.082/0.083), so the
  second pattern is a second anchor for in-between variants, not a
  replacement. Gain for 4/6 is smaller than for 7, but it is safe.)
- png pattern vs every other buff (jpg and png images): worst 0.318
  (num8_png vs num4), all above their tolerance -- no false matches.
- png pattern vs buff4s_error: worst 0.711, safe.

Method: same encoder as fenix gen_recycle_patterns.py.
Threshold 80: the 5 new images all carry the white "1s" text, which
makes them look alike, so separation is much worse than the old set
(old set worst sep 0.351 at T=120; new set worst sep 0.270 at T=120,
below the 0.3 tolerance -- the orange-arrow buffs num4/num6/num8 would
be confused). T=80 is the best threshold for the new set: worst sep
0.333 (above 0.3), fragility 639 (similar to 633 at T=120). T=90 is
only 0.304 (too thin a margin); T=160/180 separate better but are far
more fragile (1627/893) and mostly dark.

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
T = 80

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

NAMES = ['buff_num4', 'buff_num5', 'buff_num6', 'buff_num7', 'buff_num8']
FILES = {
    'buff_num4': 'buff_num4_1.jpg',
    'buff_num5': 'buff_num5_1.jpg',
    'buff_num6': 'buff_num6_1.jpg',
    'buff_num7': 'buff_num7_1.jpg',
    'buff_num8': 'buff_num8_1.jpg',
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
# Second pattern for every buff: images/buff_num*_4.png (older crops),
# same T=80. The script tries BuffText[i] and BuffText2[i] (OR logic).
png_lines = []
png_bms = {}
for name in NAMES:
    s_png, bm_png = pattern_for(BASE + name + '_4.png', name + '_png')
    png_bms[name] = bm_png
    png_lines.append(f'    , "{s_png}"')
png_lines[0] = png_lines[0].replace('    , "', '    "', 1)
print('BuffText2 := [')
print('\n'.join(png_lines))
print(']')

TOL = {'buff_num4': 0.1, 'buff_num5': 0.2, 'buff_num6': 0.1,
       'buff_num7': 0.2, 'buff_num8': 0.2}
print()
print('Second-pattern check (png pattern vs own jpg image):')
for name in NAMES:
    e1, e0 = per_class_err(png_bms[name], bms[name])
    f1, f0 = per_class_err(bms[name], png_bms[name])
    print(f'  {name}: png->jpg max={max(e1, e0):.3f} jpg->png max={max(f1, f0):.3f} tol={TOL[name]}')
print('Second-pattern check (png pattern vs other buffs, jpg+png images):')
for name in NAMES:
    worst = 0.0
    for other in NAMES:
        if other == name:
            continue
        e1, e0 = per_class_err(png_bms[name], bms[other])
        f1, f0 = per_class_err(png_bms[name], png_bms[other])
        worst = max(worst, e1, e0, f1, f0)
    print(f'  {name}_png vs others: worst max err={worst:.3f} tol={TOL[name]} {"SAFE" if worst > TOL[name] else "WOULD MISIDENTIFY"}')

# Sub-patterns: every buff gets a right strip (12x32, x20-32, y0-32).
# The countdown digit lives at x9-14, so the right strip is fully
# digit-free for all five. All verified against both sources and
# sliding-window vs other buffs (tol 0.2).
# num4 right-12: self 0.078, sep 0.324, 204 black px (53%).
# num5 right-12: self 0.054, sep 0.338, 74 black px.
# num6 right-12: self 0.050, sep 0.288, 124 black px (32%).
# num7 right-12: self 0.047, sep 0.353, 109 black px (28%).
# num8 right-12: self 0.052, sep 0.351 (since 3ebf49e).
# History: num7 started with a bottom strip (3bf53ef) and num4/6 with
# bottom strips (7fce619), but their row 21 touches the digit
# (num6 x9/13, num7 x8/9/10 differ between sources -- the same flaw
# that made num5's bottom strip miss). num5 went top (too sparse, 29
# black px, matched everywhere) then bottom (same row-21 flaw) then
# right. Right strips fix all of it, so all five use the right strip.
# The BuffText3 "s"-region group (add89c5) is retired: the s-pattern
# is small (10x12) and was matching outside the buff bar row (log:
# num8 found at y=168, 2026-11-27 evening).
def sub_pattern(name, box, label):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    sub = [row[x1:x2] for row in bms[name][y1:y2]]
    s = encode(sub, w, label)
    t6, bm6 = decode(s)
    assert bm6 == sub, f'round-trip mismatch for {label}'
    print(f'{label} := "{s}"')
    sub_png = [row[x1:x2] for row in png_bms[name][y1:y2]]
    e1, e0 = per_class_err(sub, sub_png)
    worst = 1.0
    for other in NAMES:
        if other == name:
            continue
        for src_bm in (bms[other], png_bms[other]):
            for y in range(0, 32 - h + 1):
                for x in range(0, 32 - w + 1):
                    win = [row[x:x + w] for row in src_bm[y:y + h]]
                    a1, a0 = per_class_err(sub, win)
                    worst = min(worst, max(a1, a0))
    print(f'  {label}: vs png max={max(e1, e0):.3f} sep_worst={worst:.3f} (tol 0.2) {"SAFE" if max(e1, e0) < 0.2 and worst > 0.2 else "NO"}')
    return s

print()
print('right-strip sub-patterns (digit-free, x 20-32, y 0-32):')
sub_pattern('buff_num4', (20, 0, 32, 32), 'buff_num4_right')
sub_pattern('buff_num5', (20, 0, 32, 32), 'buff_num5_right')
sub_pattern('buff_num6', (20, 0, 32, 32), 'buff_num6_right')
sub_pattern('buff_num7', (20, 0, 32, 32), 'buff_num7_right')
sub_pattern('buff_num8', (20, 0, 32, 32), 'buff_num8_right')
