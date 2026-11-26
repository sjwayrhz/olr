#!/usr/bin/env python3
"""Inject freshly generated FindText patterns (from gen_buff_patterns.py)
into olr_fishing.ahk programmatically. Never hand-copy pattern strings:
a single dropped character breaks the pattern (189 vs 190 chars, 2026-11-26).

Two rules this script enforces (both were broken by the first version):
1. BuffText order MUST match BuffName/BuffKey/BuffSpace/BuffRest:
   buff_num4, buff_num5, buff_num6, buff_num7, buff_num8
   (the generator emits them by screenshot file: 0007, 0005, 0020,
   0001, 0030, and GEN_TO_DISPLAY below maps each to its key).
2. The FIRST element must NOT have a leading comma. In AHK v2 a leading
   comma before the first element creates an empty BuffText[1], and
   FindBuff(1) then throws "Item has no value. Specifically: 1".
   Format: first line `    "..."`, later lines `    , "..."`.

Verifies each injected line matches the generator output exactly.
"""
import re
import subprocess
import sys

AHK = "/home/hatch/workspace/olr/olr_fishing.ahk"
GEN = "/home/hatch/workspace/olr/tools/gen_buff_patterns.py"
# Generator names (from screenshot files) -> display names (by numpad key).
# Canonical order, must match BuffName in olr_fishing.ahk.
GEN_TO_DISPLAY = {
    "Buff0007": "buff_num4",
    "Buff0005": "buff_num5",
    "Buff0020": "buff_num6",
    "Buff0001": "buff_num7",
    "Buff0030": "buff_num8",
}
ORDER = ["buff_num4", "buff_num5", "buff_num6", "buff_num7", "buff_num8"]

out = subprocess.run([sys.executable, GEN], capture_output=True, text=True, check=True).stdout
m = re.search(r"BuffText := \[\n(.*?)\n\]", out, re.S)
if not m:
    raise SystemExit("generator output has no BuffText block")
gen_lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
assert len(gen_lines) == 5, f"expected 5 pattern lines, got {len(gen_lines)}"

# Map buff name -> the pattern string (without leading comma/quote handling).
by_name = {}
for ln in gen_lines:
    mm = re.search(r'"\|<(\w+)>\*', ln)
    assert mm, f"cannot parse buff name from: {ln[:50]}"
    gen_name = mm.group(1)
    assert gen_name in GEN_TO_DISPLAY, f"unknown generator name {gen_name}"
    disp = GEN_TO_DISPLAY[gen_name]
    # strip leading comma and surrounding quotes/spaces
    pat = ln.lstrip(", ").strip()
    assert pat.startswith('"') and pat.endswith('"'), f"bad line: {ln[:50]}"
    # rewrite the pattern label to the display name (buff_num4, ...)
    pat = pat.replace(f"|<{gen_name}>", f"|<{disp}>", 1)
    by_name[disp] = pat
assert set(by_name) == set(ORDER), f"generator names {sorted(by_name)} != order {ORDER}"

# Emit in canonical order: first line no leading comma, rest with one.
new_lines = []
for idx, name in enumerate(ORDER):
    pat = by_name[name]
    new_lines.append(('    ' if idx == 0 else '    , ') + pat)

src = open(AHK, encoding="utf-8-sig").read()
m2 = re.search(r"BuffText := \[\n.*?\n\]", src, re.S)
if not m2:
    raise SystemExit("olr_fishing.ahk has no BuffText block")
new_block = "BuffText := [\n" + "\n".join(new_lines) + "\n]"
src2 = src[:m2.start()] + new_block + src[m2.end():]
open(AHK, "w", encoding="utf-8-sig", newline="").write(src2)

# Verify: re-read, confirm order + exact match + first line has no leading comma.
after = open(AHK, encoding="utf-8-sig").read()
m3 = re.search(r"BuffText := \[\n(.*?)\n\]", after, re.S)
got = [ln for ln in m3.group(1).splitlines() if ln.strip()]
assert got == new_lines, "injected patterns do not match expected block"
assert got[0].lstrip().startswith('"'), "first element must not have a leading comma"
assert all(ln.lstrip().startswith(', "') for ln in got[1:]), "later elements need a leading comma"
for name, ln in zip(ORDER, got):
    assert f"|<{name}>" in ln, f"line {ln[:40]} is not {name}"
    assert "*120$" in ln, f"wrong threshold in line: {ln[:50]}"
print("injected 5 patterns at T=120 in canonical order (buff_num4,buff_num5,buff_num6,buff_num7,buff_num8),")
print("first element has no leading comma; verified byte-identical to generator output")
for ln in got:
    print(" ", ln[:60], "... len", len(ln))
