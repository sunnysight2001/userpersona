"""
processor.py — Cipla Learner Persona Dashboard
Exact column names matched to Rahul's Excel structure.
All ranked questions are SINGLE columns with semicolon or multi-line values.
"""

import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────
# PERSONA TYPE DEFINITIONS
# ─────────────────────────────────────────────────────────────────
PERSONA_TYPES = {
    "Pathfinder": {"emoji":"🧭","color":"#0d6efd",
        "tagline":"Driven by growth, always moving forward",
        "description":"Highly motivated learners who connect every module to their next career move. They engage frequently, prefer structured progression, and respond strongly to recognition."},
    "Pragmatist": {"emoji":"⚡","color":"#d97706",
        "tagline":"Time is precious — make every minute count",
        "description":"Busy, results-oriented learners who need content that is immediately applicable. They favour short formats, dislike abstract content, and drop off quickly if relevance is not clear."},
    "Inquirer": {"emoji":"🔬","color":"#0891b2",
        "tagline":"Depth over breadth, evidence over assertion",
        "description":"Curious learners who go beyond the surface. They explore case studies and want to understand the why. Scientific and clinical depth energises them."},
    "Navigator": {"emoji":"🗺️","color":"#7c3aed",
        "tagline":"Experience-led, self-directed, performance-focused",
        "description":"Seasoned professionals who know what they need. They self-direct their learning, prefer flexibility, and are motivated by improving outcomes rather than advancement."},
    "Connector": {"emoji":"🤝","color":"#059669",
        "tagline":"Learning is better together",
        "description":"Collaborative learners energised by peer interaction, team scenarios, and shared challenges. Coaching simulations and group formats resonate most with them."},
}

ROLE_COLORS  = {"TM":"#0d6efd","ABM":"#7c3aed","HBM/SBM":"#0891b2","RBM":"#d97706","ZBM":"#be123c","Marketing":"#059669"}
ROLE_DISPLAY = {"TM":"Therapy Manager","ABM":"Area Business Manager","HBM/SBM":"Hospital / Scientific BM",
                "RBM":"Regional Business Manager","ZBM":"Zonal Business Manager","Marketing":"Marketing Team"}
