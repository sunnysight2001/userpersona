"""
processor.py
Cipla Learner Persona Dashboard — Data Processing Engine

Reads the uploaded Excel, assigns each respondent a persona type,
computes all filter combinations, and builds the full data payload
that gets injected into the HTML template.
"""

import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────

PERSONA_TYPES = {
    "Pathfinder": {
        "emoji": "🧭",
        "color": "#0d6efd",
        "tagline": "Driven by growth, always moving forward",
        "description": "Highly motivated learners who connect every module to their next career move. They engage frequently, prefer structured progression, and respond strongly to recognition.",
    },
    "Pragmatist": {
        "emoji": "⚡",
        "color": "#d97706",
        "tagline": "Time is precious — make every minute count",
        "description": "Busy, results-oriented learners who need content that is immediately applicable. They favour short formats, dislike abstract content, and drop off quickly if relevance is not clear.",
    },
    "Inquirer": {
        "emoji": "🔬",
        "color": "#0891b2",
        "tagline": "Depth over breadth, evidence over assertion",
        "description": "Curious learners who go beyond the surface. They read, explore case studies, and want to understand the 'why'. Scientific and clinical depth energises them.",
    },
    "Navigator": {
        "emoji": "🗺️",
        "color": "#7c3aed",
        "tagline": "Experience-led, self-directed, performance-focused",
        "description": "Seasoned professionals who know what they need. They self-direct their learning, prefer flexibility, and are motivated by improving outcomes rather than advancement.",
    },
    "Connector": {
        "emoji": "🤝",
        "color": "#059669",
        "tagline": "Learning is better together",
        "description": "Collaborative learners energised by peer interaction, team scenarios, and shared challenges. Coaching simulations and group formats resonate most with them.",
    },
}

ROLE_COLORS = {
    "TM":        "#0d6efd",
    "ABM":       "#7c3aed",
    "HBM/SBM":   "#0891b2",
    "RBM":       "#d97706",
    "ZBM":       "#be123c",
    "Marketing": "#059669",
}

ROLE_DISPLAY = {
    "TM":        "Therapy Manager",
    "ABM":       "Area Business Manager",
    "HBM/SBM":   "Hospital / Scientific BM",
    "RBM":       "Regional Business Manager",
    "ZBM":       "Zonal Business Manager",
    "Marketing": "Marketing Team",
}

ROLE_EMOJIS = {
    "TM": "👨‍⚕️", "ABM": "👨‍💼", "HBM/SBM": "👩‍🔬",
    "RBM": "📊",  "ZBM": "🌐",  "Marketing": "📣",
}

# Persona archetype descriptions per role (for the card narrative)
ROLE_ABOUT = {
    "TM":        ("a frontline Territory Manager covering Tier 2 and Tier 3 cities, meeting doctors, pharmacists, and stockists daily. Territory performance is directly tied to product knowledge and communication effectiveness.",
                  "build product expertise and sharpen communication skills to grow into a leadership role."),
    "ABM":       ("an Area Business Manager leading a team of 4–6 TMs across multiple territories, responsible for coverage, coaching, and business outcomes.",
                  "build management and leadership capability while staying sharp on product and clinical updates."),
    "HBM/SBM":   ("a Hospital or Scientific Business Manager engaging with consultants, intensivists, and specialists who demand clinical depth and evidence-based conversations.",
                  "deepen scientific and product knowledge to engage confidently with specialist physicians."),
    "RBM":       ("a Regional Business Manager overseeing multiple areas, responsible for regional P&L, coaching ABMs, and driving strategic business outcomes.",
                  "build strategic coaching capability and leadership depth to move into a Zonal or national role."),
    "ZBM":       ("a Zonal Business Manager leading an entire zone, owning zonal P&L, setting strategic direction, and coaching RBMs across multiple regions.",
                  "sharpen strategic leadership and stay ahead of market and competitive shifts."),
    "Marketing": ("a Brand Manager owning therapy brand communication strategy, campaigns, and promotional material — collaborating with medical, regulatory, and sales teams.",
                  "build strategic brand management capability while staying updated on scientific and market developments."),
}

