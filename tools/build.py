#!/usr/bin/env python3
"""귀코목 알지 — 정적 페이지 생성기.

원본 데이터
  - data/diseases.json            30개 질환 목록·순서·발행일
  - data/conditions/<slug>.json    발행한 질환 한 편의 본문·구조화 데이터 (질환당 한 파일)
  - data/symptoms.json             대문 "증상으로 찾기" (증상 → 관련 질환)
  - data/facts.json                "알고 보면 신기한 귀·코·목" 상식

이 스크립트가 다시 만드는 것
  - 대문(index.html)의 탐험로 목록과 JSON-LD (build: 마커 사이)
  - 귀/코/목 허브 페이지, 상식 페이지(/facts/)
  - 질환 페이지 (data/conditions/<slug>.json 이 있는 발행 질환)
  - sitemap.xml, llms.txt
마지막에 tools/check.py 로 구조화 데이터를 점검한다.

새 질환 발행
  1. data/conditions/chronic-sinusitis.json 을 복사해 <slug>.json 작성
  2. data/diseases.json 해당 항목에 "published": "YYYY-MM-DD" 추가
  3. python3 tools/build.py

사용: python3 tools/build.py
"""
import json
import re
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://entrg.net"
CSS_V = "20261109c"
DATA = json.loads((ROOT / "data" / "diseases.json").read_text(encoding="utf-8"))
SYMPTOMS = json.loads((ROOT / "data" / "symptoms.json").read_text(encoding="utf-8"))
FACTS = json.loads((ROOT / "data" / "facts.json").read_text(encoding="utf-8"))
COND_DIR = ROOT / "data" / "conditions"

SITE_NAME = "귀코목 알지"
SITE_DESC = "귀, 코, 목 안쪽 길을 따라가며 이비인후과 질환의 증상, 검사, 치료를 이비인후과 전문의가 설명하는 의학정보 사이트."
PHYSICIAN = f"{SITE}/#physician"
WEBSITE = f"{SITE}/#website"
SPECIALTY = "https://schema.org/Otolaryngologic"
REGION_EN = {"ear": "Ear", "nose": "Nose", "throat": "Throat"}

HEAD = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="귀코목 알지">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:locale" content="ko_KR">
  <meta name="theme-color" content="#edf1ee">
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <link rel="stylesheet" href="/assets/site.css?v={css_v}">
  <script>try{{var a=sessionStorage.getItem("entrg-arrive");if(a){{sessionStorage.removeItem("entrg-arrive");document.documentElement.classList.add("arrive","arrive-"+a)}}}}catch(e){{}}</script>
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

NAV = [("ear", "/ear/", "귀"), ("nose", "/nose/", "코"), ("throat", "/throat/", "목"),
       ("facts", "/facts/", "상식"), ("about", "/about/", "소개")]


def nav(current=None):
    out = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        out.append(f'      <a href="{href}"{cur}>{label}</a>')
    return "\n".join(out)


def ld(graph, indent="  "):
    obj = {"@context": "https://schema.org", "@graph": graph}
    return "\n".join(indent + l for l in json.dumps(obj, ensure_ascii=False, indent=2).splitlines())


def head(*, title, desc, url, jsonld, nav_current, og_type="website", og_title=None, og_desc=None):
    return HEAD.format(title=escape(title), desc=escape(desc), url=url, og_type=og_type,
                       og_title=escape(og_title or title), og_desc=escape(og_desc or desc),
                       css_v=CSS_V, jsonld=jsonld, nav=nav(nav_current))


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def ko_date(iso):
    y, m, d = iso.split("-")
    return f"{int(y)}년 {int(m)}월 {int(d)}일"


def stop_path(region, seg, stop):
    base = seg.get("base", region["id"])
    return f"/{base}/{stop['slug']}/"


def published_stops():
    for r in DATA["regions"]:
        for s in r["segments"]:
            for st in s["stops"]:
                if st.get("published"):
                    yield r, s, st


def stop_index():
    idx = {}
    for r in DATA["regions"]:
        for s in r["segments"]:
            for st in s["stops"]:
                idx[st["slug"]] = (r, s, st)
    return idx


STOPS = None


def stop_link(slug):
    """발행한 질환은 질환 페이지로, 아직이면 허브의 해당 항목(쉬운 설명)으로."""
    r, s, st = STOPS[slug]
    return (stop_path(r, s, st) if st.get("published") else f"/{r['id']}/#{slug}"), st, r


def load_condition(slug):
    p = COND_DIR / f"{slug}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ---------- 공용 노드 ----------