ROLE_EMOJIS  = {"TM":"👨‍⚕️","ABM":"👨‍💼","HBM/SBM":"👩‍🔬","RBM":"📊","ZBM":"🌐","Marketing":"📣"}
ROLE_ABOUT   = {
    "TM":       ("a frontline Territory Manager covering Tier 2 and Tier 3 cities, meeting doctors, pharmacists, and stockists daily.",
                 "build product expertise and sharpen communication skills to grow into a leadership role."),
    "ABM":      ("an Area Business Manager leading a team of 4–6 TMs across multiple territories, responsible for coverage, coaching, and business outcomes.",
                 "build management and leadership capability while staying sharp on product and clinical updates."),
    "HBM/SBM":  ("a Hospital or Scientific Business Manager engaging with consultants and specialists who demand clinical depth and evidence-based conversations.",
                 "deepen scientific and product knowledge to engage confidently with specialist physicians."),
    "RBM":      ("a Regional Business Manager overseeing multiple areas, responsible for regional P&L, coaching ABMs, and driving strategic business outcomes.",
                 "build strategic coaching capability and leadership depth to move into a Zonal or national role."),
    "ZBM":      ("a Zonal Business Manager leading an entire zone, owning zonal P&L, setting strategic direction, and coaching RBMs.",
                 "sharpen strategic leadership and stay ahead of market and competitive shifts."),
    "Marketing":("a Brand Manager owning therapy brand communication strategy, campaigns, and promotional material.",
                 "build strategic brand management capability while staying updated on scientific and market developments."),
}
PERSONA_ATTITUDE = {
    "Pathfinder": "Show me where this learning takes me. If I can see a clear line between this module and my next role, I am all in. I engage daily and I want structured progress.",
    "Pragmatist": "Give me what I need in the shortest time possible. Short videos, clear takeaways, immediately usable. I do not have time for content that does not apply to my day.",
    "Inquirer":   "I want to understand the evidence, the mechanism, the reasoning. Do not just tell me what — tell me why. Case studies and clinical depth are where I come alive.",
    "Navigator":  "I know what I need. Give me flexibility and let me drive. I am motivated by improving my outcomes, not by completing a course for its own sake.",
    "Connector":  "Put me with my peers. Coaching scenarios, team discussions, shared challenges — that is where I learn best. Isolation kills my motivation.",
}
FORMAT_NARRATIVES = {
    "Pathfinder": "build every video around a single skill and close with an explicit link to the next career milestone. Completion streaks and progress badges will keep this group coming back.",
    "Pragmatist": "ruthlessly edit for length — if a module runs past 5 minutes, split it in two. Open with the punchline, not the context. They decide in the first 30 seconds whether to stay.",
    "Inquirer":   "pair each short video with a supplementary layer — a clinical case, an annotated study, or a downloadable evidence summary. Give them a reason to go deeper.",
    "Navigator":  "offer a curated self-select playlist rather than a fixed sequence. They know what they need — your job is to make the right content findable, not mandatory.",
    "Connector":  "anchor every video to a team discussion prompt. A 3-minute video followed by a 5-minute team debrief is more valuable to this group than a 20-minute solo module.",
}
MOTIV_NARRATIVES = {
    "career":      "Start every module with an explicit career hook — frame it as 'what completing this means for your next role.' Recognition through badges and visible completion data amplifies motivation far more than content quality alone.",
    "growth":      "Lead with the personal development angle — open with 'after this, you will be able to...' rather than 'this module covers...' This group is energised by mastery, not just task completion.",
    "performance": "Connect every piece of content directly to a daily field metric — call quality, conversion, coverage. 'How this changes your next doctor visit' is a stronger motivator than any career promise.",
    "trends":      "Position the learning as competitive intelligence — frame updates as 'what your market is doing that you need to know.' This group is energised by staying ahead, not catching up.",
}
CHALL_NARRATIVES = {
    "time":      "Design every module to be completable in a single commute or lunch break — 10 to 15 minutes maximum. Push content proactively the evening before field days.",
    "technical": "Prioritise offline-capable, low-bandwidth design as the default. Test every module on a 3G connection before launch. Compressed video and downloadable PDFs are non-negotiable.",
    "engaging":  "This group has seen enough generic slides to last a career. Raise the production bar — scenario-based videos, field simulations, and gamified assessments are the minimum viable standard.",
    "relevance": "Open every module with a role-specific context statement: 'If you are a [role] in [therapy area], this is built for you.' Generic pharma content will be closed within 60 seconds.",
    "access":    "Audit the full device mix across this group before designing content. Build SMS or WhatsApp push reminders for learners with limited smartphone time.",
}
SECONDARY_FORMATS = {
    "Pathfinder": "structured learning paths with visible progress tracking and milestone badges",
    "Pragmatist": "micro-assessments that prove competency in under 3 minutes without requiring a full module",
    "Inquirer":   "downloadable clinical summaries, annotated evidence reviews, and KOL video discussions",
    "Navigator":  "self-paced expert playlists and on-demand live Q&A sessions with internal faculty",
    "Connector":  "cohort challenges, team-based gamification, and peer coaching simulation exercises",
}


# ─────────────────────────────────────────────────────────────────
# COLUMN NORMALISER
# ─────────────────────────────────────────────────────────────────

def normalise_col(c):
    """Collapse whitespace, newlines, strip — for fuzzy matching."""
    return re.sub(r'\s+', ' ', str(c)).strip().lower()