PERSONA_ATTITUDE = {
    "Pathfinder":  "Show me where this learning takes me. If I can see a clear line between this module and my next role, I am all in. I engage daily and I want structured progress.",
    "Pragmatist":  "Give me what I need in the shortest time possible. Short videos, clear takeaways, immediately usable. I do not have time for content that does not apply to my day.",
    "Inquirer":    "I want to understand the evidence, the mechanism, the reasoning. Do not just tell me what — tell me why. Case studies and clinical depth are where I come alive.",
    "Navigator":   "I know what I need. Give me flexibility and let me drive. I am motivated by improving my outcomes, not by completing a course for its own sake.",
    "Connector":   "Put me with my peers. Coaching scenarios, team discussions, shared challenges — that is where I learn best. Isolation kills my motivation.",
}

# Narrative insight templates — filled with computed values
INSIGHT_TEMPLATES = {
    "opening": (
        "The {role_display} population in this view ({total_n} learners) is shaped by "
        "{top1_name}s ({top1_pct}%), {top2_name}s ({top2_pct}%), and {top3_name}s ({top3_pct}%) as the three dominant learning profiles. "
        "Any learning journey designed for this group must serve this blend — not just the majority type."
    ),
    "format": (
        "On content format, {format1} is the clear first choice ({format1_pct}% ranked it #1), followed by {format2} ({format2_pct}%). "
        "Given the {top1_name} majority, {format_narrative}"
    ),
    "time": (
        "Time availability is a real constraint — {time_pct}% of this group can commit only {time_bracket} per week. "
        "Design learning in chunks of {chunk_size} minutes maximum, batched into a {batch_freq} rhythm."
    ),
    "motivation": (
        "The primary motivator is {motiv1} ({motiv1_pct}% rank it #1), with {motiv2} close behind ({motiv2_pct}%). "
        "{motiv_narrative}"
    ),
    "challenge": (
        "The biggest barrier to engagement is {chall1} ({chall1_pct}% flagged it), followed by {chall2} ({chall2_pct}%). "
        "{chall_narrative}"
    ),
    "closing": (
        "For the {top2_name} and {top3_name} segments, layer in {secondary_formats}. "
        "Avoid generic content — {relevance_note}"
    ),
}

FORMAT_NARRATIVES = {
    "Pathfinder":  "keep videos punchy and tie every module explicitly to role progression milestones.",
    "Pragmatist":  "ruthlessly edit for length — if it runs past 5 minutes, break it into two modules.",
    "Inquirer":    "pair short videos with supplementary reading and clinical case discussions.",
    "Navigator":   "offer a curated playlist they can self-navigate rather than a linear mandatory path.",
    "Connector":   "anchor each video to a team discussion prompt or coaching scenario.",
}

MOTIV_NARRATIVES = {
    "career":     "Frame every module with explicit career progression language — 'What this means for your next role.' Badges and completion certificates amplify this group's motivation significantly.",
    "growth":     "Lead with the personal development angle — 'What you will be able to do differently.' This group responds to mastery, not just completion.",
    "performance":"Connect content directly to daily KPIs and field metrics. 'How this will change your next doctor call' is more powerful than any career promise.",
    "trends":     "Position learning as staying ahead of the market. Competitive intelligence, therapy updates, and industry context energise this group.",
}

CHALL_NARRATIVES = {
    "time":       "Combat this by pushing content proactively before field days and designing offline-capable modules. Never require connectivity at the point of learning.",
    "technical":  "Prioritise mobile-first, low-bandwidth design. Test every module on a 3G connection before launch. Offer downloadable offline versions.",
    "engaging":   "Invest in production quality — this group has seen enough generic slides. Scenario-based, visual, gamified formats are the minimum bar.",
    "relevance":  "Every module must open with a clear 'this is for you because...' statement. Generic pharma content will be abandoned in the first 60 seconds.",
    "access":     "Ensure modules work across device types. Build an SMS or WhatsApp nudge system for Non-Metro users with limited smartphone time.",
}

SECONDARY_FORMATS = {
    "Pathfinder":  "structured learning paths with visible progression tracking",
    "Pragmatist":  "micro-assessments that prove competency quickly without lengthy modules",
    "Inquirer":    "downloadable clinical summaries, white papers, and annotated evidence reviews",
    "Navigator":   "self-paced playlists and on-demand expert sessions",
    "Connector":   "peer cohort challenges, coaching simulations, and team-based gamification",
}


# ─────────────────────────────────────────────────────────────────
# COLUMN DETECTION
# ─────────────────────────────────────────────────────────────────

