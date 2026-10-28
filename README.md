# MAHA-GR-ALIGN
### AI-Assisted GR Drafting & Alignment — VJTI AI Hackathon 2026, Problem Area 1

Streamline Government Resolution (GR) processing by automatically checking a draft GR against:
1. **Manual of Office Procedure (MOP) template** — required sections present or missing
2. **Reference tracking** — extracts cited GR numbers/dates, validates them against a corpus
3. **Cross-departmental conflict detection** — flags overlap/contradiction with existing GRs from other departments
4. **Terminology standardization** — flags informal/inconsistent wording and suggests standard legal phrasing

---

## Quick start (run this first)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

In the app, click **"Load sample draft"** then **"Analyze Draft"** to see all 4 features fire on a
pre-built example that has a deliberate procedural conflict baked in (bypassing Finance Department
concurrence) — good for a live demo.

---

## Project structure

```
gr_align/
├── app.py                  # Streamlit UI (4 tabs: Template, References, Conflicts, Terminology)
├── analyzer.py              # Core logic for all 4 features
├── requirements.txt
├── data/
│   ├── sample_grs.json       # 6 synthetic GRs across departments (the "corpus")
│   ├── mop_template.json     # Required MOP sections + detection keywords
│   └── terminology_dict.json # Informal → standard term mappings
└── README.md
```

## How each feature works (for your pitch)

| Feature | Method | Why this approach (given time constraints) |
|---|---|---|
| Template Enforcement | Keyword/phrase matching against a configurable MOP checklist (`mop_template.json`) | Deterministic, explainable, no ML training needed — matches how a real clerk would check a draft |
| Reference Tracking | Regex extraction of "GR No. ... dated ..." patterns, cross-checked against the corpus | Fast, doesn't need an LLM; extensible to real gr.maharashtra.gov.in scraping later |
| Conflict Detection | TF-IDF cosine similarity (scikit-learn) to surface topically related GRs + rule-based heuristics (e.g. "without concurrence" vs "concurrence of Finance Department") | Works fully offline, no API key required, and the heuristic layer catches *procedural* contradictions, not just topic overlap |
| Terminology Standardization | Dictionary-based find & suggest, plus one-click auto-rewrite | Simple, auditable, and easy for a judge to verify by inspecting `terminology_dict.json` |

## Extending this for a stronger submission (if you get more time)

- Replace `data/sample_grs.json` with real GRs scraped from `gr.maharashtra.gov.in` / `aaplesarkar`
- Swap TF-IDF for sentence-embedding similarity (e.g. `sentence-transformers`) for better semantic conflict detection
- Add an LLM call (Claude/GPT) to rewrite non-compliant sections automatically, not just flag them
- Add a PDF/DOCX upload option (drafts often arrive as Word docs) instead of paste-only

## Demo script (2 minutes)

1. "This tool helps government departments draft GRs correctly and catch conflicts before they're issued."
2. Load the sample draft → click Analyze.
3. **Template tab**: "All MOP sections are present — 100% compliance."
4. **References tab**: "It found 2 citations — one verified against our GR database, one flagged as unverified for manual check."
5. **Conflicts tab**: "Here's the key insight — this draft tries to waive Finance Department concurrence for future grant releases, but it's semantically 83% similar to an earlier GR on the same topic, and our rule engine flags the contradiction directly."
6. **Terminology tab**: "It also caught informal phrasing like 'asap' and auto-suggests the standard legal term, with one-click rewrite."