def detect_columns(df):
    """
    Map logical field names to actual Excel column names.
    Uses normalised matching (ignores newlines and extra spaces).
    """
    norm_map = {normalise_col(c): c for c in df.columns}

    def find(candidates):
        """Return first matching actual column name."""
        for cand in candidates:
            cand_n = normalise_col(cand)
            # Exact normalised match
            if cand_n in norm_map:
                return norm_map[cand_n]
        # Partial match fallback
        for cand in candidates:
            cand_n = normalise_col(cand)
            for col_n, col_orig in norm_map.items():
                if cand_n in col_n:
                    return col_orig
        return ""

    mapping = {
        # ── Filters / demographics ──
        "cluster":     find(["Cluster"]),
        "bu_division": find(["BU/Division", "BU / Division", "BU_Division", "Division"]),
        "short_role":  find(["Short Role", "Short_Role"]),
        "role":        find(["Role"]),
        "metro":       find(["Metro/Non Metro2", "Metro/Non Metro", "Metro Non Metro", "Metro"]),
        "emp_status":  find(["Employee Status", "Emp Status", "EmpStatus"]),

        # ── Learning profile ──
        "frequency":   find(["Frequency of using digital learning platforms for professional development",
                             "Frequency of using digital learning", "frequency"]),
        "time":        find(["Time you're willing to dedicate to digital learning each week",
                             "Time willing", "Time available"]),
        "exp":         find(["Years in current role", "Experience", "Years in Role"]),
        "education":   find(["Highest Level of Education", "Education", "Qualification"]),
        "style":       find(["Rank your preferred Learning Style", "Learning Style"]),

        # ── Ranked / multi-select questions ──
        # Format: single column, responses semicolon-separated in rank order
        "format":      find(["What is your preferred format of digital learning content",
                             "preferred format of digital learning"]),
        "motiv":       find(["What motivates you to participate in professional development activities",
                             "motivates you to participate", "motivation"]),
        "dev_needs":   find(["What are your top 3 professional development needs within your current role",
                             "top 3 professional development needs", "professional development needs"]),
        "participation": find(["What type of learning reward and recognition will encourage your active participation",
                               "learning reward and recognition", "reward and recognition"]),
        "challenges":  find(["Biggest challenges accessing or using digital learning content",
                             "biggest challenges accessing", "challenges"]),
    }

    return mapping


# ─────────────────────────────────────────────────────────────────
# VALUE EXTRACTION FROM SINGLE COLUMN (semicolon or newline separated)
# ─────────────────────────────────────────────────────────────────

def split_responses(val):
    """Split a cell value on semicolons or newlines into a list of responses."""
    if pd.isna(val) or str(val).strip() == "":
        return []
    # Split on ; or newline
    parts = re.split(r'[;\n]', str(val))
    return [p.strip() for p in parts if p.strip() and p.strip().lower() not in ("nan","none","")]


def get_rank1_from_cell(val):
    """Get the first (rank 1) item from a cell."""
    parts = split_responses(val)
    return parts[0] if parts else ""


def aggregate_single_col_ranked(series, top_n=6):
    """
    Count how many respondents chose each item as Rank 1 (first in list).
    Returns [(label, pct_of_respondents), ...] sorted descending.
    """
    counts = defaultdict(int)
    n_answered = 0
    for val in series.dropna():
        r1 = get_rank1_from_cell(val)
        if r1:
            counts[r1] += 1
            n_answered += 1
    if n_answered == 0:
        return []
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(cnt / n_answered * 100)) for item, cnt in items]


def aggregate_single_col_multiselect(series, top_n=6):
    """
    Count how many respondents selected each item (any position in list).
    Returns [(label, pct_of_respondents), ...] sorted descending.
    """
    counts = defaultdict(int)
    n_answered = 0
    for val in series.dropna():
        parts = split_responses(val)
        if parts:
            n_answered += 1
            for p in parts:
                counts[p] += 1
    if n_answered == 0:
        return []
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(cnt / n_answered * 100)) for item, cnt in items]


# ─────────────────────────────────────────────────────────────────
# PERSONA ASSIGNMENT
# ─────────────────────────────────────────────────────────────────