def detect_columns(df):
    """Flexibly detect column names regardless of exact naming."""
    cols = {c.lower().strip(): c for c in df.columns}
    mapping = {}

    patterns = {
        "cluster":     ["cluster"],
        "subdept2":    ["sub dept 2", "subdept2", "sub_dept_2", "sub dept2"],
        "role":        ["role", "designation"],
        "metro":       ["metro", "metro/non metro", "metro_nonmetro"],
        "emp_status":  ["employee status", "emp status", "empstatus", "status"],
        "motiv":       ["learning motivation", "motivation", "what motivates"],
        "format":      ["preferred content format", "content format", "format preference"],
        "style":       ["learning style", "style preference"],
        "time":        ["time willing", "time available", "hours per week", "time_willing"],
        "frequency":   ["digital platform frequency", "frequency", "how often"],
        "challenges":  ["challenges", "access challenge", "digital learning challenge"],
        "dev_needs":   ["professional development", "dev needs", "development need"],
        "exp":         ["experience", "years in role", "time in current role"],
        "education":   ["education", "qualification"],
    }

    for key, candidates in patterns.items():
        for cand in candidates:
            if cand in cols:
                mapping[key] = cols[cand]
                break
        # fallback: partial match
        if key not in mapping:
            for cand in candidates:
                for col_lower, col_orig in cols.items():
                    if cand in col_lower:
                        mapping[key] = col_orig
                        break
                if key in mapping:
                    break

    return mapping


# ─────────────────────────────────────────────────────────────────
# PERSONA ASSIGNMENT
# ─────────────────────────────────────────────────────────────────

def get_rank1(cell):
    """Extract rank-1 item from semicolon-separated ranked string."""
    if pd.isna(cell):
        return ""
    parts = str(cell).split(";")
    return parts[0].strip().lower() if parts else ""


def assign_persona(row, col_map):
    """
    Rule-based persona assignment scoring across 4 dimensions:
    1. Primary motivation (rank 1)
    2. Preferred format (rank 1)
    3. Learning frequency
    4. Time available per week
    Returns persona name string.
    """
    scores = {p: 0 for p in PERSONA_TYPES}

    # ── Motivation ──
    motiv = get_rank1(row.get(col_map.get("motiv", ""), ""))
    if "career" in motiv:
        scores["Pathfinder"] += 3
    elif "growth" in motiv or "personal" in motiv:
        scores["Inquirer"] += 2; scores["Pathfinder"] += 1
    elif "performance" in motiv or "job" in motiv:
        scores["Navigator"] += 3; scores["Pragmatist"] += 1
    elif "trend" in motiv or "industry" in motiv:
        scores["Inquirer"] += 2

    # ── Format preference ──
    fmt = get_rank1(row.get(col_map.get("format", ""), ""))
    if "video" in fmt or "short" in fmt:
        scores["Pragmatist"] += 2; scores["Pathfinder"] += 1
    elif "game" in fmt or "gamif" in fmt or "interact" in fmt:
        scores["Connector"] += 2; scores["Pathfinder"] += 1
    elif "case" in fmt or "scenario" in fmt:
        scores["Inquirer"] += 2; scores["Connector"] += 1
    elif "book" in fmt or "article" in fmt or "read" in fmt:
        scores["Inquirer"] += 3
    elif "podcast" in fmt or "audio" in fmt:
        scores["Navigator"] += 2

    # ── Learning style ──
    style = get_rank1(row.get(col_map.get("style", ""), ""))
    if "visual" in style:
        scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif "simulation" in style or "game" in style:
        scores["Connector"] += 2
    elif "reading" in style or "writing" in style:
        scores["Inquirer"] += 2
    elif "audio" in style:
        scores["Navigator"] += 1

    # ── Frequency ──
    freq = str(row.get(col_map.get("frequency", ""), "")).lower()
    if "daily" in freq:
        scores["Pathfinder"] += 2
    elif "weekly" in freq:
        scores["Pragmatist"] += 1; scores["Connector"] += 1
    elif "monthly" in freq or "occasional" in freq:
        scores["Navigator"] += 2

    # ── Time available ──
    time_val = str(row.get(col_map.get("time", ""), "")).lower()
    if "<1" in time_val or "less than 1" in time_val or "30" in time_val:
        scores["Pragmatist"] += 2
    elif "1-2" in time_val or "1 to 2" in time_val or "60" in time_val or "90" in time_val:
        scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif "3" in time_val or "more" in time_val or ">3" in time_val:
        scores["Inquirer"] += 1; scores["Navigator"] += 1

    # ── Emp status tiebreaker ──
    emp = str(row.get(col_map.get("emp_status", ""), "")).upper()
    if "HELP" in emp:
        scores["Pragmatist"] += 1
    elif "HEHP" in emp:
        scores["Pathfinder"] += 1
    elif "LELP" in emp:
        scores["Connector"] += 1
    elif "LEHP" in emp:
        scores["Navigator"] += 1

    return max(scores, key=scores.get)


