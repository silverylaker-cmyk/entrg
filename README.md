# 귀코목 알지 (entrg.net)

이비인후과 질환 의학정보 사이트. 빌드 도구 없는 정적 HTML이며 GitHub Pages로 그대로 배포된다.

## 구조

| 경로 | 내용 |
|---|---|
| `/` | 대문: 검색 → 귀·코·목 그림 카드 → 오늘의 상식 → 증상으로 찾기 → 작성자 (섹션은 build.py가 생성) |
| `/ear/` `/nose/` `/throat/` | 부위별 허브 (자동 생성) |
| `/<부위>/<slug>/` | 질환 페이지 (MedicalWebPage + MedicalCondition + FAQPage JSON-LD) |
| `/care/` · `/care/<slug>/` | 검사·치료 허브와 검사·치료 페이지 (MedicalWebPage + MedicalTest/TherapeuticProcedure 계열 + FAQPage JSON-LD) |
| `/about/` | 원장 소개 (Person JSON-LD 전체본) |
| `data/diseases.json` | 질환 목록·순서·발행일, 단일 원본 |
| `data/conditions/<slug>.json` | 발행한 질환 한 편의 본문·구조화 데이터 원본 |
| `data/care.json` · `data/care/<slug>.json` | 검사·치료 묶음 순서와 한 편씩의 본문·구조화 데이터 원본 |
| `tools/build.py` | 대문 탐험로·JSON-LD, 허브 3개, 질환 페이지, sitemap.xml, llms.txt 생성 |
| `tools/check.py` | 구조화 데이터 점검 (build.py 마지막에 자동 실행) |
| `llms.txt` | AI 검색용 사이트 안내 (자동 생성) |
| `data/figures/*.svg` | 해부 그림 6장(귀 단면, 코 옆·정면, 목 옆, 후두 내시경 시야, 목 옆면). 부위는 `data-part`, 질환별 강조는 `tools/content/figures.py` |
| `data/figures/head-map.svg` | 이전 대문의 머리 지도. 공유 미리보기 카드(대문·상식·소개)에만 사용, 스타일은 `tools/og.css` |
| `assets/og/*.jpg` | 공유 미리보기 이미지 1200×630. `python3 tools/og.py`로 생성(Playwright 필요), 있으면 build.py가 og:image를 붙임 |
| `assets/home.js` · `assets/search.json` | 대문 검색(브라우저 안에서 질환·증상·상식 찾기), 예시 문구, 오늘의 상식. 색인은 build.py가 생성 |

## 새 질환 페이지 발행

질환 페이지는 손으로 쓰지 않는다. 질환마다 원본 데이터 파일 하나를 두고, 페이지 본문·JSON-LD·sitemap·llms.txt를 모두 거기서 만든다. 화면 본문과 구조화 데이터가 어긋나지 않게 하기 위해서다.

1. `data/conditions/chronic-sinusitis.json`을 복사해 `data/conditions/<slug>.json` 작성
   - `condition`: 구조화 데이터 (질병명, 다른 이름, ICD-10/ICD-11 코드, 해부 부위, 증상, 위험 요인, 검사, 치료, 합병증)
   - `body`: 본문 블록 (`p`, `h2`, `ul`, `alert`, `steps`). 문자열 안에 `<strong>` 정도의 HTML 허용
   - `faq`, `references`(DOI·PubMed 번호), `lastReviewed`, `dateModified`
2. `data/diseases.json` 해당 항목에 `"published": "YYYY-MM-DD"` 추가
3. 그림을 넣으려면 `tools/content/figures.py`에 강조 부위와 설명을 추가하고 실행
4. `python3 tools/og.py <slug>`로 미리보기 이미지 생성
5. `python3 tools/build.py` 실행. 마지막에 `tools/check.py`가 돌아 오류가 있으면 실패로 끝난다
6. 커밋

## 검사·치료 페이지와 질환 연결

이비인후과 의원에서 실제로 하는 검사와 치료를 `data/care/<slug>.json` 한 파일씩으로 둔다. 질환과 검사·치료가 JSON-LD의 `@id`로 서로 이어져 하나의 그래프가 된다.

- `kind`: `test`(검사) 또는 `treatment`(치료). `entity.type`은 schema.org 유형(`MedicalTest`, `BloodTest`, `PathologyTest`, `TherapeuticProcedure`, `MedicalTherapy`, `PhysicalTherapy`, `PsychologicalTreatment`)
- `conditions`: 이어지는 질환 slug. 검사는 여기 적은 질환이 `usedToDiagnose`로 나가므로 **실제로 진단에 쓰는 질환만** 적는다. 치료는 페이지의 `mentions`와 "관련 질환" 목록으로 나간다
- `status: "emerging"`: 아직 표준 치료가 아닌 것. 허브와 llms.txt에 표시되고, 본문 첫머리에 근거 수준 안내 상자(`alert`의 `kind: "note"`)를 둔다
- 질환 쪽에서는 `condition.tests` / `condition.treatments` 항목에 `"care": "<slug>"`를 적으면 `typicalTest` / `possibleTreatment`가 검사·치료 페이지의 `@id`로 이어진다. 여러 검사를 묶어 부른 이름(예: 알레르기 검사)은 목록으로 적는다
- 질환 페이지 아래 "관련 검사와 치료" 목록은 질환 쪽 `care` 값과 검사·치료 쪽 `conditions`를 합쳐 만든다
- 새 검사·치료 추가: `data/care/<slug>.json` 작성 → `data/care.json`의 묶음에 slug 추가 → 필요하면 `tools/content/link_care.py`의 이름 표에 추가해 실행 → `python3 tools/og.py care-<slug>` → `python3 tools/build.py`

`tools/check.py`가 확인하는 것: JSON 문법, `@id` 참조가 모두 정의돼 있는지, 내부 주소에 실제 파일이 있는지, 날짜 형식(자리표시자 금지), MedicalWebPage 필수 항목, FAQ 질문·답이 화면 본문과 글자 그대로 같은지, canonical과 JSON-LD url 일치, sitemap과 실제 페이지 일치, 검사·치료 노드의 필수 항목(검사는 `usedToDiagnose`, 치료는 `howPerformed`), 같은 `@id`가 페이지마다 같은 유형·이름으로 적혔는지.

발행 전 검수 항목은 30편 기획 문서의 작성 규칙을 따른다.
