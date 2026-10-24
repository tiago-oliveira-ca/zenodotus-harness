#!/usr/bin/env python3
"""Lint skill frontmatter: name matches its directory, description present, under the length ceiling,
and a 'Trigger on:' list exists. Exits non-zero on any violation."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEILING = 1024
bad = []
for skill in sorted((ROOT / "skills").rglob("SKILL.md")):
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    rel = skill.relative_to(ROOT)
    if not m:
        bad.append(f"{rel}: no frontmatter")
        continue
    front = m.group(1)
    name = re.search(r"^name:\s*(\S+)", front, re.M)
    desc = re.search(r"^description:\s*>?\s*\n?(.*)", front, re.S | re.M)
    if not name or name.group(1) != skill.parent.name:
        bad.append(f"{rel}: name does not match directory")
    if not desc:
        bad.append(f"{rel}: no description")
        continue
    d = " ".join(desc.group(1).split())
    if len(d) > CEILING:
        bad.append(f"{rel}: description is {len(d)} chars (ceiling {CEILING})")
    if "Trigger on:" not in d and "trigger on:" not in d.lower():
        bad.append(f"{rel}: description has no 'Trigger on:' list")
for line in bad:
    print(line)
print(f"{len(bad)} problem(s)")
sys.exit(1 if bad else 0)