# ─────────────────────────────────────────────────────────────────
# SAFE RANK EXTRACTION
# ─────────────────────────────────────────────────────────────────

def get_ranked_counts(series, top_n=6):
    """Count rank-1 responses from semicolon-separated ranked series."""
    counts = defaultdict(int)
    for val in series.dropna():
        parts = str(val).split(";")
        if parts:
            item = parts[0].strip()
            if item:
                counts[item] += 1
    total = sum(counts.values())
    if total == 0:
        return []
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(v / total * 100)) for item, v in sorted_items]


def get_multi_counts(series, top_n=6):
    """Count responses from multi-select (semicolon or comma separated)."""
    counts = defaultdict(int)
    for val in series.dropna():
        for part in re.split(r"[;,]", str(val)):
            item = part.strip()
            if item and len(item) > 1:
                counts[item] += 1
    total_respondents = series.notna().sum()
    if total_respondents == 0:
        return []
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(v / total_respondents * 100)) for item, v in sorted_items]


# ─────────────────────────────────────────────────────────────────
# BUILD SEGMENT DATA
# ─────────────────────────────────────────────────────────────────

def build_segment_data(df, col_map):
    """
    For a given (filtered) dataframe, compute:
    - persona type distribution
    - graph data (motivation, format, style, challenges, dev_needs, participation)
    - trainer insight narrative
    - summary stats
    """
    n = len(df)
    if n == 0:
        return None

    # Persona distribution
    persona_counts = df["_persona"].value_counts()
    persona_dist = []
    for pname, pinfo in PERSONA_TYPES.items():
        cnt = int(persona_counts.get(pname, 0))
        pct = round(cnt / n * 100) if n > 0 else 0
        persona_dist.append({
            "name": pname,
            "count": cnt,
            "pct": pct,
            "emoji": pinfo["emoji"],
            "color": pinfo["color"],
            "tagline": pinfo["tagline"],
            "description": pinfo["description"],
        })
    persona_dist.sort(key=lambda x: x["pct"], reverse=True)

    # Graph data
    motiv_data   = get_ranked_counts(df.get(col_map.get("motiv", "Never"), pd.Series(dtype=str)))
    format_data  = get_ranked_counts(df.get(col_map.get("format", "Never"), pd.Series(dtype=str)), top_n=6)
    style_data   = get_ranked_counts(df.get(col_map.get("style", "Never"), pd.Series(dtype=str)), top_n=4)
    chall_data   = get_multi_counts(df.get(col_map.get("challenges", "Never"), pd.Series(dtype=str)), top_n=5)
    dev_data     = get_multi_counts(df.get(col_map.get("dev_needs", "Never"), pd.Series(dtype=str)), top_n=5)

    # Time bracket
    time_series  = df.get(col_map.get("time", "Never"), pd.Series(dtype=str))
    time_counts  = get_ranked_counts(time_series, top_n=4)

    # Metro split
    metro_col = col_map.get("metro", "")
    if metro_col and metro_col in df.columns:
        metro_counts = df[metro_col].value_counts()
        metro_n  = int(metro_counts.get("Metro", 0))
        nmetro_n = n - metro_n
    else:
        metro_n = nmetro_n = 0

    # Emp status split
    es_col = col_map.get("emp_status", "")
    es_dist = {}
    if es_col and es_col in df.columns:
        for k, v in df[es_col].value_counts().items():
            es_dist[str(k)] = int(v)

    # Challenge icon map
    chall_icons = {"time": "⏰", "technical": "📶", "engaging": "😐",
                   "relevance": "🎯", "access": "🔒", "accessib": "🔒"}

    def chall_icon(label):
        l = label.lower()
        for k, ic in chall_icons.items():
            if k in l:
                return ic
        return "•"

    graphs = {
        "motivation":    [[item, pct] for item, pct in motiv_data],
        "format":        [[item, pct] for item, pct in format_data],
        "style":         [[item, pct] for item, pct in style_data],
        "challenges":    [[item, pct, chall_icon(item)] for item, pct in chall_data],
        "devNeeds":      [[item, pct] for item, pct in dev_data],
        "participation": [],  # derived below
    }

    # Trainer insight narrative
    insight = build_insight(persona_dist, motiv_data, format_data, time_counts, chall_data, n)

    return {
        "n": n,
        "metro_n": metro_n,
        "nmetro_n": nmetro_n,
        "metro_pct": round(metro_n / n * 100) if n > 0 else 0,
        "nmetro_pct": round(nmetro_n / n * 100) if n > 0 else 0,
        "es_dist": es_dist,
        "persona_dist": persona_dist,
        "graphs": graphs,
        "insight": insight,
    }