def website_node():
    return {"@type": "WebSite", "@id": WEBSITE, "url": f"{SITE}/", "name": SITE_NAME,
            "alternateName": "ENTRG", "description": SITE_DESC, "inLanguage": "ko-KR",
            "publisher": {"@id": PHYSICIAN}}


def person_stub():
    return {"@type": "Person", "@id": PHYSICIAN, "name": "박종원", "jobTitle": "이비인후과 전문의",
            "url": f"{SITE}/about/"}


def anatomy_node(r):
    return {"@type": "AnatomicalStructure", "name": r["name"], "alternateName": REGION_EN[r["id"]]}


def breadcrumb(url, items):
    return {"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(items)]}


# ---------- 대문 ----------
def route_list(region, with_symptom=False, indent="        "):
    lines = [f'{indent}<ol class="line {region["id"]}">']
    for seg in region["segments"]:
        lines.append(f'{indent}  <li class="seg" aria-hidden="true">{escape(seg["name"])}</li>')
        for st in seg["stops"]:
            name = escape(st["name"])
            sym, sid = "", ""
            if with_symptom:
                sid = f' id="{st["slug"]}"'
                easy = f'<span class="easy">{escape(st["easy"])}</span>' if st.get("easy") else ""
                sym = f'{easy}<span class="sym">흔한 증상 · {escape(st["symptom"])}</span>'
            if st.get("published"):
                href = stop_path(region, seg, st)
                lines.append(f'{indent}  <li class="stop open"{sid}><a href="{href}">{name}</a>{sym}</li>')
            else:
                lines.append(f'{indent}  <li class="stop"{sid}><span class="soon">{name}<em>준비 중</em></span>{sym}</li>')
    lines.append(f"{indent}</ol>")
    return "\n".join(lines)


def home_jsonld(page_title, page_desc):
    url = f"{SITE}/"
    hubs = [(f"{r['name']}: {r['route']}", f"{SITE}/{r['id']}/") for r in DATA["regions"]]
    webpage = {
        "@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page_title,
        "description": page_desc, "inLanguage": "ko-KR", "isPartOf": {"@id": WEBSITE},
        "about": [anatomy_node(r) for r in DATA["regions"]],
        "author": {"@id": PHYSICIAN},
        "hasPart": [{"@id": u + "#webpage"} for _, u in hubs] + [{"@id": f"{SITE}/facts/#webpage"}],
        "mainEntity": {"@type": "ItemList", "name": "귀코목 탐험로", "numberOfItems": len(hubs),
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "url": u}
                                           for i, (n, u) in enumerate(hubs)]},
    }
    return [website_node(), person_stub(), webpage]


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
    s = re.sub(r"(<!-- build:symptoms -->)(.*?)(\s*<!-- /build:symptoms -->)",
               lambda m: m.group(1) + "\n" + symptoms_section() + m.group(3), s, flags=re.S)
    s = re.sub(r"(<!-- build:facts -->)(.*?)(\s*<!-- /build:facts -->)",
               lambda m: m.group(1) + "\n" + facts_section() + m.group(3), s, flags=re.S)
    title = re.search(r"<title>(.*?)</title>", s).group(1)
    desc = re.search(r'<meta name="description" content="(.*?)">', s).group(1)
    js = "  <script type=\"application/ld+json\">\n" + ld(home_jsonld(title, desc)) + "\n  </script>"
    s = re.sub(r"(<!-- build:jsonld -->\n)(.*?)(\n\s*<!-- /build:jsonld -->)",
               lambda m: m.group(1) + js + m.group(3), s, flags=re.S)
    p.write_text(s, encoding="utf-8")


def symptoms_section():
    cards = []
    for it in SYMPTOMS["items"]:
        chips = []
        for slug in it["slugs"]:
            href, st, _ = stop_link(slug)
            cls = "chip open" if st.get("published") else "chip"
            chips.append(f'<li><a class="{cls}" href="{href}">{escape(st["name"])}</a></li>')
        cards.append(f"""        <div class="finder-item c-{it['region']}">
          <h3>{escape(it['q'])}</h3>
          <ul>{''.join(chips)}</ul>
        </div>""")
    return f"""    <section class="finder wrap" aria-labelledby="finder-title">
      <div class="section-head">
        <h2 id="finder-title">증상으로 찾기</h2>
        <p>{escape(SYMPTOMS['intro'])}</p>
      </div>
      <div class="finder-grid">
{chr(10).join(cards)}
      </div>
      <p class="finder-urgent"><strong>바로 진료가 필요할 때</strong>{escape(SYMPTOMS['urgent'])}</p>
    </section>"""


