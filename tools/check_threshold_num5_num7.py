"""Check per-buff threshold choice for buff_num7 and buff_num5.

Recognition is low for these two at the current T=120. For each
threshold T, report for each buff:
  ones   = bright pixels (bit 0) in the pattern at T
  sep    = min over the other 4 buffs of (max per-class err, both
           directions). Higher = more distinctive, harder to confuse.
  frag   = pixels whose gray is within +-15 of T. Lower = fewer pixels
           flip when the live icon is a bit brighter/darker, so the
           pattern survives brightness shifts better.
A threshold is good for a buff when sep is high and frag is low.
"""
from PIL import Image

BASE = '/home/hatch/workspace/olr/images/'
NAMES = ['buff_num4', 'buff_num5', 'buff_num6', 'buff_num7', 'buff_num8']


def gray(px):
    r, g, b = px[0], px[1], px[2]
    return (r * 38 + g * 75 + b * 15) >> 7


def load_gray(name):
    im = Image.open(BASE + name + '.png').convert('RGB')
    px = im.load()
    w, h = im.size
    return [[gray(px[x, y]) for x in range(w)] for y in range(h)], w, h


def binarize(g, T):
    return [[1 if g[y][x] <= T else 0 for x in range(len(g[0]))] for y in range(len(g))]


def per_class_err(pat, img):
    ones = sum(sum(r) for r in pat)
    zeros = sum(len(r) for r in pat) - ones
    e1 = sum(1 for y in range(len(pat)) for x in range(len(pat[0]))
             if pat[y][x] == 1 and img[y][x] == 0) / max(ones, 1)
    e0 = sum(1 for y in range(len(pat)) for x in range(len(pat[0]))
             if pat[y][x] == 0 and img[y][x] == 1) / max(zeros, 1)
    return e1, e0


grays = {n: load_gray(n)[0] for n in NAMES}

print(f"{'T':>4} | {'buff':>9} | {'ones':>4} | {'sep':>5} | {'frag':>4}")
print('-' * 40)
for T in [80, 90, 100, 110, 120, 130, 140, 150, 160, 180]:
    bms = {n: binarize(grays[n], T) for n in NAMES}
    for n in NAMES:
        ones = sum(sum(r) for r in bms[n])
        zeros = 1024 - ones
        # separation: worst (smallest) max-err vs any other buff
        sep = 1.0
        for m in NAMES:
            if m == n:
                continue
            e1, e0 = per_class_err(bms[n], bms[m])
            f1, f0 = per_class_err(bms[m], bms[n])
            sep = min(sep, max(e1, e0, f1, f0))
        frag = sum(1 for y in range(32) for x in range(32)
                   if abs(grays[n][y][x] - T) <= 15)
        mark = ' <<<' if n in ('buff_num7', 'buff_num5') else ''
        print(f"{T:>4} | {n:>9} | {ones:>4} | {sep:>5.3f} | {frag:>4}{mark}")
    print('-' * 40)