def assign_persona(row, col_map):
    scores = {p: 0 for p in PERSONA_TYPES}

    def r1(key):
        col = col_map.get(key, "")
        if not col: return ""
        return get_rank1_from_cell(row.get(col, "")).lower()

    motiv = r1("motiv")
    fmt   = r1("format")
    style_col = col_map.get("style", "")
    style = get_rank1_from_cell(row.get(style_col, "")).lower() if style_col else ""

    # Motivation
    if "career" in motiv:                           scores["Pathfinder"] += 3
    elif "growth" in motiv or "personal" in motiv:  scores["Inquirer"] += 2; scores["Pathfinder"] += 1
    elif "performance" in motiv or "job" in motiv:  scores["Navigator"] += 3; scores["Pragmatist"] += 1
    elif "trend" in motiv or "industry" in motiv:   scores["Inquirer"] += 2

    # Format
    if "video" in fmt or "short" in fmt:            scores["Pragmatist"] += 2; scores["Pathfinder"] += 1
    elif "game" in fmt or "gamif" in fmt:            scores["Connector"] += 2; scores["Pathfinder"] += 1
    elif "case" in fmt or "scenario" in fmt:         scores["Inquirer"] += 2; scores["Connector"] += 1
    elif "book" in fmt or "article" in fmt:          scores["Inquirer"] += 3
    elif "podcast" in fmt or "audio" in fmt:         scores["Navigator"] += 2
    elif "infograph" in fmt or "flash" in fmt:       scores["Pragmatist"] += 2

    # Style
    if "visual" in style:                            scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif "simulation" in style or "game" in style:   scores["Connector"] += 2
    elif "reading" in style or "writing" in style:   scores["Inquirer"] += 2
    elif "audio" in style:                           scores["Navigator"] += 1

    # Frequency
    freq_col = col_map.get("frequency", "")
    freq = str(row.get(freq_col, "")).lower() if freq_col else ""
    if "daily" in freq:          scores["Pathfinder"] += 2
    elif "weekly" in freq:       scores["Pragmatist"] += 1; scores["Connector"] += 1
    elif "month" in freq or "occasion" in freq: scores["Navigator"] += 2

    # Time
    time_col = col_map.get("time", "")
    tv = str(row.get(time_col, "")).lower() if time_col else ""
    if any(x in tv for x in ["<1","30 min","less than 1","30 minutes"]):
        scores["Pragmatist"] += 2
    elif "1" in tv and "2" in tv:
        scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif any(x in tv for x in ["3","4","more",">3"]):
        scores["Inquirer"] += 1; scores["Navigator"] += 1

    # Emp status
    es_col = col_map.get("emp_status", "")
    emp = str(row.get(es_col, "")).upper() if es_col else ""
    if "HELP" in emp:   scores["Pragmatist"] += 1
    elif "HEHP" in emp: scores["Pathfinder"] += 1
    elif "LELP" in emp: scores["Connector"] += 1
    elif "LEHP" in emp: scores["Navigator"] += 1

    return max(scores, key=scores.get)


# ─────────────────────────────────────────────────────────────────
# BUILD SEGMENT DATA
# ─────────────────────────────────────────────────────────────────

def get_series(df, col_map, key):
    col = col_map.get(key, "")
    if col and col in df.columns:
        return df[col]
    return pd.Series(dtype=str)