def fact_card(f, with_id=False, heading="h3"):
    rel = []
    for slug in f["related"]:
        href, st, _ = stop_link(slug)
        rel.append(f'<a href="{href}">{escape(st["name"])}</a>')
    region = next(r for r in DATA["regions"] if r["id"] == f["region"])
    if not rel:
        rel.append(f'<a href="/{region["id"]}/">{region["name"]} 탐험로</a>')
    fid = f' id="{f["id"]}"' if with_id else ""
    return f"""<article class="fact c-{f['region']}"{fid}>
          <p class="fact-figure">{escape(f['figure'])}</p>
          <{heading}>{escape(f['title'])}</{heading}>
          <p>{escape(f['body'])}</p>
          <p class="fact-rel">더 알아보기 {' · '.join(rel)}</p>
        </article>"""


def facts_section():
    picks = [f for f in FACTS["items"] if f.get("home")]
    cards = "\n        ".join(fact_card(f) for f in picks)
    return f"""    <section class="facts wrap" aria-labelledby="facts-title">
      <div class="section-head">
        <h2 id="facts-title">{escape(FACTS['title'])}</h2>
        <p>{escape(FACTS['intro'])}</p>
      </div>
      <div class="fact-grid">
        {cards}
      </div>
      <p class="more"><a href="/facts/">상식 {len(FACTS['items'])}가지 모두 보기</a></p>
    </section>"""


def build_facts_page():
    url = f"{SITE}/facts/"
    title = FACTS["title"]
    desc = (f"{FACTS['intro']} " + ", ".join(f["title"] for f in FACTS["items"][:3]) + " 등 "
            f"{len(FACTS['items'])}가지를 이비인후과 전문의가 설명합니다.")
    page = {"@type": "CollectionPage", "@id": url + "#webpage", "url": url, "name": title,
            "description": desc, "inLanguage": "ko-KR", "isPartOf": {"@id": WEBSITE},
            "breadcrumb": {"@id": url + "#breadcrumb"},
            "about": [anatomy_node(r) for r in DATA["regions"]], "specialty": SPECIALTY,
            "author": {"@id": PHYSICIAN}, "reviewedBy": {"@id": PHYSICIAN},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(FACTS["items"]),
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f["title"],
                                                "url": f"{url}#{f['id']}"} for i, f in enumerate(FACTS["items"])]}}
    graph = [page, person_stub(), breadcrumb(url, [(SITE_NAME, f"{SITE}/"), ("상식", url)])]
    h = head(title=f"{title} | 귀코목 알지", desc=desc, url=url, jsonld=ld(graph), nav_current="facts")
    groups = []
    for r in DATA["regions"]:
        cards = "\n        ".join(fact_card(f, with_id=True, heading="h3") for f in FACTS["items"] if f["region"] == r["id"])
        groups.append(f"""    <section class="fact-group c-{r['id']}" aria-labelledby="fg-{r['id']}">
      <h2 id="fg-{r['id']}"><span class="dot" aria-hidden="true"></span>{r['name']}</h2>
      <div class="fact-grid two">
        {cards}
      </div>
    </section>""")
    body = f"""
  <main id="main" class="wrap">
    <div class="page-head">
      <p class="crumbs"><a href="/">귀코목 알지</a><span aria-hidden="true">/</span>상식</p>
      <h1>{escape(title)}</h1>
      <p class="lede">{escape(FACTS['intro'])}</p>
    </div>
{chr(10).join(groups)}
  </main>
"""
    out = ROOT / "facts" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(h + body + FOOT, encoding="utf-8")


# ---------- 허브 ----------
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
    page = {"@type": "CollectionPage", "@id": url + "#webpage", "url": url,
            "name": f"{r['name']} 질환 안내", "description": desc, "inLanguage": "ko-KR",
            "isPartOf": {"@id": WEBSITE}, "breadcrumb": {"@id": url + "#breadcrumb"},
            "about": anatomy_node(r), "specialty": SPECIALTY,
            "reviewedBy": {"@id": PHYSICIAN}}
    if items:
        page["hasPart"] = [{"@id": it["url"] + "#webpage"} for it in items]
        page["mainEntity"] = {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items}
    graph = [page, breadcrumb(url, [(SITE_NAME, f"{SITE}/"), (r["name"], url)])]
    h = head(title=f"{r['name']} 질환 안내 | 귀코목 알지", og_title=f"{r['name']}: {r['route']}",
             desc=desc, url=url, jsonld=ld(graph), nav_current=r["id"])
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
    out.write_text(h + body + FOOT, encoding="utf-8")


