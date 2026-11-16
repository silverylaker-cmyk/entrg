"""질환(data/conditions/<slug>.json)과 검사·치료(data/care/<slug>.json) 원본 데이터를 짧게 쓰기 위한 도우미.

tools/content/<부위>.py 에서 페이지를 dict로 정의하고 write_all()로 저장한다.
한 번 만든 뒤에는 data/conditions/*.json 을 직접 고쳐도 된다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "conditions"
CARE_OUT = ROOT / "data" / "care"
DATE = "2026-11-09"

# 참고문헌 (PubMed 확인)
REF = {
    "aoe": ("미국이비인후과학회 급성 외이도염 진료지침 (2014)", "Clinical practice guideline: acute otitis externa",
            "Rosenfeld RM, et al. Otolaryngol Head Neck Surg. 2014;150(1 Suppl):S1-S24.", "10.1177/0194599813517083", "24491310", 2014),
    "aom": ("미국소아과학회 급성 중이염 진료지침 (2013)", "The diagnosis and management of acute otitis media",
            "Lieberthal AS, et al. Pediatrics. 2013;131(3):e964-e999.", "10.1542/peds.2012-3488", "23439909", 2013),
    "ome": ("미국이비인후과학회 삼출성 중이염 진료지침 (2016)", "Clinical Practice Guideline: Otitis Media with Effusion (Update)",
            "Rosenfeld RM, et al. Otolaryngol Head Neck Surg. 2016;154(1 Suppl):S1-S41.", "10.1177/0194599815623467", "26832942", 2016),
    "csom": ("Chronic suppurative otitis media (Lancet, 2024)", "Chronic suppurative otitis media",
             "Bhutta MF, et al. Lancet. 2024;403(10441):2339-2348.", "10.1016/S0140-6736(24)00259-9", "38621397", 2024),
    "ssnhl": ("미국이비인후과학회 돌발성 난청 진료지침 (2019)", "Clinical Practice Guideline: Sudden Hearing Loss (Update)",
              "Chandrasekhar SS, et al. Otolaryngol Head Neck Surg. 2019;161(1 Suppl):S1-S45.", "10.1177/0194599819859885", "31369359", 2019),
    "tinnitus": ("미국이비인후과학회 이명 진료지침 (2014)", "Clinical practice guideline: tinnitus",
                 "Tunkel DE, et al. Otolaryngol Head Neck Surg. 2014;151(2 Suppl):S1-S40.", "10.1177/0194599814545325", "25273878", 2014),
    "bppv": ("미국이비인후과학회 양성 돌발성 체위성 현훈 진료지침 (2017)", "Clinical Practice Guideline: Benign Paroxysmal Positional Vertigo (Update)",
             "Bhattacharyya N, et al. Otolaryngol Head Neck Surg. 2017;156(3 Suppl):S1-S47.", "10.1177/0194599816689667", "28248609", 2017),
    "vn": ("Vestibular neuritis (N Engl J Med, 2003)", "Clinical practice. Vestibular neuritis",
           "Baloh RW. N Engl J Med. 2003;348(11):1027-1032.", "10.1056/NEJMcp021154", "12637613", 2003),
    "meniere": ("미국이비인후과학회 메니에르병 진료지침 (2020)", "Clinical Practice Guideline: Ménière's Disease",
                "Basura GJ, et al. Otolaryngol Head Neck Surg. 2020;162(2 Suppl):S1-S55.", "10.1177/0194599820909438", "32267799", 2020),
    "epistaxis": ("미국이비인후과학회 코피 진료지침 (2020)", "Clinical Practice Guideline: Nosebleed (Epistaxis)",
                  "Tunkel DE, et al. Otolaryngol Head Neck Surg. 2020;162(1 Suppl):S1-S38.", "10.1177/0194599819890327", "31910111", 2020),
    "septo": ("미국이비인후과학회 비중격 성형술·하비갑개 축소술 합의문 (2015)", "Clinical Consensus Statement: Septoplasty with or without Inferior Turbinate Reduction",
              "Han JK, et al. Otolaryngol Head Neck Surg. 2015;153(5):708-720.", "10.1177/0194599815606435", "26527752", 2015),
    "ar": ("미국이비인후과학회 알레르기 비염 진료지침 (2015)", "Clinical practice guideline: Allergic rhinitis",
           "Seidman MD, et al. Otolaryngol Head Neck Surg. 2015;152(1 Suppl):S1-S43.", "10.1177/0194599814561600", "25644617", 2015),
    "rhinitis2020": ("미국 알레르기 학회 비염 진료 지침 (Rhinitis 2020)", "Rhinitis 2020: A practice parameter update",
                     "Dykewicz MS, et al. J Allergy Clin Immunol. 2020;146(4):721-767.", "10.1016/j.jaci.2020.07.007", "32707227", 2020),
    "epos": ("European Position Paper on Rhinosinusitis and Nasal Polyps 2020 (EPOS 2020)", "European Position Paper on Rhinosinusitis and Nasal Polyps 2020",
             "Fokkens WJ, et al. Rhinology. 2020;58(Suppl S29):1-464.", "10.4193/Rhin20.600", "32077450", 2020),
    "olf": ("후각 장애 국제 입장문 (Position paper on olfactory dysfunction, 2023)", "Position paper on olfactory dysfunction: 2023",
            "Whitcroft KL, et al. Rhinology. 2023;61(33):1-108.", "10.4193/Rhin22.483", "37454287", 2023),
    "abrs": ("미국이비인후과학회 성인 부비동염 진료지침 (2015)", "Clinical practice guideline (update): adult sinusitis",
             "Rosenfeld RM, et al. Otolaryngol Head Neck Surg. 2015;152(2 Suppl):S1-S39.", "10.1177/0194599815572097", "25832968", 2015),
    "ods": ("치성 부비동염 진단 국제 합의문 (2021)", "Diagnosing odontogenic sinusitis: An international multidisciplinary consensus statement",
            "Craig JR, et al. Int Forum Allergy Rhinol. 2021;11(8):1235-1248.", "10.1002/alr.22777", "33583151", 2021),
    "uacs": ("미국흉부학회 상기도 기침 증후군 지침 (2006)", "Chronic upper airway cough syndrome secondary to rhinosinus diseases (previously referred to as postnasal drip syndrome)",
             "Pratter MR. Chest. 2006;129(1 Suppl):63S-71S.", "10.1378/chest.129.1_suppl.63S", "16428694", 2006),
    "tonsillolith": ("Changes in tonsillolith characteristics detected in a follow-up CT study (2021)", "Changes in tonsillolith characteristics detected in a follow-up CT study",
                     "Yamashita K, et al. BMC Oral Health. 2021;21(1):72.", "10.1186/s12903-021-01426-1", "33593358", 2021),
    "tonsillectomy": ("미국이비인후과학회 소아 편도 절제술 진료지침 (2019)", "Clinical Practice Guideline: Tonsillectomy in Children (Update)",
                      "Mitchell RB, et al. Otolaryngol Head Neck Surg. 2019;160(1 Suppl):S1-S42.", "10.1177/0194599818801757", "30798778", 2019),
    "gas": ("미국감염학회 A군 연쇄상구균 인두염 진료지침 (2012)", "Clinical practice guideline for the diagnosis and management of group A streptococcal pharyngitis: 2012 update",
            "Shulman ST, et al. Clin Infect Dis. 2012;55(10):e86-e102.", "10.1093/cid/cis629", "22965026", 2012),
    "osa": ("미국수면의학회 성인 폐쇄성 수면무호흡 진단 지침 (2017)", "Clinical Practice Guideline for Diagnostic Testing for Adult Obstructive Sleep Apnea",
            "Kapur VK, et al. J Clin Sleep Med. 2017;13(3):479-504.", "10.5664/jcsm.6506", "28162150", 2017),
    "posa": ("미국소아과학회 소아 폐쇄성 수면무호흡 진료지침 (2012)", "Diagnosis and management of childhood obstructive sleep apnea syndrome",
             "Marcus CL, et al. Pediatrics. 2012;130(3):576-584.", "10.1542/peds.2012-1671", "22926173", 2012),
    "lpr": ("인후두 역류 샌디에이고 합의문 (2025)", "The San Diego Consensus for Laryngopharyngeal Symptoms and Laryngopharyngeal Reflux Disease",
            "Yadlapati R, et al. Am J Gastroenterol. 2025;121(2):322-336.", "10.14309/ajg.0000000000003482", "40197644", 2025),
    "globus": ("로마 IV 기능성 식도 질환 (2016)", "Functional Esophageal Disorders",
               "Aziz Q, et al. Gastroenterology. 2016;150(6):1368-1379.", "10.1053/j.gastro.2016.02.012", "27144625", 2016),
    "dysphonia": ("미국이비인후과학회 쉰 목소리 진료지침 (2018)", "Clinical Practice Guideline: Hoarseness (Dysphonia) (Update)",
                  "Stachler RJ, et al. Otolaryngol Head Neck Surg. 2018;158(1 Suppl):S1-S42.", "10.1177/0194599817751030", "29494321", 2018),
    "neckmass": ("미국이비인후과학회 성인 목 멍울 평가 진료지침 (2017)", "Clinical Practice Guideline: Evaluation of the Neck Mass in Adults Executive Summary",
                 "Pynnonen MA, et al. Otolaryngol Head Neck Surg. 2017;157(3):355-371.", "10.1177/0194599817723609", "28891424", 2017),
    # 검사·치료 페이지와 추가 질환 (PubMed 확인 2026-11-16)
    "spt": ("피부단자검사 유럽 표준 (2013)", "The skin prick test - European standards",
            "Heinzerling L, et al. Clin Transl Allergy. 2013;3(1):3.", "10.1186/2045-7022-3-3", "23369181", 2013),
    "ige": ("세계알레르기기구 IgE 알레르기 진단 입장문 (2020)", "IgE allergy diagnostics and other relevant tests in allergy, a World Allergy Organization position paper",
            "Ansotegui IJ, et al. World Allergy Organ J. 2020;13(2):100080.", "10.1016/j.waojou.2019.100080", "32128023", 2020),
    "cytology": ("비강 세포검사 방법론 (2018)", "Nasal cytology: Methodology with application to clinical practice and research",
                 "Heffler E, et al. Clin Exp Allergy. 2018;48(9):1092-1106.", "10.1111/cea.13207", "29904978", 2018),
    "nac": ("유럽알레르기학회 비유발검사 표준화 입장문 (2018)", "EAACI Position paper on the standardization of nasal allergen challenges",
            "Augé J, et al. Allergy. 2018;73(8):1597-1608.", "10.1111/all.13416", "29377177", 2018),
    "rhinotools": ("유럽 비과 진단 도구 입장문 (2019)", "European position paper on diagnostic tools in rhinology",
                   "Rimmer J, et al. Rhinology. 2019;57(Suppl S28):1-41.", "10.4193/Rhin19.410", "31376816", 2019),
    "nno": ("비강 산화질소 측정 표준 프로토콜 (2020)", "Nasal Nitric Oxide Measurement in Primary Ciliary Dyskinesia. A Technical Paper on Standardized Testing Protocols",
            "Shapiro AJ, et al. Ann Am Thorac Soc. 2020;17(2):e1-e12.", "10.1513/AnnalsATS.201904-347OT", "31770003", 2020),
    "ait": ("유럽알레르기학회 알레르기 면역치료 지침: 알레르기 비결막염 (2018)", "EAACI Guidelines on Allergen Immunotherapy: Allergic rhinoconjunctivitis",
            "Roberts G, et al. Allergy. 2018;73(4):765-798.", "10.1111/all.13317", "28940458", 2018),
    "ilit": ("림프절 내 면역치료 평가와 초음파 유도 주사 권고 (2024)", "How to hit the allergy target: A critical appraisal of intralymphatic immunotherapy with practical recommendations on ultrasound-guided injections",
             "Flory S, et al. Allergy. 2024;79(8):2222-2234.", "10.1111/all.16138", "38712754", 2024),
    "itit": ("편도 내 면역치료 무작위 대조 시험 (2024)", "Efficacy and safety of intratonsillar immunotherapy for allergic rhinitis: A randomized, double-blind, placebo-controlled clinical trial",
             "Zhang J, et al. Ann Allergy Asthma Immunol. 2024;132(3):346-354.e1.", "10.1016/j.anai.2023.10.029", "37913839", 2024),
    "vrt": ("미국물리치료학회 전정재활 진료지침 (2022)", "Vestibular Rehabilitation for Peripheral Vestibular Hypofunction: An Updated Clinical Practice Guideline From the Academy of Neurologic Physical Therapy of the American Physical Therapy Association",
            "Hall CD, et al. J Neurol Phys Ther. 2022;46(2):118-177.", "10.1097/NPT.0000000000000382", "34864777", 2022),
    "cpap": ("미국수면의학회 양압기 치료 진료지침 (2019)", "Treatment of Adult Obstructive Sleep Apnea with Positive Airway Pressure: An American Academy of Sleep Medicine Clinical Practice Guideline",
             "Patil SP, et al. J Clin Sleep Med. 2019;15(2):335-343.", "10.5664/jcsm.7640", "30736887", 2019),
    "omt": ("수면무호흡 근기능 치료 체계적 고찰 (2015)", "Myofunctional Therapy to Treat Obstructive Sleep Apnea: A Systematic Review and Meta-analysis",
            "Camacho M, et al. Sleep. 2015;38(5):669-675.", "10.5665/sleep.4652", "25348130", 2015),
    "bdet": ("미국이비인후과학회 이관 풍선확장술 합의문 (2019)", "Clinical Consensus Statement: Balloon Dilation of the Eustachian Tube",
             "Tucci DL, et al. Otolaryngol Head Neck Surg. 2019;161(1):6-17.", "10.1177/0194599819848423", "31161864", 2019),
    "etd": ("이관기능장애 국제 합의문 (2015)", "Eustachian tube dysfunction: consensus statement on definition, types, clinical presentation and diagnosis",
            "Schilder AG, et al. Clin Otolaryngol. 2015;40(5):407-411.", "10.1111/coa.12475", "26347263", 2015),
    "arhl": ("미국이비인후과학회 노인성 난청 진료지침 (2024)", "Clinical Practice Guideline: Age-Related Hearing Loss",
             "Tsai Do BS, et al. Otolaryngol Head Neck Surg. 2024;170(Suppl 2):S1-S54.", "10.1002/ohn.750", "38687845", 2024),
    "cerumen": ("미국이비인후과학회 귀지 막힘 진료지침 (2017)", "Clinical Practice Guideline (Update): Earwax (Cerumen Impaction)",
                "Schwartz SR, et al. Otolaryngol Head Neck Surg. 2017;156(1_suppl):S1-S29.", "10.1177/0194599816671491", "28045591", 2017),
    "tmregen": ("고막 천공 재생 치료 (2011)", "Regenerative treatment for tympanic membrane perforation",
                "Kanemaru S, et al. Otol Neurotol. 2011;32(8):1218-1223.", "10.1097/MAO.0b013e31822e0e53", "21897328", 2011),
    "stutter": ("말더듬의 이해와 치료 (Am Fam Physician, 2019)", "Stuttering: Understanding and Treating a Common Disability",
                "Sander RW, Osborne CA. Am Fam Physician. 2019;100(9):556-560.", None, "31674746", 2019),
    "cbt": ("코크란 리뷰: 이명 인지행동치료 (2020)", "Cognitive behavioural therapy for tinnitus",
            "Fuller T, et al. Cochrane Database Syst Rev. 2020;1(1):CD012614.", "10.1002/14651858.CD012614.pub2", "31912887", 2020),
    "pnn": ("만성 비염 고주파 신경 차단 무작위 대조 시험 (2021)", "Effect of Radiofrequency Neurolysis on the Symptoms of Chronic Rhinitis: A Randomized Controlled Trial",
            "Stolovitzky JP, et al. OTO Open. 2021;5(3):2473974X211041124.", "10.1177/2473974X211041124", "34527852", 2021),
}


def ref(key):
    short, name, cite, doi, pmid, year = REF[key]
    d = {"short": short, "citation": cite, "name": name, "doi": doi, "pubmed": pmid, "year": year}
    return {k: v for k, v in d.items() if v is not None}


def P(t, cls=None):
    return {"p": t, **({"class": cls} if cls else {})}


def DEF(t):
    return P(t, "definition")


def H(t):
    return {"h2": t}


def UL(*items):
    return {"ul": list(items)}


def ALERT(items, p=None, title="이럴 때는 바로 진료를 받으세요"):
    a = {"title": title, "ul": list(items)}
    if p:
        a["p"] = p
    return {"alert": a}


def NOTE(title, p, items=()):
    """경고가 아닌 안내 상자 (예: 아직 표준 치료가 아닌 치료의 근거 수준 안내)."""
    a = {"title": title, "kind": "note", "p": p}
    if items:
        a["ul"] = list(items)
    return {"alert": a}


def FIG(fig, hl, caption, kind="anat"):
    return {"figure": {"fig": fig, "hl": hl, "caption": caption, "kind": kind}}


def STEPS(*pairs):
    return {"steps": [{"title": t, "text": x} for t, x in pairs]}


def T(name, typ="MedicalTest"):
    return {"name": name, "type": typ}


def page(slug, *, title, seo, meta, og, name, alt, codes, anatomy, desc, symptoms, risks, tests, treatments,
         complications, body, faq, refs):
    return {
        "slug": slug, "title": title, "seoTitle": seo, "metaDescription": meta, "ogDescription": og,
        "lastReviewed": DATE, "dateModified": DATE,
        "condition": {
            "name": name, "alternateName": alt,
            "codes": [{"codingSystem": s, "code": c} for s, c in codes],
            "anatomy": {"name": anatomy[0], "alternateName": anatomy[1]},
            "description": desc, "symptoms": symptoms, "riskFactors": risks,
            "tests": tests, "treatments": treatments, "complications": complications,
        },
        "body": body,
        "faq": [{"q": q, "a": a} for q, a in faq],
        "references": [ref(k) for k in refs],
    }


def write_all(pages):
    OUT.mkdir(parents=True, exist_ok=True)
    for p in pages:
        (OUT / f"{p['slug']}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", [p["slug"] for p in pages])


def care(slug, *, kind, group, region, title, seo, meta, og, typ, name, alt, desc, conditions, body, faq, refs,
         status="standard", location=None, how=None, prep=None, followup=None, device=None, adverse=(), contra=()):
    """검사·치료 한 편. kind: test | treatment, status: standard | emerging(근거가 쌓이는 중)."""
    entity = {"type": typ, "name": name, "alternateName": alt, "description": desc,
              "bodyLocation": location, "howPerformed": how, "preparation": prep, "followup": followup,
              "usesDevice": device, "adverseOutcomes": list(adverse), "contraindications": list(contra)}
    return {
        "slug": slug, "kind": kind, "group": group, "region": region, "status": status,
        "title": title, "seoTitle": seo, "metaDescription": meta, "ogDescription": og,
        "published": DATE, "lastReviewed": DATE, "dateModified": DATE,
        "entity": {k: v for k, v in entity.items() if v not in (None, [], "")},
        "conditions": conditions,
        "body": body,
        "faq": [{"q": q, "a": a} for q, a in faq],
        "references": [ref(k) for k in refs],
    }


CARE_TITLE = "검사·치료"
CARE_INTRO = ("이비인후과 진료실에서 실제로 하는 검사와 치료를 하나씩 설명합니다. 무엇을 알아보는 검사인지, 어떻게 진행하는지, "
              "아픈지, 치료 뒤에는 무엇을 조심해야 하는지 미리 알고 오시면 진료가 한결 편해집니다.")


def write_care(pages):
    """data/care/<slug>.json 과 묶음 순서 목록 data/care.json 을 쓴다."""
    CARE_OUT.mkdir(parents=True, exist_ok=True)
    groups = []
    for p in pages:
        p = dict(p)
        kind, name = p["kind"], p.pop("group")
        g = next((x for x in groups if x["kind"] == kind and x["name"] == name), None)
        if not g:
            g = {"kind": kind, "name": name, "slugs": []}
            groups.append(g)
        g["slugs"].append(p["slug"])
        (CARE_OUT / f"{p['slug']}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {"title": CARE_TITLE, "intro": CARE_INTRO, "groups": groups}
    (ROOT / "data" / "care.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote care", [p["slug"] for p in pages])