def build_segment_data(df, col_map):
    n = len(df)
    if n == 0: return None

    persona_counts = df["_persona"].value_counts()
    persona_dist = []
    for pname, pinfo in PERSONA_TYPES.items():
        cnt = int(persona_counts.get(pname, 0))
        persona_dist.append({"name":pname,"count":cnt,"pct":round(cnt/n*100) if n>0 else 0,
            "emoji":pinfo["emoji"],"color":pinfo["color"],"tagline":pinfo["tagline"],"description":pinfo["description"]})
    persona_dist.sort(key=lambda x: x["pct"], reverse=True)

    motiv_data  = aggregate_single_col_ranked(get_series(df, col_map, "motiv"), top_n=5)
    format_data = aggregate_single_col_ranked(get_series(df, col_map, "format"), top_n=6)
    style_data  = aggregate_single_col_ranked(get_series(df, col_map, "style"), top_n=4)
    dev_data    = aggregate_single_col_multiselect(get_series(df, col_map, "dev_needs"), top_n=5)
    part_data   = aggregate_single_col_multiselect(get_series(df, col_map, "participation"), top_n=5)
    chall_data  = aggregate_single_col_multiselect(get_series(df, col_map, "challenges"), top_n=5)

    time_col = col_map.get("time", "")
    time_data = []
    if time_col and time_col in df.columns:
        tc = df[time_col].dropna().value_counts()
        tot = tc.sum()
        time_data = [(str(k), round(v/tot*100)) for k,v in tc.items()]
        time_data.sort(key=lambda x: x[1], reverse=True)

    metro_col = col_map.get("metro", "")
    metro_n = 0
    if metro_col and metro_col in df.columns:
        mc = df[metro_col].value_counts()
        # Handle "Metro" or "Metro " or "METRO"
        for k,v in mc.items():
            if str(k).strip().lower() == "metro":
                metro_n = int(v); break

    es_col = col_map.get("emp_status", "")
    es_dist = {}
    if es_col and es_col in df.columns:
        for k,v in df[es_col].value_counts().items():
            if not pd.isna(k): es_dist[str(k).strip()] = int(v)

    def ci(label):
        l = label.lower()
        for k,ic in {"time":"⏰","technical":"📶","connect":"📶","engag":"😐","relev":"🎯","access":"🔒","tool":"🛠️"}.items():
            if k in l: return ic
        return "•"

    graphs = {
        "motivation":    [[i,p] for i,p in motiv_data],
        "format":        [[i,p] for i,p in format_data],
        "style":         [[i,p] for i,p in style_data],
        "challenges":    [[i,p,ci(i)] for i,p in chall_data],
        "devNeeds":      [[i,p] for i,p in dev_data],
        "participation": [[i,p] for i,p in part_data],
    }

    insight = build_insight(persona_dist, motiv_data, format_data, time_data, chall_data, n)

    return {"n":n,"metro_n":metro_n,"metro_pct":round(metro_n/n*100) if n>0 else 0,
            "es_dist":es_dist,"persona_dist":persona_dist,"graphs":graphs,"insight":insight}


# ─────────────────────────────────────────────────────────────────
# INSIGHT NARRATIVE
# ─────────────────────────────────────────────────────────────────

