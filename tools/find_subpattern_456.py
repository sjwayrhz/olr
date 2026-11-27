"""Find digit-free sub-patterns for num4/5/6, same method as num7 bottom
(3bf53ef) and num8 right strip (3ebf49e): crop a region that contains no
countdown digit, verify it covers both sources and separates from other
buffs, then render preview images for the user to approve.

Candidate regions (32x32 icon):
  bottom: y21-32, x0-32 / x0-22
  right:  x20-32, y0-32 / x22-32
  left:   x0-12, y0-32 / x0-10
  top:    y0-12, x0-32 / y0-10
Digit-free test: pixel diff between the jpg and png sources inside the
region (the digit differs between sources, so a digit-bearing region
shows a big diff; a digit-free region shows near-zero diff).
"""
import sys
sys.path.insert(0, '/home/hatch/workspace/olr/tools')
from gen_buff_patterns import load_bm, encode, decode, per_class_err, BASE, NAMES, FILES
from PIL import Image, ImageDraw

bms = {}
png_bms = {}
for name in NAMES:
    bms[name], _, _ = load_bm(BASE + FILES[name])
    png_bms[name], _, _ = load_bm(BASE + name + '_4.png')

CANDIDATES = {
    'bottom-full':  (0, 21, 32, 32),
    'bottom-22':    (0, 21, 22, 32),
    'right-12':     (20, 0, 32, 32),
    'right-10':     (22, 0, 32, 32),
    'left-12':      (0, 0, 12, 32),
    'left-10':      (0, 0, 10, 32),
    'top-full':     (0, 0, 32, 12),
    'top-10':       (0, 0, 32, 10),
}

def region(bm, box):
    x1, y1, x2, y2 = box
    return [row[x1:x2] for row in bm[y1:y2]]

def diff_count(a, b):
    return sum(1 for y in range(len(a)) for x in range(len(a[0])) if a[y][x] != b[y][x])

def slide_sep(pat, others):
    """Worst (smallest) sliding-window max-err of pat vs each other buff image."""
    h, w = len(pat), len(pat[0])
    worst = 1.0
    for src in others:
        for y in range(0, 32 - h + 1):
            for x in range(0, 32 - w + 1):
                win = [row[x:x + w] for row in src[y:y + h]]
                e1, e0 = per_class_err(pat, win)
                worst = min(worst, max(e1, e0))
    return worst

print('Candidate scan for num4 / num5 / num6 (tol 0.2):')
print('diff = jpg-vs-png pixel diff inside region (digit-free if small)')
print('self = jpg-pattern vs png region max err (must be < 0.2)')
print('sep  = sliding-window worst separation vs other buffs (must be > 0.2)')
print()
results = {}
for name in ['buff_num4', 'buff_num5', 'buff_num6']:
    print(f'--- {name} ---')
    best = None
    for cname, box in CANDIDATES.items():
        sub = region(bms[name], box)
        sub_png = region(png_bms[name], box)
        d = diff_count(sub, sub_png)
        e1, e0 = per_class_err(sub, sub_png)
        self_err = max(e1, e0)
        others = [bms[o] for o in NAMES if o != name] + [png_bms[o] for o in NAMES if o != name]
        sep = slide_sep(sub, others)
        ok = self_err < 0.2 and sep > 0.2
        ones = sum(sum(r) for r in sub)
        print(f'  {cname:12s} {box} ones={ones:3d} diff={d:3d} self={self_err:.3f} sep={sep:.3f} {"OK" if ok else "--"}')
        if ok and (best is None or sep > best[3]):
            best = (cname, box, self_err, sep, sub)
    results[name] = best
    if best:
        print(f'  BEST: {best[0]} {best[1]} self={best[2]:.3f} sep={best[3]:.3f}')
    else:
        print('  NO candidate passes both checks')
    print()

# Render preview images: for each of num4/5/6, the best region (or the
# bottom-22 / right-12 fallback) highlighted on both source images,
# 6x scale, plus the binarised sub-pattern at 8x.
OUT = '/home/hatch/workspace/user/files/subpattern-456/'
import os
os.makedirs(OUT, exist_ok=True)
for name in ['buff_num4', 'buff_num5', 'buff_num6']:
    best = results[name]
    box = best[1] if best else (0, 21, 22, 32)
    label = best[0] if best else 'bottom-22 (fallback)'
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    for tag, src in (('1.jpg', FILES[name]), ('4.png', name + '_4.png')):
        im = Image.open(BASE + src).convert('RGB').resize((32 * 6, 32 * 6), Image.NEAREST)
        d = ImageDraw.Draw(im)
        d.rectangle([x1 * 6, y1 * 6, x2 * 6 - 1, y2 * 6 - 1], outline=(255, 0, 0), width=3)
        im.save(f'{OUT}{name}_{tag}_region.png')
    sub = region(bms[name], box)
    pat = Image.new('RGB', (w * 8, h * 8), (255, 255, 255))
    pd = ImageDraw.Draw(pat)
    for y in range(h):
        for x in range(w):
            if sub[y][x]:
                pd.rectangle([x * 8, y * 8, x * 8 + 7, y * 8 + 7], fill=(0, 0, 0))
    pat.save(f'{OUT}{name}_pattern_{label.replace(" ", "_")}.png')
    print(f'{name}: preview {label} {box} -> {OUT}')
