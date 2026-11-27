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

# Third pattern for num5 only: images/buff_num5_0011.png (ScreenShot0011,
# 2026-11-27 20:27 batch). The user sent 6 screenshots with the num5 fish
# and asked which one best improves num5 recognition. Measured at T=80:
# - 0002/0013/0022 (clean fish): match the existing jpg/png patterns well
#   (best err 0.123-0.158) -- already covered, adding one gains nothing.
# - 0004 (fish with "2s" countdown): err 0.830 vs existing -- the timer
#   text breaks the match, but the timer value changes every second, so
#   a "2s" pattern is too specific to be useful. Rejected.
# - 0011 (clean fish, BRIGHTER): err 0.367/0.415 vs existing patterns --
#   the existing T=80 patterns do NOT find it. It is brighter (avg gray
#   140.9 vs 132-137, only 142 black px at T=80 vs 187-223 for the
#   others), so at T=80 it binarizes sparser. This is the gap: when the
#   fish icon renders bright, the script misses it. Adding 0011 as a
#   third pattern covers that case. It also matches the darker instances
#   (vs 0002/0013/0022: 0.054/0.113/0.120), because its sparse black
#   pixels are a subset of theirs.
# Separation at T=80: worst 0.310 vs other buffs (closest num7 png),
# above the 0.2 tol -- safe. It is sparser than ideal (142/1024 = 14%
# black), so if num5 starts false-triggering on non-buff screen areas,
# this pattern is the first suspect.
print()
print('Third num5 pattern (buff_num5_0011.png, T=80, ScreenShot0011):')
s_n5_3, bm_n5_3 = pattern_for(BASE + 'buff_num5_0011.png', 'buff_num5_0011')
print(f'BuffNum5Third := "{s_n5_3}"')
n5_3_worst = 1.0
for other in NAMES:
    if other == 'buff_num5':
        continue
    for src_bm in (bms[other], png_bms[other]):
        e1, e0 = per_class_err(bm_n5_3, src_bm)
        n5_3_worst = min(n5_3_worst, max(e1, e0))
print(f'  BuffNum5Third: sep_worst vs other buffs={n5_3_worst:.3f} (tol 0.2) {"SAFE" if n5_3_worst > 0.2 else "WOULD MISIDENTIFY"}')
e1, e0 = per_class_err(bms['buff_num5'], bm_n5_3)
f1, f0 = per_class_err(png_bms['buff_num5'], bm_n5_3)
print(f'  BuffNum5Third: existing jpg pattern vs this image max={max(e1, e0):.3f}, existing png pattern vs this image max={max(f1, f0):.3f} (tol 0.2; above means the first two MISS this instance, so the third pattern fills a real gap)')

# Third pattern for num4 only: images/buff_num4_0003.png (ScreenShot0003,
# 2026-11-28 Desktop.zip batch, top-center target buff area at (620,76)).
# The user reported num4 recognition was low. Measured at T=80 on the 8
# new screenshots: the stored num4 patterns (2026-11-26) match the live
# num4 icon at best err 0.209-0.258 -- above the 0.2 tol, so the script
# misses it. The (620,76) icon in ScreenShot0003 is clearly num4: it
# matches the stored num4 jpg at 0.209 (closest), is distinct from num8
# (0.350) and all other buffs (0.398+). Its black density is 450/1024
# (44%), dense enough. The other candidate -- the icon at (72,76) in
# the top-left player bar -- is AMBIGUOUS (num4 0.254 vs num8 0.263),
# so it is NOT used as a pattern; it would risk false positives.
# Separation at T=80: worst 0.350 vs other buffs (closest num8 jpg),
# above the 0.2 tol -- safe.
print()
print('Third num4 pattern (buff_num4_0003.png, T=80, ScreenShot0003):')
s_n4_3, bm_n4_3 = pattern_for(BASE + 'buff_num4_0003.png', 'buff_num4_0003')
print(f'BuffNum4Third := "{s_n4_3}"')
n4_3_worst = 1.0
for other in NAMES:
    if other == 'buff_num4':
        continue
    for src_bm in (bms[other], png_bms[other]):
        e1, e0 = per_class_err(bm_n4_3, src_bm)
        n4_3_worst = min(n4_3_worst, max(e1, e0))
print(f'  BuffNum4Third: sep_worst vs other buffs={n4_3_worst:.3f} (tol 0.2) {"SAFE" if n4_3_worst > 0.2 else "WOULD MISIDENTIFY"}')
e1, e0 = per_class_err(bms['buff_num4'], bm_n4_3)
f1, f0 = per_class_err(png_bms['buff_num4'], bm_n4_3)
print(f'  BuffNum4Third: existing jpg pattern vs this image max={max(e1, e0):.3f}, existing png pattern vs this image max={max(f1, f0):.3f} (tol 0.2; above means the first two MISS this instance, so the third pattern fills a real gap)')

