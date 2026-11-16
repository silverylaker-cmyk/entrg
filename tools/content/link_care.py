"""질환의 검사·치료 항목을 검사·치료 페이지(data/care/<slug>.json)와 잇는다.

data/conditions/*.json 의 condition.tests / condition.treatments 항목 이름을 아래 표에서 찾아
"care" 값을 적어 넣는다. build.py 는 이 값으로 JSON-LD 의 typicalTest / possibleTreatment 를
검사·치료 페이지의 @id 와 연결하고, 질환 페이지 아래에 "관련 검사와 치료" 목록을 만든다.
  - 문자열: 그 항목이 곧 그 검사·치료 (JSON-LD @id 로 연결)
  - 목록: 여러 검사·치료를 묶어 부른 이름 (목록에만 표시, JSON-LD 는 이름만)
다시 실행해도 결과가 같다. 표에 없는 이름은 건드리지 않는다.

사용: python3 tools/content/link_care.py && python3 tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COND = ROOT / "data" / "conditions"
CARE = {f.stem for f in (ROOT / "data" / "care").glob("*.json")}

TESTS = {
    "비내시경 검사": "nasal-endoscopy",
    "피부단자검사": "skin-prick-test",
    "혈액 특이 IgE 검사": "specific-ige-test",
    "알레르기 검사": ["skin-prick-test", "specific-ige-test"],
    "후각검사": "smell-test",
    "비강 분비물 도말 검사": "nasal-cytology",
    "비강통기도 검사": "nasal-airflow-test",
    "수면다원검사": "polysomnography",
    "비디오 안진 검사": "videonystagmography",
    "안진 검사": "videonystagmography",
    "체위 안진 검사(딕스-홀파이크 검사)": "videonystagmography",
    "청력검사": "hearing-test",
    "순음청력검사": "hearing-test",
    "어음청력검사": "hearing-test",
    "고막운동성 검사": "hearing-test",
}
TREATMENTS = {
    "내시경 부비동 수술(ESS)": "endoscopic-sinus-surgery",
    "비중격 성형술": "septoplasty",
    "하비갑개 축소술": "turbinate-reduction",
    "면역치료": "allergen-immunotherapy",
    "식염수 코 세척": "nasal-irrigation",
    "후각 훈련": "olfactory-training",
    "이석 치환술": "canalith-repositioning",
    "전정재활운동": "vestibular-rehabilitation",
    "인지행동치료": "tinnitus-cbt",
    "양압기": "cpap",
    "양압기(CPAP)": "cpap",
    "고막 안 스테로이드 주사": "intratympanic-steroid-injection",
    "보청기": "hearing-aid",
    "고막 패치술": "eardrum-patch",
    "이관 풍선확장술": "eustachian-tube-balloon-dilation",
}
# 같은 이름이라도 질환에 따라 다른 치료를 뜻하는 경우는 잇지 않는다
SKIP = {("stuttering", "인지행동치료")}


def main():
    used = set()
    for table in (TESTS, TREATMENTS):
        for v in table.values():
            used |= set([v] if isinstance(v, str) else v)
    missing = used - CARE
    if missing:
        raise SystemExit(f"data/care 에 없는 항목: {sorted(missing)}")
    n = 0
    for f in sorted(COND.glob("*.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        for key, table in (("tests", TESTS), ("treatments", TREATMENTS)):
            for item in c["condition"][key]:
                if (c["slug"], item["name"]) in SKIP:
                    item.pop("care", None)
                elif item["name"] in table:
                    item["care"] = table[item["name"]]
                    n += 1
        f.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("linked items:", n)


if __name__ == "__main__":
    main()
