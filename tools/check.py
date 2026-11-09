#!/usr/bin/env python3
"""귀코목 알지 — 구조화 데이터 점검.

모든 페이지의 JSON-LD를 읽어 아래를 확인한다. 오류가 있으면 종료 코드 1.
  - JSON 문법
  - {"@id": ...} 참조가 사이트 어딘가에 정의된 노드를 가리키는지
  - url / item 으로 적힌 entrg.net 주소에 실제 파일이 있는지
  - 날짜가 YYYY-MM-DD 형식인지 (자리표시자 금지)
  - MedicalWebPage 필수 항목 (작성자, 검수자, 발행일, 검수일, 수정일, 주제)
  - FAQ 질문·답이 화면 본문에 그대로 보이는지 (구글 요건)
  - canonical 과 JSON-LD url 일치
  - sitemap.xml 이 실제 공개 페이지와 일치하는지

사용: python3 tools/check.py
"""
import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://entrg.net"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_KEYS = {"datePublished", "dateModified", "lastReviewed", "dateCreated"}

errors, warns = [], []


def pages():
    for p in sorted(ROOT.rglob("index.html")):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        rel = "/" + str(p.parent.relative_to(ROOT)).replace("\\", "/") + "/"
        yield ("/" if rel == "/./" else rel), p


def url_to_file(u):
    if not u.startswith(SITE):
        return None
    path = u[len(SITE):].split("#")[0]
    f = ROOT / path.lstrip("/") / "index.html" if path.endswith("/") else ROOT / path.lstrip("/")
    return f


def walk(node, fn, key=None):
    if isinstance(node, dict):
        fn(node, key)
        for k, v in node.items():
            walk(v, fn, k)
    elif isinstance(node, list):
        for v in node:
            walk(v, fn, key)


def visible_text(html):
    body = re.search(r"<main.*?</main>", html, re.S)
    t = re.sub(r"<[^>]+>", " ", body.group(0) if body else html)
    return re.sub(r"\s+", " ", unescape(t)).strip()


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


defined, refs, per_page = {}, [], {}
for rel, f in pages():
    html = f.read_text(encoding="utf-8")
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not blocks:
        warns.append(f"{rel}: JSON-LD 없음")
        continue
    graph = []
    for b in blocks:
        try:
            d = json.loads(b)
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: JSON 문법 오류 {e}")
            continue
        graph += d.get("@graph", [d])
    per_page[rel] = (html, graph)

    def collect(n, key):
        if "@id" in n and "@type" in n:
            defined.setdefault(n["@id"], rel)
        elif set(n) == {"@id"}:
            refs.append((rel, n["@id"]))
        for k in DATE_KEYS & set(n):
            if not DATE.match(str(n[k])) and not re.match(r"^\d{4}$", str(n[k])):
                errors.append(f"{rel}: {n.get('@type')} {k} 날짜 형식 오류 '{n[k]}'")
        for k in ("url", "item"):
            v = n.get(k)
            if isinstance(v, str) and v.startswith(SITE):
                tf = url_to_file(v)
                if tf and not tf.exists():
                    errors.append(f"{rel}: {k} 주소에 해당하는 파일 없음 {v}")
    for node in graph:
        walk(node, collect)

    canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    pages_nodes = [n for n in graph if str(n.get("@type", "")).endswith("Page")]
    if canon and pages_nodes and pages_nodes[0].get("url") != canon.group(1):
        errors.append(f"{rel}: canonical({canon.group(1)})과 JSON-LD url({pages_nodes[0].get('url')}) 불일치")

    for n in graph:
        t = n.get("@type")
        if t == "MedicalWebPage":
            for k in ("author", "reviewedBy", "datePublished", "lastReviewed", "dateModified", "about", "mainEntity", "inLanguage"):
                if k not in n:
                    errors.append(f"{rel}: MedicalWebPage 에 {k} 없음")
        if t == "MedicalCondition":
            for k in ("name", "description", "signOrSymptom", "possibleTreatment"):
                if k not in n:
                    errors.append(f"{rel}: MedicalCondition 에 {k} 없음")
            if not n.get("code"):
                warns.append(f"{rel}: MedicalCondition 질병코드 없음")
        if t == "FAQPage":
            text = visible_text(html)
            for q in n.get("mainEntity", []):
                if norm(q["name"]) not in text:
                    errors.append(f"{rel}: FAQ 질문이 화면에 없음 '{q['name'][:30]}'")
                if norm(q["acceptedAnswer"]["text"]) not in text:
                    errors.append(f"{rel}: FAQ 답이 화면 본문과 다름 '{q['name'][:30]}'")

for rel, i in refs:
    if i not in defined:
        errors.append(f"{rel}: 참조 {i} 를 정의한 노드가 사이트에 없음")

# sitemap
sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
in_sitemap = set(re.findall(r"<loc>(.*?)</loc>", sm))
public = {SITE + rel for rel in per_page if rel != "/404/"}
for u in sorted(public - in_sitemap):
    errors.append(f"sitemap.xml 에 빠진 페이지 {u}")
for u in sorted(in_sitemap - public):
    errors.append(f"sitemap.xml 에 있는데 파일이 없음 {u}")

types = {}
for rel, (_, g) in per_page.items():
    for n in g:
        types[n.get("@type")] = types.get(n.get("@type"), 0) + 1
print(f"점검: 페이지 {len(per_page)}개, 정의 노드 {len(defined)}개, 참조 {len(refs)}개, sitemap {len(in_sitemap)}개")
print("  노드 종류: " + ", ".join(f"{k} {v}" for k, v in sorted(types.items(), key=lambda x: -x[1])))
for w in warns:
    print("  주의:", w)
for e in errors:
    print("  오류:", e)
print("결과:", "통과" if not errors else f"오류 {len(errors)}건")
sys.exit(1 if errors else 0)
