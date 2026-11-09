#!/usr/bin/env python3
"""검수 날짜 일괄 지정.

원장 검수를 마친 날, 모든 질환의 발행일·검수일·수정일을 그날로 맞춘다.
이미 발행일이 다른 날로 적힌 질환(먼저 발행된 질환)은 발행일을 그대로 두고 검수일·수정일만 바꾼다.

사용: python3 tools/set_review_date.py 2026-11-20 [--only slug1,slug2]
      python3 tools/build.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT_DATE = "2026-11-09"  # 초안 작성일로 넣어 둔 값
REVIEWED = {"chronic-sinusitis"}  # 이미 검수·발행된 질환은 --only 로 지정할 때만 바꿈

if len(sys.argv) < 2 or not re.match(r"^\d{4}-\d{2}-\d{2}$", sys.argv[1]):
    sys.exit(__doc__)
day = sys.argv[1]
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[2] == "--only" else None

changed = []
for f in sorted((ROOT / "data" / "conditions").glob("*.json")):
    if only and f.stem not in only:
        continue
    if not only and f.stem in REVIEWED:
        continue
    c = json.loads(f.read_text(encoding="utf-8"))
    c["lastReviewed"] = day
    c["dateModified"] = day
    f.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    changed.append(f.stem)

p = ROOT / "data" / "diseases.json"
s = p.read_text(encoding="utf-8")
for slug in changed:
    s = re.sub(rf'("slug": "{slug}"[^{{}}]*"published": ")({DRAFT_DATE})(")', rf"\g<1>{day}\3", s)
json.loads(s)
p.write_text(s, encoding="utf-8")
print(f"{len(changed)}편 검수일을 {day}로 지정. 이어서 python3 tools/build.py 실행")