# ---------- 질환 페이지 ----------
def render_blocks(blocks, ind="      "):
    out = []
    for b in blocks:
        if "h2" in b:
            out.append(f"\n{ind}<h2>{b['h2']}</h2>")
        elif "p" in b:
            cls = f' class="{b["class"]}"' if b.get("class") else ""
            out.append(f"{ind}<p{cls}>{b['p']}</p>")
            if b.get("class") == "definition":
                out.append("")
        elif "ul" in b:
            out.append(f"{ind}<ul>")
            out += [f"{ind}  <li>{li}</li>" for li in b["ul"]]
            out.append(f"{ind}</ul>")
        elif "steps" in b:
            out.append(f'{ind}<ol class="steps">')
            out += [f"{ind}  <li><strong>{s['title']}</strong>{s['text']}</li>" for s in b["steps"]]
            out.append(f"{ind}</ol>")
        elif "alert" in b:
            a = b["alert"]
            out.append(f'\n{ind}<section class="alert" aria-labelledby="alert-title">')
            out.append(f'{ind}  <h2 id="alert-title">{a["title"]}</h2>')
            out.append(f"{ind}  <ul>")
            out += [f"{ind}    <li>{li}</li>" for li in a["ul"]]
            out.append(f"{ind}  </ul>")
            if a.get("p"):
                out.append(f"{ind}  <p>{a['p']}</p>")
            out.append(f"{ind}</section>")
        else:
            raise ValueError(f"알 수 없는 본문 블록: {b}")
    return "\n".join(out)


def condition_jsonld(c, r, seg, st, url):
    cond = c["condition"]
    cid = url + "#condition"
    page = {
        "@type": "MedicalWebPage", "@id": url + "#webpage", "url": url, "name": c["seoTitle"],
        "description": c["metaDescription"], "inLanguage": "ko-KR",
        "isPartOf": {"@id": WEBSITE}, "breadcrumb": {"@id": url + "#breadcrumb"},
        "about": {"@id": cid}, "mainEntity": {"@id": cid},
        "specialty": SPECIALTY,
        "audience": {"@type": "PeopleAudience", "audienceType": "환자"},
        "medicalAudience": {"@type": "MedicalAudience", "audienceType": "Patient"},
        "author": {"@id": PHYSICIAN}, "reviewedBy": {"@id": PHYSICIAN},
        "datePublished": st["published"], "lastReviewed": c["lastReviewed"], "dateModified": c["dateModified"],
    }
    cites = []
    for ref in c.get("references", []):
        node = {"@type": "ScholarlyArticle", "name": ref["name"], "description": ref["citation"]}
        if ref.get("year"):
            node["datePublished"] = str(ref["year"])
        same = []
        if ref.get("doi"):
            same.append(f"https://doi.org/{ref['doi']}")
            node["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": ref["doi"]}
        if ref.get("pubmed"):
            same.append(f"https://pubmed.ncbi.nlm.nih.gov/{ref['pubmed']}/")
        if same:
            node["sameAs"] = same
        cites.append(node)
    if cites:
        page["citation"] = cites
    condition = {
        "@type": "MedicalCondition", "@id": cid, "name": cond["name"],
        "alternateName": cond["alternateName"], "url": url, "description": cond["description"],
        "code": [{"@type": "MedicalCode", "code": x["code"], "codingSystem": x["codingSystem"]} for x in cond["codes"]],
        "relevantSpecialty": SPECIALTY,
        "associatedAnatomy": {"@type": "AnatomicalStructure", **cond["anatomy"]},
        "signOrSymptom": [{"@type": "MedicalSymptom", "name": n} for n in cond["symptoms"]],
        "riskFactor": [{"@type": "MedicalRiskFactor", "name": n} for n in cond["riskFactors"]],
        "typicalTest": [{"@type": t["type"], "name": t["name"]} for t in cond["tests"]],
        "possibleTreatment": [{"@type": t["type"], "name": t["name"],
                               **({"alternateName": t["alternateName"]} if t.get("alternateName") else {})}
                              for t in cond["treatments"]],
        "possibleComplication": cond["complications"],
    }
    condition = {k: v for k, v in condition.items() if v not in ([], None, "")}
    faq = {"@type": "FAQPage", "@id": url + "#faq", "isPartOf": {"@id": url + "#webpage"},
           "mainEntity": [{"@type": "Question", "name": strip_tags(f["q"]),
                           "acceptedAnswer": {"@type": "Answer", "text": strip_tags(f["a"])}} for f in c["faq"]]}
    crumbs = breadcrumb(url, [(SITE_NAME, f"{SITE}/"), (r["name"], f"{SITE}/{r['id']}/"), (cond["name"], url)])
    return [page, person_stub(), condition, faq, crumbs]


