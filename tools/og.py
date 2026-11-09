#!/usr/bin/env python3
"""공유 미리보기 이미지(og:image) 생성.

페이지마다 1200x630 JPG를 assets/og/<key>.jpg 로 만든다.
  - 질환 페이지: 질환 이름, 쉬운 설명, 해당 부위를 강조한 해부 그림
  - 허브: 부위 이름, 탐험로 설명, 부위 그림
  - 대문·상식·소개: 대문의 머리 지도

이미지가 있으면 build.py가 og:image 메타와 JSON-LD primaryImageOfPage를 자동으로 붙인다.
질환을 추가하거나 제목·설명·그림을 바꾼 뒤 실행한다.

필요: pip install playwright && playwright install chromium (또는 CHROME=/경로/크롬)
사용: python3 tools/og.py [key ...]   # key 생략 시 전부
      python3 tools/build.py
"""
import asyncio
import json
import os
import re
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

OUT = ROOT / "assets" / "og"
HUB_FIG = {
    "ear": {"fig": "ear", "hl": ["canal", "middle", "cochlea", "canals"]},
    "nose": {"fig": "nose-side", "hl": ["it", "mt", "st", "olf"]},
    "throat": {"fig": "throat-side", "hl": ["tonsil", "palate-soft", "larynx"]},
}

CSS = """
html, body { margin: 0; }
.og { width: 1200px; height: 630px; box-sizing: border-box; display: grid;
      grid-template-columns: 600px 1fr; gap: 24px; align-items: center;
      padding: 52px 48px 44px 72px; background: var(--paper); color: var(--ink);
      font-family: "Pretendard Variable", Pretendard, sans-serif; overflow: hidden; }
.og-text { display: flex; flex-direction: column; height: 100%; }
.og-brand { display: flex; align-items: center; gap: 12px; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }
.og-brand .dots { display: inline-flex; gap: 5px; }
.og-brand .dots i { width: 12px; height: 12px; border-radius: 50%; display: block; }
.og-brand .dots i:nth-child(1) { background: var(--ear-glow); }
.og-brand .dots i:nth-child(2) { background: var(--nose-glow); }
.og-brand .dots i:nth-child(3) { background: var(--throat-glow); }
.og-main { margin: auto 0; }
.og-kicker { margin: 0 0 16px; font-size: 26px; font-weight: 700; color: var(--c, var(--ink-soft)); }
.og h1 { margin: 0; font-weight: 900; letter-spacing: -0.045em; line-height: 1.12; text-wrap: balance; }
.og-sub { margin: 22px 0 0; font-size: 27px; line-height: 1.5; color: var(--ink-soft); word-break: keep-all;
          display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.og-foot { margin: 0; font-size: 21px; color: var(--ink-soft); }
.og-fig { display: flex; align-items: center; justify-content: center; height: 100%; }
.og-fig .anat { margin: 0; width: 100%; max-width: none; }
.og-fig .anat figcaption { display: none; }
.og-fig .anat .lbl { font-size: 17px; }
.og-fig .anat .lbl.sm { font-size: 14px; }
.og-fig .map svg { width: 470px; height: auto; display: block; }
"""


def pages():
    """(key, region, kicker, title, sub, figure_html)"""
    m = re.search(r'<div class="map" id="map">\s*(<svg.*?</svg>)', (ROOT / "index.html").read_text(encoding="utf-8"), re.S)
    map_svg = f'<div class="map">{m.group(1)}</div>'
    lede = "소리가 들어오는 길, 숨이 지나는 길, 목소리가 나오는 길. 이비인후과 전문의가 그 길 위에서 생기는 질환을 하나씩 짚어 드립니다."
    yield "home", None, "이비인후과 의학정보", "귀, 코, 목<br>안쪽으로 떠나는 탐험", lede, map_svg
    yield "facts", None, "상식", escape(build.FACTS["title"]), build.FACTS["intro"], map_svg
    yield "about", None, "이 지도를 그린 사람", "이비인후과 전문의<br>박종원", \
        "계명대학교 동산병원 이비인후과 전공의 수료, 삼성서울병원 이비인후과 임상강사, 전 계명대학교 의과대학 이비인후과학교실 조교수", map_svg
    for r in build.DATA["regions"]:
        f = HUB_FIG[r["id"]]
        yield r["id"], r["id"], f"{r['name']} 탐험로", escape(r["route"]), r["intro"], \
            build.render_figure({**f, "caption": r["route"]}, "")
        for s in r["segments"]:
            for st in s["stops"]:
                c = build.load_condition(st["slug"])
                if not c or not st.get("published"):
                    continue
                fig = next((b["figure"] for b in c["body"] if "figure" in b and b["figure"].get("kind") == "anat"), None)
                fig_html = build.render_figure(fig, "") if fig else map_svg
                yield st["slug"], r["id"], f"{r['name']} · {s['name']}", escape(c["title"]), st.get("easy", c["condition"]["description"]), fig_html


def title_size(title):
    n = len(re.sub(r"<br>|<[^>]+>", "", title))
    return 76 if n <= 8 else 64 if n <= 14 else 54


def html_for(key, region, kicker, title, sub, fig):
    css_href = (ROOT / "assets" / "site.css").as_uri()
    cls = f"og on-stage c-{region}" if region else "og on-stage"
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{css_href}"><style>{CSS}</style></head><body>
<div class="{cls}">
  <div class="og-text">
    <p class="og-brand"><span class="dots"><i></i><i></i><i></i></span>귀코목 알지</p>
    <div class="og-main">
      <p class="og-kicker">{escape(kicker)}</p>
      <h1 style="font-size:{title_size(title)}px">{title}</h1>
      <p class="og-sub">{escape(sub)}</p>
    </div>
    <p class="og-foot">이비인후과 전문의가 쓰고 검수한 의학정보 · entrg.net</p>
  </div>
  <div class="og-fig">{fig}</div>
</div></body></html>"""


async def main(only):
    from playwright.async_api import async_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    exe = os.environ.get("CHROME") or ("/usr/bin/google-chrome" if Path("/usr/bin/google-chrome").exists() else None)
    made = []
    with tempfile.TemporaryDirectory() as td:
        async with async_playwright() as p:
            b = await p.chromium.launch(**({"executable_path": exe} if exe else {}))
            pg = await b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
            for key, region, kicker, title, sub, fig in pages():
                if only and key not in only:
                    continue
                f = Path(td) / f"{key}.html"
                f.write_text(html_for(key, region, kicker, title, sub, fig), encoding="utf-8")
                await pg.goto(f.as_uri())
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(150)
                await pg.screenshot(path=str(OUT / f"{key}.jpg"), type="jpeg", quality=86)
                made.append(key)
            await b.close()
    print(f"og images: {len(made)}개 → assets/og/")


if __name__ == "__main__":
    asyncio.run(main(set(sys.argv[1:])))
