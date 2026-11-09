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
| `tools/build.py` | 대문 탐험로, 허브 3개, sitemap.xml 재생성 |

## 새 질환 페이지 발행

1. `nose/chronic-sinusitis/index.html`을 복사해 `/<부위>/<slug>/index.html` 작성 (수면 3편은 `/sleep/<slug>/`)
2. `data/diseases.json` 해당 항목에 `"published": "YYYY-MM-DD"` 추가
3. `python3 tools/build.py` 실행 후 커밋

발행 전 검수 항목은 30편 기획 문서의 작성 규칙을 따른다.
