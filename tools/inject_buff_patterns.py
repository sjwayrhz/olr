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

def delete_line(src, header):
    m = re.search(re.escape(header) + r' := ".*"\n?', src)
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
SUBS = {"BuffNum7Right": ("buff_num7_right", 12)}
sub_lines = {}
sub_matches = {}
for header, (label, width) in SUBS.items():
    m = re.search(re.escape(label) + r' := ("\|<' + label + r'>\*80\$' + str(width) + r'\.[\w+/]+")', out)
    assert m, f"generator output has no {label} line"
    sub_matches[header] = m
    sub_lines[header] = f'{header} := {m.group(1)}'

m_err = re.search(r'buff4s_error := ("\|<buff4s_error>\*80\$32\.[\w+/]+")', out)
assert m_err, "generator output has no buff4s_error line"
err_line = f'ErrorText := {m_err.group(1)}'

m_err2 = re.search(r'buff4s_error_2 := ("\|<buff4s_error_2>\*80\$32\.[\w+/]+")', out)
assert m_err2, "generator output has no buff4s_error_2 line"
err2_line = f'ErrorText2 := {m_err2.group(1)}'

m_n5_3 = re.search(r'BuffNum5Third := ("\|<buff_num5_0011>\*80\$32\.[\w+/]+")', out)
assert m_n5_3, "generator output has no BuffNum5Third line"
n5_3_line = f'BuffNum5Third := {m_n5_3.group(1)}'

m_n4_3 = re.search(r'BuffNum4Third := ("\|<buff_num4_0003>\*80\$32\.[\w+/]+")', out)
assert m_n4_3, "generator output has no BuffNum4Third line"
n4_3_line = f'BuffNum4Third := {m_n4_3.group(1)}'

m_n6_3 = re.search(r'BuffNum6Third := ("\|<buff_num6_0026>\*80\$32\.[\w+/]+")', out)
assert m_n6_3, "generator output has no BuffNum6Third line"
n6_3_line = f'BuffNum6Third := {m_n6_3.group(1)}'

m_n7_3 = re.search(r'BuffNum7Third := ("\|<buff_num7_0007>\*80\$32\.[\w+/]+")', out)
assert m_n7_3, "generator output has no BuffNum7Third line"
n7_3_line = f'BuffNum7Third := {m_n7_3.group(1)}'

m_n7_top = re.search(r'BuffNum7Top := ("\|<buff_num7_top>\*80\$32\.[\w+/]+")', out)
assert m_n7_top, "generator output has no BuffNum7Top line"
n7_top_line = f'BuffNum7Top := {m_n7_top.group(1)}'

m_n7_r2 = re.search(r'BuffNum7Right2 := ("\|<buff_num7_right2>\*80\$12\.[\w+/]+")', out)
assert m_n7_r2, "generator output has no BuffNum7Right2 line"
n7_r2_line = f'BuffNum7Right2 := {m_n7_r2.group(1)}'

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
src = inject_line(src, "ErrorText", err_line)
src = inject_line(src, "ErrorText2", err2_line)
src = inject_line(src, "BuffNum5Third", n5_3_line)
src = inject_line(src, "BuffNum4Third", n4_3_line)
src = inject_line(src, "BuffNum6Third", n6_3_line)
src = inject_line(src, "BuffNum7Third", n7_3_line)
src = inject_line(src, "BuffNum7Top", n7_top_line)
src = inject_line(src, "BuffNum7Right2", n7_r2_line)
for header in SUBS:
    src = inject_line(src, header, sub_lines[header])
for old in ("BuffNum4Top", "BuffNum4Right", "BuffNum4Bottom", "BuffNum5Right", "BuffNum5Bottom", "BuffNum5Top", "BuffNum6Right", "BuffNum6Bottom", "BuffNum7Bottom", "BuffNum8Right"):
    src = delete_line(src, old)
open(AHK, "w", encoding="utf-8-sig", newline="").write(src)

