#!/usr/bin/env python3
"""Inject freshly generated FindText patterns (from gen_buff_patterns.py)
into olr_fishing.ahk programmatically. Never hand-copy pattern strings:
a single dropped character breaks the pattern (189 vs 190 chars, 2026-11-26).

Two rules this script enforces (both were broken by the first version):
1. BuffText order MUST match BuffName/BuffKey/BuffSpace/BuffRest:
   buff_num4, buff_num5, buff_num6, buff_num7, buff_num8
   (the generator emits them in that order).
2. The FIRST element must NOT have a leading comma. In AHK v2 a leading
   comma before the first element creates an empty BuffText[1], and
   FindBuff(1) then throws "Item has no value. Specifically: 1".
   Format: first line `    "..."`, later lines `    , "..."`.

num7 has two patterns (BuffNum7Text, both T=80): the buff_num7_1.jpg
pattern (same as BuffText[4]) and the buff_num7.png pattern. FindBuff
tries both for num7 (OR logic). This script injects both blocks and
verifies each line matches the generator output exactly.
"""
import re
import subprocess
import sys

AHK = "/home/hatch/workspace/olr/olr_fishing.ahk"
GEN = "/home/hatch/workspace/olr/tools/gen_buff_patterns.py"
# Canonical order for BuffText, must match BuffName in olr_fishing.ahk.
ORDER = ["buff_num4", "buff_num5", "buff_num6", "buff_num7", "buff_num8"]
NUM7_ORDER = ["buff_num7", "buff_num7_png"]

out = subprocess.run([sys.executable, GEN], capture_output=True, text=True, check=True).stdout

def parse_block(out, header):
    m = re.search(re.escape(header) + r" := \[\n(.*?)\n\]", out, re.S)
    if not m:
        raise SystemExit(f"generator output has no {header} block")
    lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
    by_name = {}
    for ln in lines:
        mm = re.search(r'"\|<(\w+)>\*', ln)
        assert mm, f"cannot parse buff name from: {ln[:50]}"
        pat = ln.lstrip(", ").strip()
        assert pat.startswith('"') and pat.endswith('"'), f"bad line: {ln[:50]}"
        by_name[mm.group(1)] = pat
    return lines, by_name

def emit_block(order, by_name):
    new_lines = []
    for idx, name in enumerate(order):
        pat = by_name[name]
        new_lines.append(('    ' if idx == 0 else '    , ') + pat)
    return new_lines

def inject_block(src, header, new_lines):
    m = re.search(re.escape(header) + r" := \[\n.*?\n\]", src, re.S)
    if not m:
        raise SystemExit(f"olr_fishing.ahk has no {header} block")
    new_block = header + " := [\n" + "\n".join(new_lines) + "\n]"
    return src[:m.start()] + new_block + src[m.end():]

def verify_block(after, header, order, new_lines):
    m = re.search(re.escape(header) + r" := \[\n(.*?)\n\]", after, re.S)
    got = [ln for ln in m.group(1).splitlines() if ln.strip()]
    assert got == new_lines, f"injected {header} does not match expected block"
    assert got[0].lstrip().startswith('"'), f"{header}: first element must not have a leading comma"
    assert all(ln.lstrip().startswith(', "') for ln in got[1:]), f"{header}: later elements need a leading comma"
    for name, ln in zip(order, got):
        assert f"|<{name}>" in ln, f"{header} line {ln[:40]} is not {name}"
        assert "*80$" in ln, f"{header} wrong threshold in line: {ln[:50]}"

gen_lines, by_name = parse_block(out, "BuffText")
assert len(gen_lines) == 5, f"expected 5 BuffText lines, got {len(gen_lines)}"
assert set(by_name) == set(ORDER), f"generator BuffText names {sorted(by_name)} != order {ORDER}"
num7_lines, num7_by_name = parse_block(out, "BuffNum7Text")
assert len(num7_lines) == 2, f"expected 2 BuffNum7Text lines, got {len(num7_lines)}"
assert set(num7_by_name) == set(NUM7_ORDER), f"generator BuffNum7Text names {sorted(num7_by_name)} != {NUM7_ORDER}"

new_text = emit_block(ORDER, by_name)
new_num7 = emit_block(NUM7_ORDER, num7_by_name)

src = open(AHK, encoding="utf-8-sig").read()
src = inject_block(src, "BuffText", new_text)
src = inject_block(src, "BuffNum7Text", new_num7)
open(AHK, "w", encoding="utf-8-sig", newline="").write(src)

after = open(AHK, encoding="utf-8-sig").read()
verify_block(after, "BuffText", ORDER, new_text)
verify_block(after, "BuffNum7Text", NUM7_ORDER, new_num7)
print("injected BuffText (5 patterns at T=80) and BuffNum7Text (2 patterns at T=80),")
print("first elements have no leading comma; verified byte-identical to generator output")
