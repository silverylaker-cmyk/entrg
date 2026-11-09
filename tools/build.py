#!/usr/bin/env python3
"""귀코목 알지 — 정적 페이지 생성기.

data/diseases.json 하나를 기준으로 아래를 다시 만든다.
  - 대문(index.html)의 탐험로 목록 (build:routes 마커 사이)
  - 귀/코/목 허브 페이지 (ear/, nose/, throat/ 의 index.html)
  - sitemap.xml

질환 페이지 자체는 직접 작성한다. 새 질환 페이지를 올리면
diseases.json 해당 항목에 "published": "YYYY-MM-DD" 를 넣고 다시 실행한다.

사용: python3 tools/build.py
"""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://entrg.net"
DATA = json.loads((ROOT / "data" / "diseases.json").read_text(encoding="utf-8"))

HEAD = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="귀코목 알지">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="ko_KR">
  <meta name="theme-color" content="#edf1ee">
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <link rel="stylesheet" href="/assets/site.css">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <script type="application/ld+json">
{jsonld}
  </script>
</head>
<body>
  <a class="skip" href="#main">본문으로 건너뛰기</a>
  <header class="site-header">
    <a class="wordmark" href="/"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>귀코목 알지</a>
    <nav class="site-nav" aria-label="주요 메뉴">
{nav}
    </nav>
  </header>
"""

FOOT = """
  <footer class="site-footer">
    <div class="inner">
      <p>이 사이트의 글은 일반적인 의학 정보이며 진료를 대신하지 않습니다. 증상이 있거나 오래 지속되면 이비인후과 진료를 받으세요.</p>
      <p>작성·검수 이비인후과 전문의 박종원 © 2026 귀코목 알지</p>
    </div>
  </footer>
</body>
</html>
"""

NAV = [("ear", "/ear/", "귀"), ("nose", "/nose/", "코"), ("throat", "/throat/", "목"), ("about", "/about/", "소개")]


def nav(current=None):
    out = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        out.append(f'      <a href="{href}"{cur}>{label}</a>')
    return "\n".join(out)


def stop_path(region, seg, stop):
    base = seg.get("base", region["id"])
    return f"/{base}/{stop['slug']}/"


def route_list(region, with_symptom=False, indent="        "):
    lines = [f'{indent}<ol class="line {region["id"]}">']
    for seg in region["segments"]:
        lines.append(f'{indent}  <li class="seg" aria-hidden="true">{escape(seg["name"])}</li>')
        for st in seg["stops"]:
            name = escape(st["name"])
            sym = f'<span class="sym">{escape(st["symptom"])}</span>' if with_symptom else ""
            if st.get("published"):
                href = stop_path(region, seg, st)
                lines.append(f'{indent}  <li class="stop open"><a href="{href}">{name}</a>{sym}</li>')
            else:
                lines.append(f'{indent}  <li class="stop"><span class="soon">{name}<em>준비 중</em></span>{sym}</li>')
    lines.append(f"{indent}</ol>")
    return "\n".join(lines)


def build_home():
    parts = ['      <div class="route-grid">']
    for r in DATA["regions"]:
        parts.append(f'        <div class="route-col">')
        parts.append(f'          <h3><a href="/{r["id"]}/">{r["name"]}</a><small>{escape(r["route"])}</small></h3>')
        parts.append(f'          <p>{escape(r["intro"])}</p>')
        parts.append(route_list(r, indent="          "))
        parts.append("        </div>")
    parts.append("      </div>")
    block = "\n".join(parts)
    p = ROOT / "index.html"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"(<!-- build:routes -->)(.*?)(\s*<!-- /build:routes -->)",
               lambda m: m.group(1) + "\n" + block + m.group(3), s, flags=re.S)
    p.write_text(s, encoding="utf-8")


def build_hub(r):
    url = f"{SITE}/{r['id']}/"
    count = sum(len(s["stops"]) for s in r["segments"])
    names = [st["name"] for s in r["segments"] for st in s["stops"]]
    desc = f"{r['name']} 질환 {count}가지: {', '.join(names[:6])} 등. 증상, 검사, 치료를 이비인후과 전문의가 설명합니다."
    items = []
    for s in r["segments"]:
        for st in s["stops"]:
            if st.get("published"):
                items.append({"@type": "ListItem", "position": len(items) + 1,
                              "url": SITE + stop_path(r, s, st), "name": st["name"]})
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "@id": url + "#webpage", "url": url,
             "name": f"{r['name']} 질환 안내", "inLanguage": "ko-KR",
             "isPartOf": {"@id": f"{SITE}/#website"},
             "about": {"@type": "AnatomicalStructure", "name": r["name"]},
             "reviewedBy": {"@id": f"{SITE}/#physician"},
             **({"mainEntity": {"@type": "ItemList", "itemListElement": items}} if items else {})},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "귀코목 알지", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": r["name"], "item": url}]}
        ]
    }
    head = HEAD.format(
        title=f"{r['name']} 질환 안내 | 귀코목 알지",
        og_title=f"{r['name']}: {r['route']}",
        desc=escape(desc), url=url,
        jsonld="\n".join("  " + l for l in json.dumps(jsonld, ensure_ascii=False, indent=2).splitlines()),
        nav=nav(r["id"]))
    body = f"""
  <main id="main" class="wrap c-{r['id']}">
    <div class="page-head">
      <p class="crumbs"><a href="/">귀코목 알지</a><span aria-hidden="true">/</span>{r['name']}</p>
      <h1><span class="dot" aria-hidden="true"></span>{r['name']}: {escape(r['route'])}</h1>
      <p class="lede">{escape(r['intro'])} 길을 따라 {count}가지 질환을 차례로 정리하고 있습니다.</p>
    </div>
    <div class="hub-body">
{route_list(r, with_symptom=True, indent="      ")}
    </div>
  </main>
"""
    out = ROOT / r["id"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head + body + FOOT, encoding="utf-8")


def build_sitemap():
    urls = [(f"{SITE}/", None), (f"{SITE}/about/", None)]
    urls += [(f"{SITE}/{r['id']}/", None) for r in DATA["regions"]]
    for r in DATA["regions"]:
        for s in r["segments"]:
            for st in s["stops"]:
                if st.get("published"):
                    urls.append((SITE + stop_path(r, s, st), st["published"]))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        lm = f"<lastmod>{mod}</lastmod>" if mod else ""
        lines.append(f"  <url><loc>{loc}</loc>{lm}</url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_home()
    for region in DATA["regions"]:
        build_hub(region)
    build_sitemap()
    print("built: index routes, hubs", [r["id"] for r in DATA["regions"]], "sitemap")