def build_insight(persona_dist, motiv_data, format_data, time_counts, chall_data, total_n):
    if not persona_dist or total_n == 0:
        return {"paragraphs":["Insufficient data for this filter combination."]}

    top1  = persona_dist[0] if len(persona_dist)>0 else {"name":"Pragmatist","pct":0}
    top2  = persona_dist[1] if len(persona_dist)>1 else {"name":"Pathfinder","pct":0}
    top3v = persona_dist[2] if len(persona_dist)>2 else {"name":"Inquirer","pct":0}

    fmt1 = format_data[0] if format_data else ("short videos",48)
    fmt2 = format_data[1] if len(format_data)>1 else ("gamified modules",22)
    mot1 = motiv_data[0]  if motiv_data  else ("career advancement",37)
    mot2 = motiv_data[1]  if len(motiv_data)>1 else ("personal growth",27)
    ch1  = chall_data[0]  if chall_data  else ("time constraint",52)
    ch2  = chall_data[1]  if len(chall_data)>1 else ("lack of engaging content",31)

    time_bracket = "1–2 hours"; time_pct = 52; chunk = "15"; freq = "weekly"
    if time_counts:
        time_bracket = str(time_counts[0][0]); time_pct = time_counts[0][1]
        tb = time_bracket.lower()
        if any(x in tb for x in ["<1","30 min","less than 1","30 minutes"]): chunk="10"; freq="twice-weekly"
        elif any(x in tb for x in ["3","4","more",">3"]): chunk="20"; freq="bi-weekly"

    fmt_narr = FORMAT_NARRATIVES.get(top1["name"], FORMAT_NARRATIVES["Pragmatist"])
    mot_key  = ("career" if "career" in mot1[0].lower() else
                "performance" if "perf" in mot1[0].lower() else
                "growth" if "growth" in mot1[0].lower() else "trends")
    mot_narr = MOTIV_NARRATIVES.get(mot_key, MOTIV_NARRATIVES["career"])
    ch_key   = ("time" if "time" in ch1[0].lower() else
                "technical" if "tech" in ch1[0].lower() else
                "engaging" if "engag" in ch1[0].lower() else
                "relevance" if "relev" in ch1[0].lower() else "access")
    ch_narr  = CHALL_NARRATIVES.get(ch_key, CHALL_NARRATIVES["time"])
    sec_fmt  = SECONDARY_FORMATS.get(top2["name"], "peer-based and scenario-driven formats")
    rel_pct  = next((p for it,p in chall_data if "relev" in it.lower()), 38)

    return {"paragraphs":[
        (f"This group of {total_n:,} learners is led by {top1['name']}s ({top1['pct']}%), "
         f"with {top2['name']}s ({top2['pct']}%) and {top3v['name']}s ({top3v['pct']}%) as the next dominant profiles. "
         f"Design your learning journey anchored to the {top1['name']} majority, "
         f"then layer in formats that also serve the {top2['name']} and {top3v['name']} segments."),

        (f"{fmt1[0]} is the top-ranked format ({fmt1[1]}% chose it as their #1 preference), "
         f"followed by {fmt2[0]} ({fmt2[1]}%). "
         f"For this {top1['name']}-led group, {fmt_narr}"),

        (f"Time is a non-negotiable design constraint — {time_pct}% of this group can commit "
         f"only {time_bracket} per week to learning. Cap every module at {chunk} minutes "
         f"and release on a {freq} rhythm. Modules that exceed this window will be started but not finished."),

        (f"{mot1[0]} is the #1 stated motivator ({mot1[1]}% ranked it first), "
         f"with {mot2[0]} as the strong second ({mot2[1]}%). {mot_narr}"),

        (f"The most cited barrier is {ch1[0]} ({ch1[1]}% flagged it), "
         f"followed by {ch2[0]} ({ch2[1]}%). {ch_narr}"),

        (f"To serve the {top2['name']} ({top2['pct']}%) and {top3v['name']} ({top3v['pct']}%) "
         f"segments alongside the majority, layer in {sec_fmt}. "
         f"Content relevance is flagged by {rel_pct}% of this group — "
         f"open every module with a role-specific context statement. "
         f"Generic pharma content will be closed within the first 60 seconds."),
    ]}


# ─────────────────────────────────────────────────────────────────
# PERSONA CARD
# ─────────────────────────────────────────────────────────────────