after = open(AHK, encoding="utf-8-sig").read()
verify_block(after, "BuffText", ORDER, new_text)
verify_block(after, "BuffText2", PNG_ORDER, new_png)
assert "BuffNum7Text" not in after, "BuffNum7Text block was not removed"
assert "BuffText3" not in after, "BuffText3 block was not removed"
for header, (label, width) in SUBS.items():
    assert header in after, f"{header} missing after injection"
    m_after = re.search(re.escape(header) + r' := ("\|<[^>]+>\*80\$' + str(width) + r'\.[\w+/]+")', after)
    assert m_after and m_after.group(1) == sub_matches[header].group(1), f"injected {header} does not match generator output"
m_err_after = re.search(r'ErrorText := ("\|<buff4s_error>\*80\$32\.[\w+/]+")', after)
assert m_err_after and m_err_after.group(1) == m_err.group(1), "injected ErrorText does not match generator output"
m_err2_after = re.search(r'ErrorText2 := ("\|<buff4s_error_2>\*80\$32\.[\w+/]+")', after)
assert m_err2_after and m_err2_after.group(1) == m_err2.group(1), "injected ErrorText2 does not match generator output"
m_n5_3_after = re.search(r'BuffNum5Third := ("\|<buff_num5_0011>\*80\$32\.[\w+/]+")', after)
assert m_n5_3_after and m_n5_3_after.group(1) == m_n5_3.group(1), "injected BuffNum5Third does not match generator output"
m_n4_3_after = re.search(r'BuffNum4Third := ("\|<buff_num4_0003>\*80\$32\.[\w+/]+")', after)
assert m_n4_3_after and m_n4_3_after.group(1) == m_n4_3.group(1), "injected BuffNum4Third does not match generator output"
m_n6_3_after = re.search(r'BuffNum6Third := ("\|<buff_num6_0026>\*80\$32\.[\w+/]+")', after)
assert m_n6_3_after and m_n6_3_after.group(1) == m_n6_3.group(1), "injected BuffNum6Third does not match generator output"
m_n7_3_after = re.search(r'BuffNum7Third := ("\|<buff_num7_0007>\*80\$32\.[\w+/]+")', after)
assert m_n7_3_after and m_n7_3_after.group(1) == m_n7_3.group(1), "injected BuffNum7Third does not match generator output"
m_n7_top_after = re.search(r'BuffNum7Top := ("\|<buff_num7_top>\*80\$32\.[\w+/]+")', after)
assert m_n7_top_after and m_n7_top_after.group(1) == m_n7_top.group(1), "injected BuffNum7Top does not match generator output"
m_n7_r2_after = re.search(r'BuffNum7Right2 := ("\|<buff_num7_right2>\*80\$12\.[\w+/]+")', after)
assert m_n7_r2_after and m_n7_r2_after.group(1) == m_n7_r2.group(1), "injected BuffNum7Right2 does not match generator output"
for old in ("BuffNum4Top", "BuffNum4Right", "BuffNum4Bottom", "BuffNum5Right", "BuffNum5Bottom", "BuffNum5Top", "BuffNum6Right", "BuffNum6Bottom", "BuffNum7Bottom", "BuffNum8Right"):
    assert old not in after, f"old {old} was not removed"
print("injected BuffText (5 patterns at T=80), BuffText2 (5 png patterns at T=80),")
print("BuffNum5Third (ScreenShot0011 bright fish, T=80),")
print("BuffNum4Third (ScreenShot0003, T=80),")
print("BuffNum6Third (ScreenShot0026, T=80),")
print("BuffNum7Third (ScreenShot0007, T=80),")
print("BuffNum7Top (digit-masked top strip y0-12 from 0007, T=80),")
print("BuffNum7Right2 (digit-masked right strip x20-32 from 0007, T=80),")
print("ErrorText (buff4s_error at T=80, 32x32, original ScreenShot0004), ErrorText2 (buff4s_error_2 at T=80, ScreenShot0004 2026-11-28), BuffNum7Right (12x32);")
print("BuffNum8Right removed 2026-11-28 (terrain false positives at y=168);")
print("num4/5/6 sub-patterns removed; verified byte-identical to generator output")