# Sub-patterns: only num7 and num8 get a third pattern (the right strip,
# 12x32, x20-32, y0-32). The countdown digit lives at x9-14, y13-21,
# so the right strip is fully digit-free.
# num7 right-12: self 0.047, sep 0.353, 109 black px (28%).
# num8 right-12: self 0.052, sep 0.351 (since 3ebf49e) -- REMOVED
# 2026-11-28, see below.
# num4/5/6 have NO third pattern: they use only the two full patterns.
# Their sub-patterns were tried and removed one by one because they kept
# causing misidentification in live play:
# - num4/6 bottom strips (7fce619): row 21 touches the digit (num6 x9/13,
#   num7 x8/9/10 differ between sources).
# - num5 top strip (7fce619): only 29 black px (8%), matched everywhere
#   (log 2026-11-27 18:36-18:49).
# - num5 bottom strip (6b58243): row 21 digit pixels, missed often.
# - num4/6/7 right strips (57ef130): unified, but errors still occurred.
# - num4 top strip (f016472): self 0.034 but sep only 0.221 (closest to
#   num8), still caused errors.
# 2026-11-27 19:38 she decided: only 7 and 8 keep the right strip;
# 4/5/6 go back to two full patterns only. If 4/5/6 recognition drops,
# revisit then -- do not re-add sub-patterns unasked.
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
print('sub-patterns (digit-free right strips, only num7 now):')
sub_pattern('buff_num7', (20, 0, 32, 32), 'buff_num7_right')
# buff_num8_right REMOVED 2026-11-28: the 12x32 strip kept matching
# terrain outside the buff bar row (log 2026-11-28 05:24-05:38: every
# num8 press was at y=168 or y=318, while the real buff bar is y=207;
# after num7 was pressed and went on its 5.1s rest, the script found a
# false num8 at y=168 and pressed 8 instead of waiting for 7). A thin
# 12px strip is not distinctive enough -- it matches vertical terrain
# features (tree trunks, rock edges). Same failure mode as the retired
# "s" pattern (10x12), which also false-matched at y=168. num8 keeps
# its two full 32x32 patterns (jpg + png); num7 keeps its right strip
# (it never false-matched).

# buff4s_error pattern (red downward arrow, 32x32, images/buff4s_error.png).
# Threshold is 80, same as the buffs. This is the ORIGINAL icon from
# ScreenShot0004 (fish blood bar, rightmost of the 3 buffs, x=653-685,
# y=75-107, no stack count). At T=80 the separation from the buffs is
# 0.506 (0.573 at T=60, 0.455 at T=100) -- comfortably above the 0.3
# tol. Restored 2026-11-28 at the user's request: she had the icon
# changed twice (2026-11-27 20:19: first to a fresh ScreenShot0020
# capture with x4 at T=60, then corrected to the below-x4 crop 32x20
# at T=40), and now wants the FIRST version back. The ScreenShot0020
# below-x4 crop (32x20, T=40) is NOT kept -- the file in images/ is
# the original ScreenShot0004 full 32x32 icon again. If the icon's
# brightness varies between sessions and error stops being found,
# re-capture it and re-run this generator.
print()
print('buff4s_error pattern (threshold 80, 32x32, original ScreenShot0004):')
err_im = Image.open(BASE + 'buff4s_error.png').convert('RGB')
err_px = err_im.load()
err_bm = [[1 if gray(err_px[x, y]) <= 80 else 0 for x in range(32)] for y in range(32)]
T = 80
err_s = encode(err_bm, 32, 'buff4s_error')
print(f'buff4s_error := "{err_s}"')
err_t, err_bm2 = decode(err_s)
assert err_bm2 == err_bm, 'round-trip mismatch for buff4s_error'
assert err_t == 80, 'error pattern threshold is not 80'
# Separation must be measured against the buffs binarized at the SAME
# threshold FindText will use for this pattern (80).
err_worst = 1.0
for other in NAMES:
    for src_path in (BASE + FILES[other], BASE + other + '_4.png'):
        src_im = Image.open(src_path).convert('RGB')
        src_px = src_im.load()
        src_bm = [[1 if gray(src_px[x, y]) <= 80 else 0 for x in range(32)] for y in range(32)]
        a1, a0 = per_class_err(err_bm, src_bm)
        err_worst = min(err_worst, max(a1, a0))
print(f'  buff4s_error: sep_worst vs buffs={err_worst:.3f} (tol 0.3) {"SAFE" if err_worst > 0.3 else "WOULD MISIDENTIFY"}')