# ─────────────────────────────────────────────────────────────────
# INSIGHT NARRATIVE BUILDER
# ─────────────────────────────────────────────────────────────────

def build_insight(persona_dist, motiv_data, format_data, time_counts, chall_data, total_n):
    """Build narrative insight paragraphs from computed data."""
    if not persona_dist or total_n == 0:
        return {"paragraphs": ["Insufficient data to generate insights for this filter combination."]}

    top3 = persona_dist[:3]
    top1 = top3[0] if len(top3) > 0 else {"name": "—", "pct": 0}
    top2 = top3[1] if len(top3) > 1 else {"name": "—", "pct": 0}
    top3v = top3[2] if len(top3) > 2 else {"name": "—", "pct": 0}

    fmt1 = format_data[0] if format_data else ("short videos", 0)
    fmt2 = format_data[1] if len(format_data) > 1 else ("interactive modules", 0)
    mot1 = motiv_data[0] if motiv_data else ("career advancement", 0)
    mot2 = motiv_data[1] if len(motiv_data) > 1 else ("personal growth", 0)
    ch1  = chall_data[0] if chall_data else ("time constraint", 0)
    ch2  = chall_data[1] if len(chall_data) > 1 else ("technical difficulties", 0)

    # Time bracket
    time_bracket = "1–2 hours"
    time_pct = 52
    chunk_size = "15"
    batch_freq = "weekly"
    if time_counts:
        time_bracket = time_counts[0][0]
        time_pct = time_counts[0][1]
        if "<1" in time_bracket or "30" in time_bracket:
            chunk_size = "10"; batch_freq = "twice-weekly"
        elif "3" in time_bracket or "more" in time_bracket:
            chunk_size = "20"; batch_freq = "bi-weekly"

    # Pick narrative snippets
    fmt_narr  = FORMAT_NARRATIVES.get(top1["name"], FORMAT_NARRATIVES["Pragmatist"])
    mot_key   = "career" if "career" in mot1[0].lower() else \
                "performance" if "performance" in mot1[0].lower() else \
                "growth" if "growth" in mot1[0].lower() else "trends"
    mot_narr  = MOTIV_NARRATIVES.get(mot_key, MOTIV_NARRATIVES["career"])
    ch_key    = "time" if "time" in ch1[0].lower() else \
                "technical" if "tech" in ch1[0].lower() else \
                "engaging" if "engag" in ch1[0].lower() else \
                "relevance" if "relev" in ch1[0].lower() else "access"
    ch_narr   = CHALL_NARRATIVES.get(ch_key, CHALL_NARRATIVES["time"])
    sec_fmt   = SECONDARY_FORMATS.get(top2["name"], "peer-based and scenario-driven formats")
    rel_note  = "relevance is flagged by {r}% of this group — every module must open with a clear 'this is for you because' statement.".format(
        r=next((p for it, p in chall_data if "relev" in it.lower()), "40")
    )

    paragraphs = [
        # Opening
        "This group of {n} learners is shaped by {t1}s ({p1}%), {t2}s ({p2}%), and {t3}s ({p3}%) as the three dominant profiles. Any learning journey must serve this blend — design for the majority but do not ignore the other two.".format(
            n=total_n, t1=top1["name"], p1=top1["pct"],
            t2=top2["name"], p2=top2["pct"], t3=top3v["name"], p3=top3v["pct"]),

        # Format
        "{fmt1} is the clear first-choice format ({fp1}% ranked it #1), followed by {fmt2} ({fp2}%). Given the {t1} majority, {fn}".format(
            fmt1=fmt1[0], fp1=fmt1[1], fmt2=fmt2[0], fp2=fmt2[1],
            t1=top1["name"], fn=fmt_narr),

        # Time
        "Time is a real design constraint — {tp}% of this group can commit only {tb} per week. Build every module to a maximum of {cs} minutes, batched into a {bf} rhythm. Longer modules should offer clear pause-and-resume points.".format(
            tp=time_pct, tb=time_bracket, cs=chunk_size, bf=batch_freq),

        # Motivation
        "The primary motivator is {m1} ({mp1}% rank it #1), with {m2} close behind ({mp2}%). {mn}".format(
            m1=mot1[0], mp1=mot1[1], m2=mot2[0], mp2=mot2[1], mn=mot_narr),

        # Challenge
        "The biggest barrier to engagement is {c1} ({cp1}% flagged it), followed by {c2} ({cp2}%). {cn}".format(
            c1=ch1[0], cp1=ch1[1], c2=ch2[0], cp2=ch2[1], cn=ch_narr),

        # Closing
        "For the {t2} ({p2}%) and {t3} ({p3}%) segments, layer in {sf}. {rn}".format(
            t2=top2["name"], p2=top2["pct"], t3=top3v["name"], p3=top3v["pct"],
            sf=sec_fmt, rn=rel_note),
    ]

    return {"paragraphs": paragraphs}


