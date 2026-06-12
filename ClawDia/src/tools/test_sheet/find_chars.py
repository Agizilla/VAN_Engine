import json
from pathlib import Path

p = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\ComicCookCreatorStudio\narratives\ComicBook_Edition_1_Chapters_1to12.json")
lines = p.read_text(encoding="utf-8").split("\n")
# Scan for character names in panel dialogue keys
import re
chars = set()
for line in lines:
    m = re.search(r'"character":\s*"([^"]+)"', line)
    if m:
        chars.add(m.group(1))
for line in lines:
    m = re.search(r'"([A-Z][A-Z\s]+)":\s*"', line)
    if m:
        name = m.group(1).strip()
        if len(name) > 3 and " " not in name:
            chars.add(name)
for c in sorted(chars):
    print(c)
