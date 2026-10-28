import streamlit as st
import json
import os
from datetime import datetime

import plotly.graph_objects as go

from analyzer import (
    analyze_draft, check_template, extract_references, validate_references,
    detect_conflicts, check_terminology, standardize_text, load_json
)

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="MAHA-GR-ALIGN | Govt. of Maharashtra",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2. THEME STATE
# =========================================================
if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

LIGHT = {
    "app_bg": "radial-gradient(circle at 10% 0%, #eef3fb 0%, #f6f8fb 35%, #f4f6f9 100%)",
    "text_primary": "#1e3c72",
    "text_secondary": "#555b66",
    "text_muted": "#6c757d",
    "card_bg": "#ffffff",
    "card_border": "#e3e8f0",
    "banner_grad": "linear-gradient(120deg, #0f2557 0%, #1e3c72 45%, #2a5298 100%)",
    "banner_text": "#d7e5fb",
    "sidebar_grad": "linear-gradient(180deg, #0b1220 0%, #111827 100%)",
    "footer_bg": "#eef2f8",
    "footer_text": "#667085",
    "tab_bg": "#eef2f8",
    "tab_active_bg": "#ffffff",
    "shadow": "rgba(30, 60, 114, 0.10)",
}

DARK = {
    "app_bg": "radial-gradient(circle at 10% 0%, #131a2b 0%, #0d1220 40%, #0a0e18 100%)",
    "text_primary": "#eaf0ff",
    "text_secondary": "#c3cbdb",
    "text_muted": "#9aa4bb",
    "card_bg": "#161d2e",
    "card_border": "#2a3450",
    "banner_grad": "linear-gradient(120deg, #060b18 0%, #101c3d 45%, #1b3a72 100%)",
    "banner_text": "#c7d7f7",
    "sidebar_grad": "linear-gradient(180deg, #05070d 0%, #0a0e18 100%)",
    "footer_bg": "#151b2c",
    "footer_text": "#9aa4bb",
    "tab_bg": "#161d2e",
    "tab_active_bg": "#1e2740",
    "shadow": "rgba(0, 0, 0, 0.45)",
}

T = DARK if st.session_state["theme"] == "Dark" else LIGHT

