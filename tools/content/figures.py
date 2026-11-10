"""질환별 해부 그림 배치.

각 질환에 (그림, 강조 부위, 설명)을 지정해 data/conditions/<slug>.json 본문에 넣는다.
  - "anat": 정의 다음에 들어가는 위치 그림
  - "exam": "검사" 제목 바로 다음 목록 뒤에 들어가는 검사 그림
그림 원본은 data/figures/<그림>.svg, 부위 이름은 SVG의 data-part 값.
다시 실행하면 기존 그림 블록을 지우고 새로 넣는다.

사용: python3 tools/content/figures.py && python3 tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COND = ROOT / "data" / "conditions"

OTO = "scope-ear"
NE = "scope-nose"
LE = "scope-throat"

FIG = {
  "otitis-externa": {
    "anat": ("ear", ["canal"], "<strong>외이도염이 생기는 곳.</strong> 귀 입구에서 고막까지 이어지는 통로(외이도)의 피부입니다."),
    "exam": ("ear", ["canal", "drum", OTO], "<strong>이경 검사.</strong> 귀 입구에 이경을 대고 빛을 비춰 외이도의 부기와 분비물, 고막 상태를 봅니다.")},
  "acute-otitis-media": {
    "anat": ("ear", ["middle", "fluid", "drum", "tube"], "<strong>급성 중이염이 생기는 곳.</strong> 고막 안쪽 공간(중이)에 고름이 차고 고막이 바깥으로 부풀어 오릅니다. 중이는 이관으로 코 뒤쪽과 이어져 있어, 감기 때 세균이 이 길로 올라갑니다."),
    "exam": ("ear", ["drum", "middle", "fluid", OTO], "<strong>이경 검사.</strong> 빨갛게 붓고 바깥으로 볼록해진 고막을 확인합니다.")},
  "otitis-media-effusion": {
    "anat": ("ear", ["middle", "fluid", "tube"], "<strong>고막 안쪽에 물이 고인 모습.</strong> 귀와 코를 잇는 이관이 제대로 열리지 않으면 중이의 물이 빠지지 못합니다."),
    "exam": ("ear", ["drum", "middle", "fluid", OTO], "<strong>이경 검사.</strong> 고막 너머로 비치는 물과 공기 방울을 보고, 고막운동성 검사로 확인합니다.")},
  "chronic-otitis-media": {
    "anat": ("ear", ["drum", "perf", "middle"], "<strong>고막에 구멍이 남은 모습.</strong> 구멍으로 물과 세균이 드나들며 중이 염증이 반복되고, 고름이 흘러나옵니다."),
    "exam": ("ear", ["canal", "drum", "perf", OTO], "<strong>귀 내시경 검사.</strong> 고막 구멍의 크기와 위치, 진주종이 있는지 봅니다.")},
  "sudden-hearing-loss": {
    "anat": ("ear", ["cochlea", "nerve-coch"], "<strong>소리를 느끼는 달팽이관과 청신경.</strong> 돌발성 난청은 이 부분의 갑작스러운 손상으로 생기며, 외이도와 고막, 중이는 정상입니다.")},
  "tinnitus": {
    "anat": ("ear", ["cochlea", "nerve-coch"], "<strong>이명이 시작되는 곳.</strong> 대개 달팽이관과 청신경입니다. 이곳에서 들어오는 소리 신호가 줄면 뇌가 신호를 키우면서 소리가 들린다고 설명합니다.")},
  "bppv": {
    "anat": ("ear", ["canals", "vestibule", "otoconia"], "<strong>이석이 굴러 들어간 모습.</strong> 이석은 원래 전정 안에 있습니다. 떨어져 나온 이석이 회전을 느끼는 반고리관으로 들어가면 고개를 움직일 때마다 어지럼이 생깁니다.")},
  "vestibular-neuritis": {
    "anat": ("ear", ["nerve-vest", "vestibule", "canals"], "<strong>염증이 생기는 전정신경.</strong> 균형 정보를 뇌로 보내는 신경입니다. 소리를 전하는 청신경은 대개 괜찮아 청력은 그대로입니다.")},
  "menieres-disease": {
    "anat": ("ear", ["cochlea", "vestibule", "canals"], "<strong>메니에르병이 생기는 속귀.</strong> 달팽이관과 전정, 반고리관에 차 있는 림프액의 압력이 높아져 청력과 균형 증상이 함께 옵니다.")},

  "nosebleed": {
    "anat": ("nose-side", ["kiss"], "<strong>코피가 잘 나는 곳.</strong> 대부분 콧구멍 바로 안쪽, 코 가운데 칸막이(비중격) 앞부분의 혈관이 모인 곳입니다. 그래서 콧방울을 꽉 누르면 멈춥니다.")},
  "deviated-septum": {
    "anat": ("nose-front", ["deviation"], "<strong>코를 정면에서 자른 모습.</strong> 코 가운데 칸막이(비중격)가 한쪽으로 휘어 한쪽 숨길이 좁아졌습니다.")},
  "turbinate-hypertrophy": {
    "anat": ("nose-front", ["it-big"], "<strong>코를 정면에서 자른 모습.</strong> 코 옆벽의 하비갑개가 부어 커지면 양쪽 숨길이 좁아집니다."),
    "exam": ("nose-side", ["it", NE], "<strong>비내시경 검사.</strong> 혈관수축제를 뿌리기 전과 후에 하비갑개가 얼마나 줄어드는지 봅니다.")},
  "allergic-rhinitis": {
    "anat": ("nose-side", ["it", "mt", "st"], "<strong>코 안 점막과 비갑개.</strong> 알레르기 비염에서는 이 점막이 붓고 맑은 콧물이 많아져 코가 막히고 재채기가 납니다.")},
  "nonallergic-rhinitis": {
    "anat": ("nose-side", ["it", "mt", "st"], "<strong>코 안 점막과 비갑개.</strong> 비알레르기성 비염도 같은 곳에서 일어나지만, 원인이 알레르기가 아니라 온도, 냄새 같은 자극입니다.")},
  "rhinitis-medicamentosa": {
    "anat": ("nose-side", ["it"], "<strong>코 스프레이가 작용하는 하비갑개.</strong> 충혈제거제는 이곳의 혈관을 수축시켜 코를 뚫지만, 오래 쓰면 반동으로 더 크게 붓습니다.")},
  "nasal-polyps": {
    "anat": ("nose-front", ["polyps", "ethmoid"], "<strong>비용종이 잘 생기는 곳.</strong> 눈 사이의 사골동과 그 출구 주변에서 생겨 숨길과 냄새의 길을 막습니다."),
    "exam": ("nose-side", ["mt", NE], "<strong>비내시경 검사.</strong> 가는 내시경을 콧구멍으로 넣어 비갑개 사이의 물혹을 직접 봅니다.")},
  "smell-loss": {
    "anat": ("nose-side", ["olf"], "<strong>냄새를 맡는 후각 점막.</strong> 코 천장의 좁은 부위에 있습니다. 코가 붓거나 물혹이 있으면 냄새 분자가 이곳까지 올라가지 못합니다.")},
  "acute-sinusitis": {
    "anat": ("nose-front", ["maxillary", "ethmoid", "fluid-l", "fluid-r"], "<strong>코를 정면에서 자른 모습.</strong> 광대뼈 속의 상악동과 눈 사이의 사골동에 염증과 분비물이 고입니다.")},
  "chronic-sinusitis": {
    "anat": ("nose-front", ["maxillary", "ethmoid", "fluid-l", "fluid-r"], "<strong>염증이 흔히 생기는 상악동과 사골동.</strong> 부비동은 좁은 통로로 코와 이어져 있어, 통로가 막히면 분비물이 고이고 염증이 오래갑니다."),
    "exam": ("nose-side", ["mt", NE], "<strong>비내시경 검사.</strong> 부비동 출구 주변의 부기, 고름, 물혹을 직접 봅니다.")},
  "odontogenic-sinusitis": {
    "anat": ("nose-front", ["tooth-r", "fluid-r"], "<strong>위 어금니와 상악동.</strong> 위 어금니의 뿌리는 상악동 바닥과 아주 가깝습니다. 치아의 염증이 얇은 뼈를 넘어 한쪽 상악동으로 번집니다.")},
  "postnasal-drip": {
    "anat": ("nose-side", ["np", "drip"], "<strong>분비물이 넘어가는 길.</strong> 코와 부비동에서 만든 분비물은 코 뒤쪽(비인두)을 지나 목으로 넘어갑니다. 양이 많거나 끈적해지면 이 흐름이 느껴집니다."),
    "exam": ("nose-side", ["np", "drip", NE], "<strong>비내시경 검사.</strong> 코 뒤쪽으로 흘러내리는 분비물과 그 출발점을 확인합니다.")},

  "tonsil-stones": {
    "anat": ("throat-side", ["tonsil", "stones"], "<strong>목을 옆에서 본 모습.</strong> 편도 표면의 작은 구멍에 찌꺼기가 뭉쳐 결석이 됩니다. 편도는 양쪽에 있지만 그림에는 한쪽만 보입니다.")},
  "tonsillitis": {
    "anat": ("throat-side", ["tonsil"], "<strong>목을 옆에서 본 모습.</strong> 급성 편도염은 목 양쪽의 편도에 생기는 감염입니다. 그림에는 한쪽만 보입니다.")},
  "snoring": {
    "anat": ("throat-side", ["palate-soft", "tongue-base", "airway", "collapse"], "<strong>코골이가 나는 곳.</strong> 잠이 들면 입천장 뒤쪽과 혀뿌리 쪽 숨길이 좁아지고, 그 사이로 공기가 빠르게 지나며 입천장과 목젖이 떨립니다.")},
  "sleep-apnea": {
    "anat": ("throat-side", ["palate-soft", "tongue-base", "airway", "collapse"], "<strong>잘 때 막히는 숨길.</strong> 수면무호흡에서는 입천장 뒤쪽이나 혀뿌리 쪽 숨길이 반복해서 막힙니다. 막히는 위치는 사람마다 달라 검사로 확인합니다.")},
  "pediatric-sleep-apnea": {
    "anat": ("throat-side", ["tonsil-big", "adenoid-big", "airway"], "<strong>아이의 숨길을 막는 편도와 아데노이드.</strong> 아이에게는 커진 편도와 코 뒤쪽의 아데노이드가 수면무호흡의 가장 흔한 원인입니다.")},
  "laryngopharyngeal-reflux": {
    "anat": ("throat-side", ["reflux", "larynx", "esophagus"], "<strong>목까지 올라오는 역류.</strong> 위산이 식도를 넘어 후두까지 올라오면, 식도보다 약한 후두 점막이 쉽게 자극을 받습니다."),
    "exam": ("throat-side", ["larynx", LE], "<strong>후두 내시경 검사.</strong> 가는 내시경을 코로 넣어 후두와 성대를 직접 봅니다.")},
  "globus": {
    "anat": ("throat-side", ["globus"], "<strong>이물감이 느껴지는 곳.</strong> 대개 목 앞쪽, 후두와 식도 입구 높이에서 느껴집니다."),
    "exam": ("throat-side", ["larynx", "epiglottis", LE], "<strong>후두 내시경 검사.</strong> 실제로 막히거나 혹이 있는 곳이 없는지 확인합니다.")},
  "vocal-nodules": {
    "anat": ("larynx-top", ["vf", "nodules"], "<strong>후두 내시경으로 위에서 본 성대.</strong> 결절은 양쪽 성대의 같은 자리에 생긴 작은 굳은살입니다."),
    "exam": ("larynx-top", ["vf", "polyp"], "<strong>성대 폴립.</strong> 대개 한쪽 성대에 생긴 물혹입니다. 내시경과 스트로보스코피로 크기와 진동을 확인합니다.")},
  "neck-lump": {
    "anat": ("neck", ["nodes", "salivary", "thyroid"], "<strong>목 멍울의 흔한 출발점.</strong> 림프절, 침샘(귀밑샘·턱밑샘), 갑상선입니다. 혹의 위치를 보면 원인을 짐작하는 데 도움이 됩니다.")},
}


def block(spec, kind):
    fig, hl, cap = spec
    return {"figure": {"fig": fig, "hl": hl, "caption": cap, "kind": kind}}


def main():
    for slug, figs in FIG.items():
        f = COND / f"{slug}.json"
        c = json.loads(f.read_text(encoding="utf-8"))
        body = [b for b in c["body"] if "figure" not in b]
        if "anat" in figs:
            # 정의 문단과 그 다음 설명 문단 뒤
            pos = 2 if len(body) > 2 and "p" in body[1] else 1
            body.insert(pos, block(figs["anat"], "anat"))
        if "exam" in figs:
            idx = next((i for i, b in enumerate(body) if b.get("h2") == "검사"), None)
            if idx is None:
                body.append(block(figs["exam"], "exam"))
            else:
                body.insert(idx + 2, block(figs["exam"], "exam"))
        c["body"] = body
        f.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("figures placed:", len(FIG))


if __name__ == "__main__":
    main()