def build_condition(r, seg, st, c):
    path = stop_path(r, seg, st)
    url = SITE + path
    h = head(title=f"{c['seoTitle']} | 귀코목 알지", og_title=c["seoTitle"], og_type="article",
             desc=c["metaDescription"], og_desc=c.get("ogDescription"), url=url,
             jsonld=ld(condition_jsonld(c, r, seg, st, url)), nav_current=r["id"])
    faq = "\n".join(f"""        <details>
          <summary>{f['q']}</summary>
          <p>{f['a']}</p>
        </details>""" for f in c["faq"])
    refs = " · ".join(ref["short"] for ref in c.get("references", []))
    ref_line = f"<br>\n        <strong>참고</strong> {refs}" if refs else ""
    body = f"""
  <main id="main" class="wrap c-{r['id']}">
    <div class="page-head">
      <p class="crumbs"><a href="/">귀코목 알지</a><span aria-hidden="true">/</span><a href="/{r['id']}/">{r['name']}</a><span aria-hidden="true">/</span>{escape(seg['name'])}</p>
      <h1><span class="dot" aria-hidden="true"></span>{c['title']}</h1>
    </div>

    <article class="article prose">
{render_blocks(c['body'])}

      <section class="faq" aria-labelledby="faq-title">
        <h2 id="faq-title">자주 묻는 질문</h2>
{faq}
      </section>

      <div class="reviewed">
        <p><strong>작성·검수</strong> 이비인후과 전문의 <a href="/about/">박종원</a><br>
        <strong>최종 검수일</strong> <time datetime="{c['lastReviewed']}">{ko_date(c['lastReviewed'])}</time>{ref_line}</p>
      </div>
    </article>
  </main>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(h + body + FOOT, encoding="utf-8")


# ---------- sitemap, llms.txt ----------
def build_sitemap():
    urls = [(f"{SITE}/", None), (f"{SITE}/facts/", None), (f"{SITE}/about/", None)]
    urls += [(f"{SITE}/{r['id']}/", None) for r in DATA["regions"]]
    for r, s, st in published_stops():
        c = load_condition(st["slug"])
        urls.append((SITE + stop_path(r, s, st), (c or {}).get("dateModified", st["published"])))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        lm = f"<lastmod>{mod}</lastmod>" if mod else ""
        lines.append(f"  <url><loc>{loc}</loc>{lm}</url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_llms():
    out = [f"# {SITE_NAME}", "",
           f"> {SITE_DESC} 작성·검수: 이비인후과 전문의 박종원.", "",
           "모든 질환 페이지는 증상, 바로 진료가 필요한 신호, 원인, 검사, 단계별 치료, 생활 관리, 자주 묻는 질문 순서로 구성되며 "
           "MedicalWebPage·MedicalCondition·FAQPage 구조화 데이터를 함께 제공합니다.", "",
           "## 부위별 안내", ""]
    for r in DATA["regions"]:
        n = sum(len(s["stops"]) for s in r["segments"])
        out.append(f"- [{r['name']}: {r['route']}]({SITE}/{r['id']}/): {r['intro']} 질환 {n}가지.")
    out += ["", "## 질환 페이지", ""]
    for r, s, st in published_stops():
        c = load_condition(st["slug"])
        desc = c["metaDescription"] if c else st["symptom"]
        out.append(f"- [{st['name']}]({SITE}{stop_path(r, s, st)}): {desc}")
    out += ["", "## 질환 30가지 쉬운 설명", ""]
    for r in DATA["regions"]:
        for s in r["segments"]:
            for st in s["stops"]:
                href, _, _ = stop_link(st["slug"])
                out.append(f"- [{st['name']}]({SITE}{href}) ({r['name']} · {s['name']}): {st.get('easy', st['symptom'])}")
    out += ["", f"## {FACTS['title']}", ""]
    for f in FACTS["items"]:
        out.append(f"- [{f['title']}]({SITE}/facts/#{f['id']}): {f['body']}")
    out += ["", "## 작성자", "", f"- [이비인후과 전문의 박종원]({SITE}/about/): 약력과 전문 분야", ""]
    (ROOT / "llms.txt").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    STOPS = stop_index()
    build_home()
    build_facts_page()
    for region in DATA["regions"]:
        build_hub(region)
    built = []
    for r, s, st in published_stops():
        c = load_condition(st["slug"])
        if c:
            build_condition(r, s, st, c)
            built.append(st["slug"])
    build_sitemap()
    build_llms()
    print("built: index, hubs", [r["id"] for r in DATA["regions"]], "conditions", built, "sitemap, llms.txt")
    sys.exit(subprocess.call([sys.executable, str(ROOT / "tools" / "check.py")]))
