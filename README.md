# 귀코목 알지 (entrg.net)

이비인후과 질환 의학정보 사이트. 빌드 도구 없는 정적 HTML이며 GitHub Pages로 그대로 배포된다.

## 구조

| 경로 | 내용 |
|---|---|
| `/` | 대문: 귀코목 탐험 지도 애니메이션 + 30개 질환 탐험로 |
| `/ear/` `/nose/` `/throat/` | 부위별 허브 (자동 생성) |
| `/nose/chronic-sinusitis/` | 질환 페이지 1편 (MedicalWebPage + MedicalCondition + FAQPage JSON-LD) |
| `/about/` | 원장 소개 (Person JSON-LD 전체본) |
| `data/diseases.json` | 30개 질환 목록·순서·발행일, 단일 원본 |
| `data/conditions/<slug>.json` | 발행한 질환 한 편의 본문·구조화 데이터 원본 |
| `tools/build.py` | 대문 탐험로·JSON-LD, 허브 3개, 질환 페이지, sitemap.xml, llms.txt 생성 |
| `tools/check.py` | 구조화 데이터 점검 (build.py 마지막에 자동 실행) |
| `llms.txt` | AI 검색용 사이트 안내 (자동 생성) |
| `assets/hero3d.js` · `hero3d-scene.js` | 대문 3D 지도(three.js). 모양은 index.html의 SVG 지도에서 읽음. WebGL 불가·동작 줄이기·데이터 절약 시 SVG 지도(`hero.js`)가 대신 표시 |

## 새 질환 페이지 발행

질환 페이지는 손으로 쓰지 않는다. 질환마다 원본 데이터 파일 하나를 두고, 페이지 본문·JSON-LD·sitemap·llms.txt를 모두 거기서 만든다. 화면 본문과 구조화 데이터가 어긋나지 않게 하기 위해서다.

1. `data/conditions/chronic-sinusitis.json`을 복사해 `data/conditions/<slug>.json` 작성
   - `condition`: 구조화 데이터 (질병명, 다른 이름, ICD-10/ICD-11 코드, 해부 부위, 증상, 위험 요인, 검사, 치료, 합병증)
   - `body`: 본문 블록 (`p`, `h2`, `ul`, `alert`, `steps`). 문자열 안에 `<strong>` 정도의 HTML 허용
   - `faq`, `references`(DOI·PubMed 번호), `lastReviewed`, `dateModified`
2. `data/diseases.json` 해당 항목에 `"published": "YYYY-MM-DD"` 추가
3. `python3 tools/build.py` 실행. 마지막에 `tools/check.py`가 돌아 오류가 있으면 실패로 끝난다
4. 커밋

`tools/check.py`가 확인하는 것: JSON 문법, `@id` 참조가 모두 정의돼 있는지, 내부 주소에 실제 파일이 있는지, 날짜 형식(자리표시자 금지), MedicalWebPage 필수 항목, FAQ 질문·답이 화면 본문과 글자 그대로 같은지, canonical과 JSON-LD url 일치, sitemap과 실제 페이지 일치.

발행 전 검수 항목은 30편 기획 문서의 작성 규칙을 따른다.
