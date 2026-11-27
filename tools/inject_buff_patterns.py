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
pattern (same as BuffText[4]) and the buff_num7_4.png pattern. FindBuff
tries both for num7 (OR logic). This script injects both blocks and
verifies each line matches the generator output exactly.

2026-11-27 evening: every buff now has a second pattern
(images/buff_num*_4.png, T=80) in BuffText2, tried for all five buffs.
BuffNum7Text is retired: this script deletes that block from the AHK
file when it injects BuffText2.
"""
import re
import subprocess
import sys

AHK = "/home/hatch/workspace/olr/olr_fishing.ahk"
GEN = "/home/hatch/workspace/olr/tools/gen_buff_patterns.py"
# Canonical order for BuffText, must match BuffName in olr_fishing.ahk.
ORDER = ["buff_num4", "buff_num5", "buff_num6", "buff_num7", "buff_num8"]
PNG_ORDER = ["buff_num4_png", "buff_num5_png", "buff_num6_png", "buff_num7_png", "buff_num8_png"]

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

def delete_block(src, header):
    m = re.search(re.escape(header) + r" := \[\n.*?\n\]\n?", src, re.S)
    if not m:
        return src
    return src[:m.start()] + src[m.end():]

def verify_block(after, header, order, new_lines):
    m = re.search(re.escape(header) + r" := \[\n(.*?)\n\]", after, re.S)
    got = [ln for ln in m.group(1).splitlines() if ln.strip()]
    assert got == new_lines, f"injected {header} does not match expected block"
    assert got[0].lstrip().startswith('"'), f"{header}: first element must not have a leading comma"
    assert all(ln.lstrip().startswith(', "') for ln in got[1:]), f"{header}: later elements need a leading comma"
    for name, ln in zip(order, got):
        assert f"|<{name}>" in ln, f"{header} line {ln[:40]} is not {name}"
        assert "*80$" in ln, f"{header} wrong threshold in line: {ln[:50]}"

def inject_line(src, header, new_line):
    """Replace (or insert after BuffText2) a single-line pattern assignment
    like BuffNum7Bottom := "..."."""
    m = re.search(re.escape(header) + r' := ".*"\n', src)
    if m:
        return src[:m.start()] + new_line + "\n" + src[m.end():]
    anchor = "BuffText2 := [\n" + "\n".join(new_png) + "\n]"
    idx = src.index(anchor) + len(anchor)
    return src[:idx] + "\n" + new_line + src[idx:]

gen_lines, by_name = parse_block(out, "BuffText")
assert len(gen_lines) == 5, f"expected 5 BuffText lines, got {len(gen_lines)}"
assert set(by_name) == set(ORDER), f"generator BuffText names {sorted(by_name)} != order {ORDER}"
png_lines, png_by_name = parse_block(out, "BuffText2")
assert len(png_lines) == 5, f"expected 5 BuffText2 lines, got {len(png_lines)}"
assert set(png_by_name) == set(PNG_ORDER), f"generator BuffText2 names {sorted(png_by_name)} != {PNG_ORDER}"
m_bottom = re.search(r'BuffNum7Bottom := ("\|<buff_num7_bottom>\*80\$22\.[\w+/]+")', out)
assert m_bottom, "generator output has no BuffNum7Bottom line"
bottom_line = f'BuffNum7Bottom := {m_bottom.group(1)}'
m_right = re.search(r'BuffNum8Right := ("\|<buff_num8_right>\*80\$12\.[\w+/]+")', out)
assert m_right, "generator output has no BuffNum8Right line"
right_line = f'BuffNum8Right := {m_right.group(1)}'
m_b4 = re.search(r'buff_num4_bottom := ("\|<buff_num4_bottom>\*80\$32\.[\w+/]+")', out)
assert m_b4, "generator output has no buff_num4_bottom line"
b4_line = f'BuffNum4Bottom := {m_b4.group(1)}'
m_t5 = re.search(r'buff_num5_top := ("\|<buff_num5_top>\*80\$32\.[\w+/]+")', out)
assert m_t5, "generator output has no buff_num5_top line"
t5_line = f'BuffNum5Top := {m_t5.group(1)}'
m_b6 = re.search(r'buff_num6_bottom := ("\|<buff_num6_bottom>\*80\$32\.[\w+/]+")', out)
assert m_b6, "generator output has no buff_num6_bottom line"
b6_line = f'BuffNum6Bottom := {m_b6.group(1)}'

new_text = emit_block(ORDER, by_name)
new_png = emit_block(PNG_ORDER, png_by_name)

src = open(AHK, encoding="utf-8-sig").read()
src = inject_block(src, "BuffText", new_text)
src = delete_block(src, "BuffNum7Text")
src = delete_block(src, "BuffText3")
if "BuffText2 := [" in src:
    src = inject_block(src, "BuffText2", new_png)
else:
    anchor = "BuffText := [\n" + "\n".join(new_text) + "\n]"
    idx = src.index(anchor) + len(anchor)
    src = src[:idx] + "\nBuffText2 := [\n" + "\n".join(new_png) + "\n]" + src[idx:]
src = inject_line(src, "BuffNum7Bottom", bottom_line)
src = inject_line(src, "BuffNum8Right", right_line)
src = inject_line(src, "BuffNum4Bottom", b4_line)
src = inject_line(src, "BuffNum5Top", t5_line)
src = inject_line(src, "BuffNum6Bottom", b6_line)
open(AHK, "w", encoding="utf-8-sig", newline="").write(src)

after = open(AHK, encoding="utf-8-sig").read()
verify_block(after, "BuffText", ORDER, new_text)
verify_block(after, "BuffText2", PNG_ORDER, new_png)
assert "BuffNum7Text" not in after, "BuffNum7Text block was not removed"
assert "BuffText3" not in after, "BuffText3 block was not removed"
for header, m_gen in (("BuffNum7Bottom", m_bottom), ("BuffNum8Right", m_right),
                      ("BuffNum4Bottom", m_b4), ("BuffNum5Top", m_t5), ("BuffNum6Bottom", m_b6)):
    m_after = re.search(re.escape(header) + r' := ("\|<[^>]+>\*80\$\d+\.[\w+/]+")', after)
    assert m_after and m_after.group(1) == m_gen.group(1), f"injected {header} does not match generator output"
print("injected BuffText (5 patterns at T=80), BuffText2 (5 png patterns at T=80),")
print("BuffNum4Bottom (32x11), BuffNum5Top (32x12), BuffNum6Bottom (32x11),")
print("BuffNum7Bottom (22x11) and BuffNum8Right (12x32); BuffText3 removed;")
print("verified byte-identical to generator output")