# =========================================================
# 3. CUSTOM CSS — GLASSMORPHIC / ANIMATED THEME, BIG BEZELS
# =========================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');

    html, body, .stApp {{
        font-family: 'Inter', sans-serif;
        background: {T['app_bg']};
    }}
    .stApp, .stApp p, .stApp li, .stApp span, .stApp label {{
        color: {T['text_secondary']};
    }}
    .stMarkdown, .stText {{ color: {T['text_secondary']}; }}
    h1, h2, h3, h4 {{ color: {T['text_primary']} !important; }}

    /* ---------- Hide default streamlit chrome (but keep sidebar controls working) ---------- */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stToolbar"] {{visibility: hidden;}}
    [data-testid="stDecoration"] {{display: none;}}
    header[data-testid="stHeader"] {{background: transparent;}}

    /* The sidebar reopen arrow lives inside stToolbar, so it inherits the
       visibility:hidden above unless explicitly overridden here. */
    [data-testid="stExpandSidebarButton"],
    [data-testid="stExpandSidebarButton"] * {{
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
    }}
    [data-testid="stExpandSidebarButton"] svg {{
        fill: {T['text_primary']} !important;
    }}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] * {{
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
    }}

    /* ---------- Animated top header banner (BIG BEZEL) ---------- */
    .header-banner {{
        position: relative;
        overflow: hidden;
        background: {T['banner_grad']};
        padding: 38px 44px;
        border-radius: 28px;
        border: 3px solid rgba(255,255,255,0.08);
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 14px 36px {T['shadow']};
        display: flex;
        align-items: center;
        gap: 26px;
        animation: fadeSlideIn 0.6s ease-out;
    }}
    .header-banner::after {{
        content: "";
        position: absolute;
        top: -60%;
        right: -10%;
        width: 340px;
        height: 340px;
        background: radial-gradient(circle, rgba(255,193,7,0.18) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        animation: pulseGlow 6s ease-in-out infinite;
    }}
    .header-banner h1 {{
        color: #ffffff !important;
        font-family: 'Poppins', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 0.3px;
    }}
    .header-banner .subtitle {{
        color: {T['banner_text']};
        font-size: 1.04rem;
        margin-top: 6px;
        margin-bottom: 0;
    }}
    .header-banner .tagline {{
        display: inline-block;
        margin-top: 12px;
        background: rgba(255, 193, 7, 0.15);
        border: 2px solid rgba(255, 193, 7, 0.4);
        color: #ffe9a8;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.6px;
        padding: 5px 14px;
        border-radius: 22px;
        text-transform: uppercase;
    }}

    @keyframes fadeSlideIn {{
        from {{ opacity: 0; transform: translateY(-14px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes pulseGlow {{
        0%, 100% {{ opacity: 0.6; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.15); }}
    }}

    /* ---------- Government emblem (stylised, not an official seal), BIG BEZEL ---------- */
    .gov-emblem {{
        flex-shrink: 0;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 30%, #ffe9a8, #ffb300 55%, #d98c00 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 22px rgba(0,0,0,0.3), inset 0 0 0 6px rgba(255,255,255,0.35);
        position: relative;
        z-index: 1;
        border: 3px solid rgba(255,255,255,0.5);
    }}
    .gov-emblem svg {{ width: 52px; height: 52px; }}

    /* ---------- Metric / KPI cards (BIG BEZEL) ---------- */
    .metric-card {{
        background: {T['card_bg']};
        border: 2px solid {T['card_border']};
        padding: 22px 18px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 14px {T['shadow']};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 28px {T['shadow']};
    }}
    .metric-card h3 {{
        color: {T['text_muted']};
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 8px;
        font-weight: 600;
    }}
    .metric-card p {{
        color: {T['text_primary']};
        font-size: 1.7rem;
        font-weight: 800;
        margin: 0;
        font-family: 'Poppins', sans-serif;
    }}

    /* ---------- Badges ---------- */
    .badge {{
        display: inline-block;
        padding: 4px 13px;
        border-radius: 22px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
        border-width: 2px;
        border-style: solid;
    }}
    .badge-green {{ background: rgba(26,127,78,0.12); color: #1a7f4e; border-color: rgba(26,127,78,0.35); }}
    .badge-amber {{ background: rgba(154,107,0,0.12); color: #c98a00; border-color: rgba(154,107,0,0.35); }}
    .badge-red   {{ background: rgba(180,35,24,0.12); color: #d1453a; border-color: rgba(180,35,24,0.35); }}
    .badge-blue  {{ background: rgba(30,80,162,0.12); color: #3f7bdb; border-color: rgba(30,80,162,0.35); }}

    /* ---------- Section title with accent bar ---------- */
    .section-title {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 8px 0 16px 0;
    }}
    .section-title .bar {{
        width: 7px;
        height: 26px;
        background: linear-gradient(180deg, #2a5298, #ffb300);
        border-radius: 6px;
    }}
    .section-title span {{
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 1.18rem;
        color: {T['text_primary']};
    }}

    /* ---------- Reference / conflict cards (BIG BEZEL) ---------- */
    .ref-card {{
        background: {T['card_bg']};
        border-radius: 18px;
        border: 2px solid {T['card_border']};
        border-left: 7px solid #2a9d8f;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 3px 10px {T['shadow']};
        transition: transform 0.15s ease;
    }}
    .ref-card:hover {{ transform: translateX(4px); }}
    .ref-card.warn {{ border-left-color: #f4a300; }}
    .ref-card.danger {{ border-left-color: #e63946; }}

    /* ---------- Buttons (BIG BEZEL) ---------- */
    .stButton > button {{
        border-radius: 14px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: 2px solid transparent !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 18px {T['shadow']};
    }}

    /* ---------- Tabs (BIG BEZEL) ---------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {T['tab_bg']};
        padding: 8px;
        border-radius: 16px;
        border: 2px solid {T['card_border']};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        font-weight: 600;
        color: {T['text_primary']};
        padding: 9px 18px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {T['tab_active_bg']} !important;
        box-shadow: 0 3px 10px {T['shadow']};
    }}

    /* ---------- Text areas / inputs (BIG BEZEL) ---------- */
    .stTextArea textarea, .stTextInput input {{
        border-radius: 16px !important;
        border: 2px solid {T['card_border']} !important;
        background: {T['card_bg']} !important;
        color: {T['text_secondary']} !important;
    }}

    /* ---------- Expanders (BIG BEZEL) ---------- */
    details {{
        border-radius: 16px !important;
        border: 2px solid {T['card_border']} !important;
        background: {T['card_bg']} !important;
        overflow: hidden;
    }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{
        background: {T['sidebar_grad']};
    }}
    section[data-testid="stSidebar"] * {{
        color: #f3f4f6 !important;
    }}
    .sidebar-emblem {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 6px 8px 6px;
    }}
    .sidebar-emblem .gov-emblem {{ width: 52px; height: 52px; border-width: 2px; }}
    .sidebar-emblem .gov-emblem svg {{ width: 30px; height: 30px; }}
    .sidebar-title {{
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        font-size: 1.05rem;
        line-height: 1.2;
    }}
    .sidebar-sub {{
        font-size: 0.72rem;
        color: #9ca3af !important;
        margin-top: 2px;
    }}

    /* ---------- Footer strip (BIG BEZEL) ---------- */
    .footer-strip {{
        margin-top: 36px;
        padding: 20px 24px;
        border-radius: 20px;
        border: 2px solid {T['card_border']};
        background: {T['footer_bg']};
        color: {T['footer_text']};
        font-size: 0.82rem;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# Stylised state-emblem SVG (an original design inspired by an ashoka-chakra motif,
# NOT a reproduction of the official Government of Maharashtra seal).
GOV_EMBLEM_SVG = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="46" fill="none" stroke="#0f2557" stroke-width="3"/>
  <g stroke="#0f2557" stroke-width="2.4">
    <line x1="50" y1="8" x2="50" y2="92"/>
    <line x1="8" y1="50" x2="92" y2="50"/>
    <line x1="18" y1="18" x2="82" y2="82"/>
    <line x1="82" y1="18" x2="18" y2="82"/>
    <line x1="50" y1="8" x2="65" y2="20"/>
    <line x1="50" y1="8" x2="35" y2="20"/>
    <line x1="50" y1="92" x2="65" y2="80"/>
    <line x1="50" y1="92" x2="35" y2="80"/>
    <line x1="8" y1="50" x2="20" y2="35"/>
    <line x1="8" y1="50" x2="20" y2="65"/>
    <line x1="92" y1="50" x2="80" y2="35"/>
    <line x1="92" y1="50" x2="80" y2="65"/>
  </g>
  <circle cx="50" cy="50" r="9" fill="#0f2557"/>
</svg>
"""

SAMPLE_DRAFTS = {
    "✅ Fully Compliant Draft": """PREAMBLE: The Government has reviewed the infrastructure needs of Government Polytechnic institutions and decided to sanction additional laboratory equipment grants.
REFERENCE: 1) Government Resolution No. HTE-2019/CR-10/16-A dated 4th June 2019 2) Government Resolution No. HTE-2022/CR-33/16-A dated 14th April 2022.
GOVERNMENT DECISION: Government is pleased to sanction a one-time laboratory equipment grant of Rs 10 lakh per institute for Financial Year 2026-27, subject to prior concurrence of Finance Department for each disbursement, in accordance with standing financial rules.
SANCTION: The expenditure of Rs 2 crore shall be met from the provision under Major Head 2203.
By order and in the name of the Governor of Maharashtra.
Copy forwarded to: 1) All Government Polytechnic Institutions 2) Finance Department 3) Accountant General, Maharashtra.
""",

    "❌ Missing MOP Sections": """The Higher & Technical Education Department has decided that all Government Engineering Colleges will now receive an additional grant of Rs 5 lakh for library modernization starting this year.
This decision has been taken keeping in mind the need for updated resources in colleges. Colleges should start utilizing the fund immediately and report utilization to the department.
""",

    "⚠️ Cross-Department Conflict": """PREAMBLE: The Government has decided to enhance the annual maintenance grant to Government Engineering Colleges further in view of rising infrastructure costs.
REFERENCE: 1) Government Resolution No. HTE-2019/CR-10/16-A dated 4th June 2019 2) Government Resolution No. HTE-2022/CR-33/16-A dated 14th April 2022.
GOVERNMENT DECISION: Government is pleased to enhance the annual maintenance grant from Rs 18 lakh to Rs 25 lakh per institute with effect from Financial Year 2026-27, without requiring further concurrence of Finance Department for release in subsequent years, so that colleges can get the money asap.
SANCTION: The additional expenditure of Rs 5 crore shall be met from the provision under Major Head 2203.
By order and in the name of the Governor of Maharashtra.
Copy forwarded to: 1) All Government Engineering Colleges 2) Finance Department
""",

    "🖊️ Informal / Non-Standard Terminology": """PREAMBLE: Govt has decided to speed up release of funds to Primary Health Centres asap due to urgent requirement of medicines and equipment.
REFERENCE: Government Resolution No. PH-2022/CR-19/Ayush-1 dated 27th May 2022.
GOVERNMENT DECISION: The department will try to release the additional grant of Rs 8 lakh per PHC ASAP, and centres should use the money as soon as possible without delay so that things move fast on the ground.
SANCTION: The expenditure of Rs 40 crore shall be met from the provision under Major Head 2210.
By order and in the name of the Governor of Maharashtra.
Copy forwarded to: 1) Director of Health Services 2) Finance Department.
""",

    "🔗 Unverified / Broken Reference": """PREAMBLE: The Government has decided to revise norms for release of scholarship funds to aided secondary schools.
REFERENCE: 1) Government Resolution No. SE-2011/CR-99/PS-7 dated 3rd March 2011 2) Government Resolution No. HTE-2019/CR-10/16-A dated 4th June 2019.
GOVERNMENT DECISION: Government is pleased to release scholarship funds at the revised rate of Rs 3,000 per student per annum, subject to concurrence of Finance Department.
SANCTION: The expenditure shall be met from the provision under Major Head 2202.
By order and in the name of the Governor of Maharashtra.
Copy forwarded to: 1) Director of Education 2) Finance Department.
""",
}

SAMPLE_DRAFT = SAMPLE_DRAFTS["⚠️ Cross-Department Conflict"]  # default / backward-compat

def section_title(text: str):
    st.markdown(f"""
        <div class="section-title"><div class="bar"></div><span>{text}</span></div>
    """, unsafe_allow_html=True)


def compliance_gauge(score: int):
    color = "#e63946" if score < 50 else "#f4a300" if score < 80 else "#1a7f4e"
    number_color = T["text_primary"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "%", "font": {"size": 34, "color": number_color, "family": "Poppins"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": T["card_border"]},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": T["card_bg"],
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "rgba(230,57,70,0.15)"},
                {"range": [50, 80], "color": "rgba(244,163,0,0.15)"},
                {"range": [80, 100], "color": "rgba(26,127,78,0.15)"},
            ],
        },
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": T["text_secondary"]},
    )
    return fig


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-emblem">
            <div class="gov-emblem">{GOV_EMBLEM_SVG}</div>
            <div>
                <div class="sidebar-title">MAHA-GR-ALIGN</div>
                <div class="sidebar-sub">Govt. of Maharashtra · Prototype</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.caption("AI-Assisted GR Drafting & Alignment")
    st.markdown("---")

    theme_choice = st.radio(
        "🌗 Appearance",
        ["Light", "Dark"],
        index=0 if st.session_state["theme"] == "Light" else 1,
        horizontal=True,
    )
    if theme_choice != st.session_state["theme"]:
        st.session_state["theme"] = theme_choice
        st.rerun()

    st.markdown("---")
    st.markdown("**Problem Area 1**\n\nStreamline Government Resolution processing.")
    st.markdown("---")
    view = st.radio("Navigate", ["🔍 Analyze Draft GR", "📚 Sample GR Corpus", "ℹ️ About"])
    st.markdown("---")
    st.caption(f"🕒 Session started: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    st.caption("VJTI AI Hackathon 2026")

corpus = load_json("sample_grs.json")

# =========================================================
# HEADER (shared across views)
# =========================================================
HEADER_TITLES = {
    "🔍 Analyze Draft GR": ("MAHA-GR-ALIGN Engine",
        "AI-Assisted Government Resolution Drafting, Cross-Dept Conflict Detection & Alignment"),
    "📚 Sample GR Corpus": ("Sample GR Corpus",
        "Reference database used for real-time validation & conflict checks"),
    "ℹ️ About": ("About MAHA-GR-ALIGN", "AI-Assisted Resolution Engine · Problem Area 1"),
}
title, subtitle = HEADER_TITLES[view]
st.markdown(f"""
    <div class="header-banner">
        <div class="gov-emblem">{GOV_EMBLEM_SVG}</div>
        <div>
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
            <span class="tagline">Government of Maharashtra</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# MAIN VIEW: ANALYZE
# =========================================================
if view == "🔍 Analyze Draft GR":

    st.write(
        "Paste a draft Government Resolution (GR) below. The tool checks MOP template "
        "compliance, extracts & validates references, detects cross-departmental conflicts, "
        "and flags non-standard terminology."
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        sample_choice = st.selectbox(
            "Demo scenario",
            list(SAMPLE_DRAFTS.keys()),
            help="Pick a scenario, then click Load — each one exercises a different part of the checker.",
            label_visibility="collapsed",
        )
    with col_b:
        if st.button("📋 Load sample draft", use_container_width=True):
            st.session_state["draft_text"] = SAMPLE_DRAFTS[sample_choice]
            st.rerun()

    draft_text = st.text_area(
        "Draft GR text",
        value=st.session_state.get("draft_text", ""),
        height=260,
        placeholder="Paste your draft Government Resolution text here..."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        analyze_clicked = st.button("🚀 Analyze Draft GR", type="primary", use_container_width=True)
    with col2:
        clear_clicked = st.button("🗑️ Clear", use_container_width=True)
        if clear_clicked:
            st.session_state["draft_text"] = ""
            st.rerun()

    if analyze_clicked and draft_text.strip():
        with st.spinner("Analyzing draft against MOP template and GR corpus..."):
            results = analyze_draft(draft_text)

        st.markdown("---")
        section_title("Analysis Summary & Results")

        # ---- Top KPI strip ----
        t = results["template"]
        refs = results["references"]
        conflicts = results["conflicts"]
        flags = results["terminology"]

        verified_refs = sum(1 for r in refs if r["status"] == "verified")
        possible_conflicts = sum(1 for c in conflicts if c["possible_conflict"])

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""<div class="metric-card"><h3>MOP Compliance</h3><p>{t['compliance_score']}%</p></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="metric-card"><h3>References Verified</h3><p>{verified_refs}/{len(refs)}</p></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="metric-card"><h3>Possible Conflicts</h3><p>{possible_conflicts}</p></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="metric-card"><h3>Terms Flagged</h3><p>{len(flags)}</p></div>""", unsafe_allow_html=True)

        st.write("")
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Template Compliance",
            "🔗 Reference Tracking",
            "⚠️ Conflict Detection",
            "🖊️ Terminology"
        ])

        # --- TAB 1: TEMPLATE ---
        with tab1:
            c1, c2 = st.columns([1, 1])
            with c1:
                st.plotly_chart(compliance_gauge(t["compliance_score"]), use_container_width=True)
            with c2:
                if t["missing_sections"]:
                    st.markdown('<span class="badge badge-red">Action needed</span>', unsafe_allow_html=True)
                    st.error(f"Missing sections: {', '.join(t['missing_sections'])}")
                else:
                    st.markdown('<span class="badge badge-green">Fully compliant</span>', unsafe_allow_html=True)
                    st.success("All required MOP sections are present!")

            st.write("")
            for sec in t["sections"]:
                icon = "✅" if sec["present"] else "❌"
                badge = '<span class="badge badge-green">Present</span>' if sec["present"] else '<span class="badge badge-red">Missing</span>'
                with st.expander(f"{icon} {sec['section']}"):
                    st.markdown(badge, unsafe_allow_html=True)
                    st.write(sec["description"])

        # --- TAB 2: REFERENCES ---
        with tab2:
            if not refs:
                st.warning("No GR references detected in the draft text.")
            for r in refs:
                if r["status"] == "verified":
                    st.markdown(f"""
                        <div class="ref-card">
                            <span class="badge badge-green">Verified</span>
                            <p style="margin:8px 0 2px 0;"><b>{r['gr_number']}</b> (dated {r.get('date') or 'unknown'})</p>
                            <p style="margin:0;">Matched: <i>{r['matched_title']}</i> — {r['matched_department']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="ref-card warn">
                            <span class="badge badge-amber">{r['status'].title()}</span>
                            <p style="margin:8px 0 2px 0;"><b>{r['gr_number']}</b> (dated {r.get('date') or 'unknown'})</p>
                            <p style="margin:0;">Double-check this citation manually.</p>
                        </div>
                    """, unsafe_allow_html=True)

        # --- TAB 3: CONFLICTS ---
        with tab3:
            if not conflicts:
                st.success("No significant overlap with existing GRs detected in the sample corpus.")
            for c in conflicts:
                badge = '<span class="badge badge-red">Possible conflict</span>' if c["possible_conflict"] else '<span class="badge badge-blue">Low / review</span>'
                with st.expander(f"{'🚨' if c['possible_conflict'] else '🟡'} {c['department']} — {c['title']} (similarity: {c['similarity']})"):
                    st.markdown(badge, unsafe_allow_html=True)
                    st.write(f"**GR Number:** `{c['gr_number']}`")
                    st.write(f"**Reason:** {c['reason']}")

        # --- TAB 4: TERMINOLOGY ---
        with tab4:
            if not flags:
                st.success("No non-standard terminology detected.")
            else:
                st.markdown(f'<span class="badge badge-amber">{len(flags)} term(s) flagged</span>', unsafe_allow_html=True)
                st.write("")
                for f in flags:
                    st.markdown(f"- \"`{f['found']}`\" → Suggestion: **{f['suggested']}**")

                st.write("")
                section_title("Auto-standardized version")
                st.text_area("Standardized draft output", standardize_text(draft_text), height=200)

    elif analyze_clicked:
        st.warning("Please paste or load a draft GR first.")

# =========================================================
# SAMPLE CORPUS VIEW
# =========================================================
elif view == "📚 Sample GR Corpus":
    st.caption(
        "In production this connects to the real Maharashtra GR repository (aaplesarkar / gr.maharashtra.gov.in)."
    )
    search = st.text_input("🔎 Search corpus by GR number, title, or department")
    st.write("")

    filtered = corpus
    if search.strip():
        s = search.lower()
        filtered = [
            gr for gr in corpus
            if s in gr["gr_number"].lower() or s in gr["title"].lower() or s in gr["department"].lower()
        ]

    if not filtered:
        st.info("No matching GRs found.")

    for gr in filtered:
        with st.expander(f"📄 {gr['gr_number']} — {gr['title']} ({gr['department']})"):
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown(f'<span class="badge badge-blue">{gr["department"]}</span>', unsafe_allow_html=True)
                st.write(f"**Date:** {gr['date']}")
            with c2:
                st.code(gr["text"], language="text")

# =========================================================
# ABOUT
# =========================================================
else:
    st.markdown("""
**VJTI AI Hackathon 2026**

MAHA-GR-ALIGN is an AI-assisted tool to help draft, validate, and cross-check
Government Resolutions (GRs) against the **Manual of Office Procedure (MOP)**, prior
GRs, and standard legal terminology.
""")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
            <div class="ref-card">
                <b>🎯 Cross-Departmental Conflict Detection</b><br>
                Identifies overlaps using TF-IDF similarity and rule-based contradiction heuristics.
            </div>
            <div class="ref-card">
                <b>🌐 Terminology Standardization</b><br>
                Dictionary-backed legal terminology mapping.
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
            <div class="ref-card">
                <b>🔗 Automated Reference Tracking</b><br>
                Regex pattern extraction matched directly against active GR corpus.
            </div>
            <div class="ref-card">
                <b>📋 Strict Template Enforcement</b><br>
                Automated checklist evaluating structural compliance against MOP guidelines.
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    section_title("Tech Stack")
    st.markdown("Python · Streamlit · scikit-learn (TF-IDF) · Regex · Plotly")

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
    <div class="footer-strip">
        ⚖️ MAHA-GR-ALIGN — Prototype built for VJTI AI Hackathon 2026 · Not an official Government of Maharashtra product
    </div>
""", unsafe_allow_html=True)