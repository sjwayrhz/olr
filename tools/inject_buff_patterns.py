#!/usr/bin/env python3
"""Inject freshly generated FindText patterns (from gen_buff_patterns.py)
into olr_fishing.ahk programmatically. Never hand-copy pattern strings:
a single dropped character breaks the pattern (189 vs 190 chars, 2026-11-26).
Verifies each injected line matches the generator output exactly.
"""
import re
import subprocess
import sys

AHK = "/home/hatch/workspace/olr/olr_fishing.ahk"
GEN = "/home/hatch/workspace/olr/tools/gen_buff_patterns.py"

out = subprocess.run([sys.executable, GEN], capture_output=True, text=True, check=True).stdout
# Extract the AHK block: from 'BuffText := [' to the closing ']'
m = re.search(r"BuffText := \[\n(.*?)\n\]", out, re.S)
if not m:
    raise SystemExit("generator output has no BuffText block")
new_block_inner = m.group(1)
new_lines = [ln for ln in new_block_inner.splitlines() if ln.strip()]
assert len(new_lines) == 5, f"expected 5 pattern lines, got {len(new_lines)}"
for ln in new_lines:
    assert ln.strip().startswith(', "|<Buff'), f"unexpected line: {ln[:40]}"

src = open(AHK, encoding="utf-8-sig").read()
# Replace the BuffText array (from 'BuffText := [' to the first ']' after it)
m2 = re.search(r"BuffText := \[\n.*?\n\]", src, re.S)
if not m2:
    raise SystemExit("olr_fishing.ahk has no BuffText block")
new_block = "BuffText := [\n" + "\n".join(new_lines) + "\n]"
src2 = src[:m2.start()] + new_block + src[m2.end():]
open(AHK, "w", encoding="utf-8-sig", newline="").write(src2)

# Verify: re-read and confirm each pattern line is byte-identical to generator output
after = open(AHK, encoding="utf-8-sig").read()
m3 = re.search(r"BuffText := \[\n(.*?)\n\]", after, re.S)
got = [ln for ln in m3.group(1).splitlines() if ln.strip()]
assert got == new_lines, "injected patterns do not match generator output"
for ln in got:
    # threshold must be *120 now
    assert "*120$" in ln, f"wrong threshold in line: {ln[:50]}"
print("injected 5 patterns at T=120, verified byte-identical to generator output")
for ln in got:
    print(" ", ln[:60], "... len", len(ln))
