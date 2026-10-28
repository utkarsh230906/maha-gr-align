"""
MAHA-GR-ALIGN core analysis engine.
Implements the 4 required features on top of plain Python + scikit-learn (no heavy ML downloads needed):
 1. Template Enforcement (Manual of Office Procedure)
 2. Automated Reference Tracking
 3. Cross-Departmental Conflict Detection
 4. Terminology Standardization
"""

import json
import re
import os
from difflib import SequenceMatcher

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- 1. TEMPLATE ENFORCEMENT ----------

def check_template(draft_text, mop_template=None):
    if mop_template is None:
        mop_template = load_json("mop_template.json")["required_sections"]

    text_lower = draft_text.lower()
    results = []
    for section in mop_template:
        found = any(kw.lower() in text_lower for kw in section["keywords"])
        results.append({
            "section": section["name"],
            "description": section["description"],
            "present": found
        })
    missing = [r["section"] for r in results if not r["present"]]
    score = round(100 * (len(results) - len(missing)) / len(results), 1)
    return {
        "sections": results,
        "missing_sections": missing,
        "compliance_score": score
    }


# ---------- 2. AUTOMATED REFERENCE TRACKING ----------

GR_NUMBER_PATTERN = re.compile(
    r"(?:Government Resolution No\.?|GR No\.?|Reference No\.?)\s*([A-Za-z]{2,5}[-/][0-9A-Za-z/\-]+)",
    re.IGNORECASE
)
DATE_PATTERN = re.compile(
    r"dated\s+(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    re.IGNORECASE
)


def extract_references(draft_text):
    refs = []
    for m in GR_NUMBER_PATTERN.finditer(draft_text):
        gr_num = m.group(1).strip().rstrip('.').rstrip(',')
        # try to find a nearby date within the next 60 chars
        window = draft_text[m.end(): m.end() + 60]
        date_match = DATE_PATTERN.search(window)
        date = date_match.group(1) if date_match else None
        refs.append({"gr_number": gr_num, "date": date})
    return refs


def validate_references(refs, corpus):
    known_numbers = {gr["gr_number"].lower(): gr for gr in corpus}
    validated = []
    for r in refs:
        key = r["gr_number"].lower()
        if key in known_numbers:
            match = known_numbers[key]
            validated.append({
                **r,
                "status": "verified",
                "matched_title": match["title"],
                "matched_department": match["department"]
            })
        else:
            validated.append({**r, "status": "unverified / not found in corpus"})
    return validated


# ---------- 3. CROSS-DEPARTMENTAL CONFLICT DETECTION ----------

def detect_conflicts(draft_text, corpus, top_k=3, similarity_threshold=0.15):
    corpus_texts = [gr["text"] for gr in corpus]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [draft_text])
    draft_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    sims = cosine_similarity(draft_vec, corpus_vecs)[0]

    ranked = sorted(
        zip(corpus, sims), key=lambda x: x[1], reverse=True
    )[:top_k]

    flagged = []
    for gr, score in ranked:
        if score < similarity_threshold:
            continue
        conflict_signal = _keyword_conflict_signal(draft_text, gr["text"])
        flagged.append({
            "gr_id": gr["id"],
            "department": gr["department"],
            "title": gr["title"],
            "gr_number": gr["gr_number"],
            "similarity": round(float(score), 3),
            "possible_conflict": conflict_signal["conflict"],
            "reason": conflict_signal["reason"]
        })
    return flagged


CONTRADICTION_MARKERS = [
    ("without requiring", "concurrence of finance department"),
    ("without", "concurrence"),
    ("not require", "concurrence"),
    ("shall not", "sanction"),
]


def _keyword_conflict_signal(draft_text, existing_text):
    d = draft_text.lower()
    e = existing_text.lower()
    # simple heuristic: if draft claims to bypass a control (concurrence/sanction)
    # that the matched GR or a Finance-type GR insists on, flag it.
    for marker_a, marker_b in CONTRADICTION_MARKERS:
        if marker_a in d and marker_b in e:
            return {
                "conflict": True,
                "reason": f"Draft contains phrase pattern resembling '{marker_a}...' while the "
                          f"existing GR emphasizes '{marker_b}' — review for procedural contradiction."
            }
    if "finance department" in e and "concurrence" not in d:
        return {
            "conflict": True,
            "reason": "Related existing GR requires Finance Department concurrence, but the draft "
                      "does not mention seeking such concurrence."
        }
    return {"conflict": False, "reason": "High topical overlap; no explicit contradiction detected, but review recommended."}


# ---------- 4. TERMINOLOGY STANDARDIZATION ----------

def check_terminology(draft_text, term_dict=None):
    if term_dict is None:
        term_dict = load_json("terminology_dict.json")

    text_lower = draft_text.lower()
    flags = []
    for informal, standard in term_dict.items():
        for m in re.finditer(re.escape(informal.lower()), text_lower):
            start, end = m.span()
            flags.append({
                "found": draft_text[start:end],
                "suggested": standard,
                "position": start
            })
    return flags


def standardize_text(draft_text, term_dict=None):
    if term_dict is None:
        term_dict = load_json("terminology_dict.json")
    result = draft_text
    # sort longest phrase first to avoid partial overlaps
    for informal in sorted(term_dict, key=len, reverse=True):
        pattern = re.compile(re.escape(informal), re.IGNORECASE)
        result = pattern.sub(term_dict[informal], result)
    return result


# ---------- FULL PIPELINE ----------

def analyze_draft(draft_text):
    corpus = load_json("sample_grs.json")
    template_result = check_template(draft_text)
    refs = extract_references(draft_text)
    refs_validated = validate_references(refs, corpus)
    conflicts = detect_conflicts(draft_text, corpus)
    terminology_flags = check_terminology(draft_text)

    return {
        "template": template_result,
        "references": refs_validated,
        "conflicts": conflicts,
        "terminology": terminology_flags
    }