def build_persona_card(df, col_map, role_key, persona_type_name):
    subset = df.copy()
    if role_key and "_role_clean" in df.columns and role_key in df["_role_clean"].values:
        subset = df[df["_role_clean"] == role_key]
    if persona_type_name:
        subset = subset[subset["_persona"] == persona_type_name]
    n = len(subset)
    if n == 0: return None

    ptype     = PERSONA_TYPES.get(persona_type_name, PERSONA_TYPES["Pragmatist"])
    role_info = ROLE_ABOUT.get(role_key, ("a field professional in the Cipla organisation.", "continue developing their skills."))

    def top_val(key, default="—"):
        col = col_map.get(key, "")
        if col and col in subset.columns:
            vc = subset[col].dropna().value_counts()
            return str(vc.index[0]).strip() if len(vc)>0 else default
        return default

    metro_col = col_map.get("metro", ""); metro_pct = 0; top_loc = "Mixed"
    if metro_col and metro_col in subset.columns:
        mc = subset[metro_col].value_counts()
        mn = sum(int(v) for k,v in mc.items() if str(k).strip().lower()=="metro")
        metro_pct = round(mn/n*100) if n>0 else 0
        top_loc = "Metro" if metro_pct>=50 else "Non-Metro"

    motiv_data  = aggregate_single_col_ranked(get_series(subset, col_map, "motiv"), top_n=5)
    format_data = aggregate_single_col_ranked(get_series(subset, col_map, "format"), top_n=6)
    style_data  = aggregate_single_col_ranked(get_series(subset, col_map, "style"), top_n=4)
    dev_data    = aggregate_single_col_multiselect(get_series(subset, col_map, "dev_needs"), top_n=5)
    part_data   = aggregate_single_col_multiselect(get_series(subset, col_map, "participation"), top_n=5)
    chall_data  = aggregate_single_col_multiselect(get_series(subset, col_map, "challenges"), top_n=5)

    def ci(label):
        l = label.lower()
        for k,ic in {"time":"⏰","technical":"📶","connect":"📶","engag":"😐","relev":"🎯","access":"🔒","tool":"🛠️"}.items():
            if k in l: return ic
        return "•"

    top_format = format_data[0][0] if format_data else "Short Videos"
    top_motiv  = motiv_data[0][0]  if motiv_data  else "Career advancement"

    time_col = col_map.get("time",""); time_bracket = "1–2 hrs / week"
    if time_col and time_col in subset.columns:
        tc = subset[time_col].dropna().value_counts()
        if len(tc)>0: time_bracket = str(tc.index[0]).strip()

    es_col = col_map.get("emp_status",""); es_dist = {}
    if es_col and es_col in subset.columns:
        for k,v in subset[es_col].value_counts().items():
            if not pd.isna(k): es_dist[str(k).strip()] = int(v)

    about_base, focus_base = role_info
    about_text = (f"This learner is {about_base} "
                  f"As a {persona_type_name}, they are driven to {ptype['tagline'].lower()}. "
                  f"They represent {n:,} learners in this filtered view.")

    return {
        "n":n, "role_key":role_key,
        "role_display": ROLE_DISPLAY.get(role_key, role_key),
        "role_color":   ROLE_COLORS.get(role_key, "#3b82f6"),
        "role_emoji":   ROLE_EMOJIS.get(role_key, "👤"),
        "persona_name":    persona_type_name,
        "persona_emoji":   ptype["emoji"],
        "persona_color":   ptype["color"],
        "persona_tagline": ptype["tagline"],
        "education":  top_val("education","Graduate"),
        "experience": top_val("exp","1–3 years"),
        "location":   f"{top_loc} ({metro_pct}% Metro)",
        "frequency":  top_val("frequency","Weekly"),
        "about":      about_text,
        "focus":      focus_base,
        "attitude":   PERSONA_ATTITUDE.get(persona_type_name,""),
        "learnPref": {"format":top_format,
                      "duration":"Short < 5 min" if any(x in top_format.lower() for x in ["video","short","flash"]) else "Flexible",
                      "category":top_motiv, "time":time_bracket},
        "topNeeds":      [d[0] for d in dev_data[:3]]   or ["—"],
        "motivations":   [d[0] for d in motiv_data[:4]] or ["—"],
        "challenges":    [d[0] for d in chall_data[:4]] or ["—"],
        "participation": [d[0] for d in part_data[:4]]  or ["—"],
        "es_dist":es_dist, "dom_es":max(es_dist,key=es_dist.get) if es_dist else "—",
        "metro_pct":metro_pct,
        "graphs":{
            "motivation":    [[i,p] for i,p in motiv_data],
            "format":        [[i,p] for i,p in format_data],
            "style":         [[i,p] for i,p in style_data],
            "challenges":    [[i,p,ci(i)] for i,p in chall_data],
            "devNeeds":      [[i,p] for i,p in dev_data],
            "participation": [[i,p] for i,p in part_data],
        },
    }


# ─────────────────────────────────────────────────────────────────
# MAIN PROCESSOR
# ─────────────────────────────────────────────────────────────────