# ─────────────────────────────────────────────────────────────────
# PER-PERSONA-TYPE CARD DATA
# ─────────────────────────────────────────────────────────────────

def build_persona_card(df, col_map, role_key, persona_type_name):
    """Build the detailed persona card data for a specific role + persona type combo."""
    subset = df.copy()
    if role_key and role_key in df.get("_role_clean", pd.Series(dtype=str)).values:
        subset = df[df["_role_clean"] == role_key]
    if persona_type_name:
        subset = subset[subset["_persona"] == persona_type_name]

    n = len(subset)
    if n == 0:
        return None

    ptype = PERSONA_TYPES.get(persona_type_name, PERSONA_TYPES["Pragmatist"])
    role_info = ROLE_ABOUT.get(role_key, ("a field professional in the Cipla organisation.", "continue developing their skills."))

    # Education
    edu_col = col_map.get("education", "")
    if edu_col and edu_col in subset.columns:
        edu_counts = subset[edu_col].value_counts()
        top_edu = edu_counts.index[0] if len(edu_counts) > 0 else "Graduate"
    else:
        top_edu = "Graduate"

    # Experience
    exp_col = col_map.get("exp", "")
    if exp_col and exp_col in subset.columns:
        exp_counts = subset[exp_col].value_counts()
        top_exp = str(exp_counts.index[0]) if len(exp_counts) > 0 else "1–3 years"
    else:
        top_exp = "1–3 years"

    # Metro
    metro_col = col_map.get("metro", "")
    if metro_col and metro_col in subset.columns:
        metro_counts = subset[metro_col].value_counts()
        metro_n = int(metro_counts.get("Metro", 0))
        metro_pct = round(metro_n / n * 100) if n > 0 else 0
        top_location = "Metro" if metro_pct >= 50 else "Non-Metro"
    else:
        top_location = "Mixed"; metro_pct = 0

    # Frequency
    freq_col = col_map.get("frequency", "")
    if freq_col and freq_col in subset.columns:
        freq_counts = subset[freq_col].value_counts()
        top_freq = str(freq_counts.index[0]) if len(freq_counts) > 0 else "Weekly"
    else:
        top_freq = "Weekly"

    # Graphs
    motiv_data  = get_ranked_counts(subset.get(col_map.get("motiv", "X"), pd.Series(dtype=str)))
    format_data = get_ranked_counts(subset.get(col_map.get("format", "X"), pd.Series(dtype=str)), top_n=6)
    style_data  = get_ranked_counts(subset.get(col_map.get("style", "X"), pd.Series(dtype=str)), top_n=4)
    chall_data  = get_multi_counts(subset.get(col_map.get("challenges", "X"), pd.Series(dtype=str)), top_n=5)
    dev_data    = get_multi_counts(subset.get(col_map.get("dev_needs", "X"), pd.Series(dtype=str)), top_n=5)

    chall_icons = {"time": "⏰", "technical": "📶", "engag": "😐", "relev": "🎯", "access": "🔒"}
    def chall_icon(label):
        l = label.lower()
        for k, ic in chall_icons.items():
            if k in l: return ic
        return "•"

    # Learning preference (top ranked)
    top_format   = format_data[0][0] if format_data else "Short Videos"
    top_motiv    = motiv_data[0][0] if motiv_data else "Career advancement"
    top_chall    = chall_data[0][0] if chall_data else "Time constraint"

    # Time bracket
    time_series = subset.get(col_map.get("time", "X"), pd.Series(dtype=str))
    time_counts = get_ranked_counts(time_series, top_n=1)
    time_bracket = time_counts[0][0] if time_counts else "1–2 hrs / week"

    # About narrative — combine role + persona type
    about_base, focus_base = role_info
    about_text = "This learner is {base} As a {ptype}, they are characterised by a drive to {tagline_lower}. They represent {n} of the learners in this filtered view.".format(
        base=about_base,
        ptype=persona_type_name,
        tagline_lower=ptype["tagline"].lower(),
        n=n,
    )
    focus_text = focus_base

    # Emp status
    es_col = col_map.get("emp_status", "")
    es_dist = {}
    if es_col and es_col in subset.columns:
        for k, v in subset[es_col].value_counts().items():
            es_dist[str(k)] = int(v)
    dom_es = max(es_dist, key=es_dist.get) if es_dist else "—"

    return {
        "n": n,
        "role_key": role_key,
        "role_display": ROLE_DISPLAY.get(role_key, role_key),
        "role_color": ROLE_COLORS.get(role_key, "#3b82f6"),
        "role_emoji": ROLE_EMOJIS.get(role_key, "👤"),
        "persona_name": persona_type_name,
        "persona_emoji": ptype["emoji"],
        "persona_color": ptype["color"],
        "persona_tagline": ptype["tagline"],
        "education": top_edu,
        "experience": top_exp,
        "location": top_location + " (" + str(metro_pct) + "% Metro)",
        "frequency": top_freq,
        "about": about_text,
        "focus": focus_text,
        "attitude": PERSONA_ATTITUDE.get(persona_type_name, ""),
        "learnPref": {
            "format": top_format,
            "duration": "Short < 5 min" if "video" in top_format.lower() or "short" in top_format.lower() else "Flexible",
            "category": top_motiv,
            "time": time_bracket,
        },
        "topNeeds": [d[0] for d in dev_data[:3]],
        "motivations": [d[0] for d in motiv_data[:4]],
        "challenges": [d[0] for d in chall_data[:4]],
        "es_dist": es_dist,
        "dom_es": dom_es,
        "metro_pct": metro_pct,
        "graphs": {
            "motivation":  [[item, pct] for item, pct in motiv_data],
            "format":      [[item, pct] for item, pct in format_data],
            "style":       [[item, pct] for item, pct in style_data],
            "challenges":  [[item, pct, chall_icon(item)] for item, pct in chall_data],
            "devNeeds":    [[item, pct] for item, pct in dev_data],
        },
    }


