"""
app.py
Cipla Learner Persona Dashboard — Streamlit App

Upload your survey Excel → Get an interactive dashboard HTML
Data never stored. Processed in memory, downloaded instantly.
"""

import streamlit as st
import pandas as pd
import json
import io
import os
import traceback
from processor import process

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cipla · Learner Persona Dashboard",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — matches dashboard look & feel
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fraunces:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* App background */
.stApp { background: #f0f4f8; }

/* Top bar */
.cipla-header {
    background: #1a2340;
    padding: 18px 32px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 28px;
    box-shadow: 0 4px 24px rgba(26,35,64,0.18);
}
.cipla-logo {
    font-family: 'Fraunces', serif;
    font-size: 24px;
    color: #fff;
}
.cipla-logo span { color: #60a5fa; }
.cipla-subtitle {
    font-size: 12px;
    color: rgba(255,255,255,0.45);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* Upload area */
.upload-card {
    background: #fff;
    border-radius: 14px;
    padding: 40px 36px;
    box-shadow: 0 4px 24px rgba(26,35,64,0.09);
    margin-bottom: 24px;
    border-top: 4px solid #0d6efd;
}
.upload-title {
    font-family: 'Fraunces', serif;
    font-size: 22px;
    color: #1a2340;
    margin-bottom: 6px;
}
.upload-sub {
    font-size: 13px;
    color: #7589a8;
    margin-bottom: 24px;
    line-height: 1.6;
}

/* Info cards */
.info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
    margin-bottom: 28px;
}
.info-card {
    background: #fff;
    border-radius: 12px;
    padding: 18px 16px;
    box-shadow: 0 2px 12px rgba(26,35,64,0.07);
    border-left: 3px solid #0d6efd;
    font-size: 12px;
    color: #3d4f6e;
    line-height: 1.6;
}
.info-card strong {
    display: block;
    font-size: 13px;
    color: #1a2340;
    margin-bottom: 4px;
}

/* Step badges */
.step-badge {
    background: #0d6efd;
    color: white;
    border-radius: 50%;
    width: 22px; height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    margin-right: 8px;
}

/* Privacy note */
.privacy-note {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 12px;
    color: #166534;
    margin-top: 16px;
    line-height: 1.6;
}

/* Processing status */
.status-card {
    background: #fff;
    border-radius: 14px;
    padding: 32px;
    box-shadow: 0 4px 24px rgba(26,35,64,0.09);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="cipla-header">
    <div>
        <div class="cipla-logo">Cipla<span>·</span>L&D</div>
        <div class="cipla-subtitle">Learner Persona Dashboard Generator</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INFO CARDS
# ─────────────────────────────────────────────
st.markdown("""
<div class="info-grid">
    <div class="info-card">
        <strong>🔒 Your Data Stays Private</strong>
        The Excel file is processed in memory only. Nothing is stored on any server. When you close the browser, it is gone.
    </div>
    <div class="info-card">
        <strong>⚡ Fast Processing</strong>
        The app reads your file, assigns learner personas, computes insights, and generates the dashboard in under 30 seconds.
    </div>
    <div class="info-card">
        <strong>📥 One Download</strong>
        You get a single HTML file. Share it with anyone — trainers, managers, L&D partners. No login needed to view it.
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UPLOAD SECTION
# ─────────────────────────────────────────────
st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown('<div class="upload-title">Upload Survey Data</div>', unsafe_allow_html=True)
st.markdown("""
<div class="upload-sub">
    Upload your Cipla Learning Survey Excel file. The app will automatically detect the right columns,
    assign each respondent a learner persona type, and build the full interactive dashboard.
    <br><br>
    <span class="step-badge">1</span>Upload Excel below &nbsp;
    <span class="step-badge">2</span>Click Generate Dashboard &nbsp;
    <span class="step-badge">3</span>Download and share the HTML file
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose your Excel file",
    type=["xlsx", "xls"],
    help="The survey data file — same format as the original Cipla learning survey export",
    label_visibility="collapsed",
)

sheet_name = st.text_input(
    "Sheet name (leave blank to use first sheet)",
    value="",
    placeholder="e.g. Data",
    help="If your Excel has multiple sheets, enter the sheet name here",
)

st.markdown("""
<div class="privacy-note">
    ✅ <strong>Privacy:</strong> This file is processed entirely in your browser session's memory.
    It is never written to disk, never stored in a database, and never transmitted to any third party.
    When you close this tab, all data is automatically cleared.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EXPECTED COLUMNS INFO
# ─────────────────────────────────────────────
with st.expander("📋 Expected Column Names (click to expand)"):
    st.markdown("""
The app will auto-detect columns using flexible matching. For best results, your Excel should contain columns similar to:

| Column | Examples of accepted names |
|--------|---------------------------|
| Cluster / Therapy Area | `Cluster`, `Therapy Area` |
| Sub Department | `Sub Dept 2`, `SubDept2` |
| Role / Designation | `Role`, `Designation` |
| Metro / Non-Metro | `Metro`, `Metro/Non Metro` |
| Employee Status | `Employee Status`, `Emp Status` |
| Learning Motivation | `Learning Motivation`, `Motivation` |
| Preferred Content Format | `Preferred Content Format`, `Format Preference` |
| Learning Style | `Learning Style`, `Style Preference` |
| Time Willing to Spend | `Time Willing`, `Time Available` |
| Platform Frequency | `Digital Platform Frequency`, `Frequency` |
| Challenges | `Challenges`, `Access Challenge` |
| Development Needs | `Professional Development`, `Dev Needs` |
| Experience in Role | `Experience`, `Years in Role` |
| Education | `Education`, `Qualification` |

**Ranked columns** should be semicolon-separated with Rank 1 first: `Career advancement;Personal growth;Job performance`
**Multi-select columns** (challenges, dev needs) can be semicolon or comma separated.
    """)

# ─────────────────────────────────────────────
# GENERATE BUTTON
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate = st.button(
        "🚀 Generate Dashboard",
        use_container_width=True,
        type="primary",
        disabled=uploaded_file is None,
    )

# ─────────────────────────────────────────────
# PROCESSING
# ─────────────────────────────────────────────
if generate and uploaded_file is not None:
    try:
        # Read Excel
        with st.spinner("Reading Excel file..."):
            if sheet_name.strip():
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name.strip())
            else:
                df = pd.read_excel(uploaded_file, sheet_name=0)

        st.success(f"✓ Loaded {len(df):,} rows and {len(df.columns)} columns")

        # Show column preview
        with st.expander("Detected columns (click to verify)"):
            st.write(list(df.columns))

        # Process data
        with st.spinner("Assigning learner persona types... (this may take 15–30 seconds for large files)"):
            payload = process(df)

        st.success(
            f"✓ Processed {payload['total_n']:,} learners across "
            f"{len(payload['roles'])} roles and "
            f"{len(payload['clusters'])} clusters"
        )

        # Show persona distribution summary
        if "precomputed" in payload and "overall" in payload["precomputed"]:
            overall = payload["precomputed"]["overall"]
            st.markdown("**Persona type distribution:**")
            cols = st.columns(5)
            for i, pt in enumerate(overall["persona_dist"]):
                with cols[i % 5]:
                    pt_info = payload["persona_types"].get(pt["name"], {})
                    st.metric(
                        label=pt_info.get("emoji", "") + " " + pt["name"],
                        value=f"{pt['pct']}%",
                        delta=f"{pt['count']:,} learners",
                        delta_color="off",
                    )

        # Build HTML
        with st.spinner("Building dashboard HTML..."):
            template_path = os.path.join(os.path.dirname(__file__), "template.html")
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            data_json = json.dumps(payload, ensure_ascii=False, default=str)
            html_output = template.replace("__CIPLA_DATA__", data_json)

        st.success("✓ Dashboard ready!")

        # Download button
        st.markdown("---")
        st.markdown("### 📥 Download Your Dashboard")
        st.markdown(
            "The dashboard is a single HTML file. Open it in any browser. "
            "Share it with trainers — no internet connection needed to view it."
        )

        st.download_button(
            label="⬇️  Download Dashboard HTML",
            data=html_output.encode("utf-8"),
            file_name="cipla_learner_persona_dashboard.html",
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

        st.info(
            "💡 **Tip:** After downloading, open the file in Chrome or Edge for the best experience. "
            "The file works completely offline — no internet needed."
        )

    except Exception as e:
        st.error(f"Something went wrong while processing the file.")
        with st.expander("Error details (share with your L&D tech team if needed)"):
            st.code(traceback.format_exc())
        st.markdown("""
        **Common fixes:**
        - Make sure the sheet name is correct (check the expander above for expected columns)
        - Ensure the file is not password-protected
        - Try saving the Excel as `.xlsx` format if it is in `.xls`
        """)

elif uploaded_file is None and generate:
    st.warning("Please upload an Excel file first.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#7589a8;padding:8px'>"
    "Cipla L&D · Learner Persona Dashboard · Data processed in-session only · Never stored"
    "</div>",
    unsafe_allow_html=True,
)