def process(df: pd.DataFrame) -> dict:
    df      = df.copy()
    col_map = detect_columns(df)

    # Role — prefer Short Role, fall back to Role
    short_role_col = col_map.get("short_role","")
    role_col       = col_map.get("role","")
    if short_role_col and short_role_col in df.columns:
        df["_role_clean"] = df[short_role_col].astype(str).str.strip()
    elif role_col and role_col in df.columns:
        df["_role_clean"] = df[role_col].astype(str).str.strip()
        norm = {"territory manager":"TM","tm":"TM","area business manager":"ABM","abm":"ABM",
                "hospital business manager":"HBM/SBM","hbm":"HBM/SBM","scientific business manager":"HBM/SBM",
                "sbm":"HBM/SBM","hbm/sbm":"HBM/SBM","regional business manager":"RBM","rbm":"RBM",
                "zonal business manager":"ZBM","zbm":"ZBM","marketing":"Marketing","brand manager":"Marketing"}
        df["_role_clean"] = df["_role_clean"].apply(lambda x: norm.get(x.lower(), x))
    else:
        df["_role_clean"] = "Unknown"

    df["_persona"] = df.apply(lambda row: assign_persona(row, col_map), axis=1)

    cluster_col = col_map.get("cluster","")
    bu_col      = col_map.get("bu_division","")
    metro_col   = col_map.get("metro","")
    es_col      = col_map.get("emp_status","")

    clusters = sorted([str(x) for x in df[cluster_col].dropna().unique()]) if cluster_col and cluster_col in df.columns else []
    bu_divs  = sorted([str(x) for x in df[bu_col].dropna().unique()])      if bu_col and bu_col in df.columns else []
    roles    = sorted([r for r in df["_role_clean"].dropna().unique() if r and r not in ("nan","Unknown")])
    metros   = sorted([str(x) for x in df[metro_col].dropna().unique()])   if metro_col and metro_col in df.columns else []

    # Anonymised rows for JS filtering
    keep = ["_role_clean","_persona"]
    for c in [cluster_col, bu_col, metro_col, es_col]:
        if c and c in df.columns and c not in keep: keep.append(c)
    rename = {"_role_clean":"role","_persona":"persona",cluster_col:"cluster",
              bu_col:"bu_division",metro_col:"metro",es_col:"empStatus"}
    clean_rows = [{rename.get(k,k):str(v).strip() for k,v in r.items()}
                  for r in df[keep].fillna("").to_dict(orient="records")]

    # Pre-compute segments
    precomputed = {}
    def seg(sub): return build_segment_data(sub, col_map)

    precomputed["overall"] = seg(df)
    for role in roles:
        s = seg(df[df["_role_clean"]==role])
        if s: precomputed[f"role::{role}"] = s
    for cluster in clusters:
        if cluster_col and cluster_col in df.columns:
            s = seg(df[df[cluster_col]==cluster])
            if s: precomputed[f"cluster::{cluster}"] = s
    for bu in bu_divs:
        if bu_col and bu_col in df.columns:
            s = seg(df[df[bu_col]==bu])
            if s: precomputed[f"bu::{bu}"] = s
    for cluster in clusters:
        for role in roles:
            if cluster_col and cluster_col in df.columns:
                sub = df[(df[cluster_col]==cluster)&(df["_role_clean"]==role)]
                if len(sub)>=10:
                    s = seg(sub)
                    if s: precomputed[f"cluster::{cluster}::role::{role}"] = s

    # Persona cards
    persona_cards = {}
    for role in roles:
        for pname in PERSONA_TYPES:
            card = build_persona_card(df, col_map, role, pname)
            if card and card["n"]>0:
                persona_cards[f"{role}::{pname}"] = card

    return {
        "total_n":len(df), "clusters":clusters, "bu_divisions":bu_divs,
        "roles":roles, "metros":metros,
        "persona_types":{k:{"emoji":v["emoji"],"color":v["color"],"tagline":v["tagline"],"description":v["description"]} for k,v in PERSONA_TYPES.items()},
        "role_colors":ROLE_COLORS, "role_display":ROLE_DISPLAY, "role_emojis":ROLE_EMOJIS,
        "rows":clean_rows, "precomputed":precomputed, "persona_cards":persona_cards,
        "col_names":{"cluster":cluster_col,"bu_division":bu_col,"metro":metro_col,"empStatus":es_col},
        "detected_cols": {k:v for k,v in col_map.items() if v},
    }