# ─────────────────────────────────────────────────────────────────
# MAIN PROCESSOR
# ─────────────────────────────────────────────────────────────────

def process(df: pd.DataFrame) -> dict:
    """
    Main entry point. Takes raw dataframe, returns full data payload.
    """
    df = df.copy()
    col_map = detect_columns(df)

    # ── Normalise role column ──
    role_col = col_map.get("role", "")
    if role_col and role_col in df.columns:
        df["_role_clean"] = df[role_col].astype(str).str.strip()
        # Normalise common variants
        role_norm = {
            "territory manager": "TM", "tm": "TM",
            "area business manager": "ABM", "abm": "ABM",
            "hospital business manager": "HBM/SBM", "hbm": "HBM/SBM",
            "scientific business manager": "HBM/SBM", "sbm": "HBM/SBM",
            "hbm/sbm": "HBM/SBM",
            "regional business manager": "RBM", "rbm": "RBM",
            "zonal business manager": "ZBM", "zbm": "ZBM",
            "marketing": "Marketing", "brand manager": "Marketing",
        }
        df["_role_clean"] = df["_role_clean"].apply(
            lambda x: role_norm.get(x.lower(), x)
        )
    else:
        df["_role_clean"] = "Unknown"

    # ── Assign persona type ──
    df["_persona"] = df.apply(lambda row: assign_persona(row, col_map), axis=1)

    # ── Filter options ──
    cluster_col  = col_map.get("cluster", "")
    subdept_col  = col_map.get("subdept2", "")
    metro_col    = col_map.get("metro", "")

    clusters  = sorted(df[cluster_col].dropna().unique().tolist()) if cluster_col and cluster_col in df.columns else []
    subdepts  = sorted(df[subdept_col].dropna().unique().tolist()) if subdept_col and subdept_col in df.columns else []
    roles     = sorted(df["_role_clean"].dropna().unique().tolist())
    metros    = sorted(df[metro_col].dropna().unique().tolist()) if metro_col and metro_col in df.columns else []

    # ── Pre-compute segment data for ALL filter combos ──
    # We pre-compute for: overall + each cluster + each role
    # The JS will then filter client-side using the full row-level data
    # Instead of pre-computing all combos (too much data), we embed the full
    # anonymised row-level data (persona + cluster + subdept + role + metro + empstatus)
    # and let JS compute on the fly.

    keep_cols = ["_role_clean", "_persona"]
    if cluster_col and cluster_col in df.columns:
        keep_cols.append(cluster_col)
    if subdept_col and subdept_col in df.columns:
        keep_cols.append(subdept_col)
    if metro_col and metro_col in df.columns:
        keep_cols.append(metro_col)
    es_col = col_map.get("emp_status", "")
    if es_col and es_col in df.columns:
        keep_cols.append(es_col)

    # Build anonymised rows (no PII — just categorical fields + persona)
    rows_data = df[keep_cols].fillna("").to_dict(orient="records")

    # Rename keys to standard names for JS
    col_rename = {
        "_role_clean": "role",
        "_persona": "persona",
        cluster_col: "cluster",
        subdept_col: "subdept2",
        metro_col: "metro",
        es_col: "empStatus",
    }
    clean_rows = []
    for row in rows_data:
        clean_row = {}
        for k, v in row.items():
            new_key = col_rename.get(k, k)
            clean_row[new_key] = str(v)
        clean_rows.append(clean_row)

    # ── Pre-compute graph data for overall + per role ──
    # This drives the graphs section (too slow to compute in JS)
    precomputed = {}

    def seg_key(cluster="", subdept="", role="", metro="", es=""):
        return json.dumps({"c": cluster, "s": subdept, "r": role, "m": metro, "e": es},
                          sort_keys=True)

    # Overall
    seg = build_segment_data(df, col_map)
    if seg:
        precomputed["overall"] = seg

    # Per role
    for role in roles:
        rdf = df[df["_role_clean"] == role]
        seg = build_segment_data(rdf, col_map)
        if seg:
            precomputed[f"role::{role}"] = seg

    # Per cluster
    for cluster in clusters:
        cdf = df[df[cluster_col] == cluster] if cluster_col and cluster_col in df.columns else pd.DataFrame()
        if len(cdf) > 0:
            seg = build_segment_data(cdf, col_map)
            if seg:
                precomputed[f"cluster::{cluster}"] = seg

    # Per cluster + role
    for cluster in clusters:
        for role in roles:
            cdf = df[(df[cluster_col] == cluster) & (df["_role_clean"] == role)] if cluster_col and cluster_col in df.columns else pd.DataFrame()
            if len(cdf) > 10:  # only meaningful segments
                seg = build_segment_data(cdf, col_map)
                if seg:
                    precomputed[f"cluster::{cluster}::role::{role}"] = seg

    # ── Build persona card data per role × persona type ──
    persona_cards = {}
    for role in roles:
        for pname in PERSONA_TYPES:
            card = build_persona_card(df, col_map, role, pname)
            if card and card["n"] > 0:
                persona_cards[f"{role}::{pname}"] = card

    return {
        "total_n": len(df),
        "clusters": clusters,
        "subdepts": subdepts,
        "roles": roles,
        "metros": metros,
        "persona_types": {k: {"emoji": v["emoji"], "color": v["color"],
                              "tagline": v["tagline"], "description": v["description"]}
                         for k, v in PERSONA_TYPES.items()},
        "role_colors": ROLE_COLORS,
        "role_display": ROLE_DISPLAY,
        "role_emojis": ROLE_EMOJIS,
        "rows": clean_rows,          # anonymised row-level data for JS filtering
        "precomputed": precomputed,  # pre-computed graph/insight data
        "persona_cards": persona_cards,
        "col_names": {
            "cluster": cluster_col,
            "subdept2": subdept_col,
            "metro": metro_col,
            "empStatus": es_col,
        },
    }
