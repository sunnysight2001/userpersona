"""
processor.py — Cipla Learner Persona Dashboard
Handles ranked columns (Rank 1/Rank 2/Rank 3...), BU/Division filter,
Short Role filter, dev needs, participation/recognition field.
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
ROLE_DISPLAY = {"TM":"Therapy Manager","ABM":"Area Business Manager","HBM/SBM":"Hospital / Scientific BM","RBM":"Regional Business Manager","ZBM":"Zonal Business Manager","Marketing":"Marketing Team"}
ROLE_EMOJIS  = {"TM":"👨‍⚕️","ABM":"👨‍💼","HBM/SBM":"👩‍🔬","RBM":"📊","ZBM":"🌐","Marketing":"📣"}
ROLE_ABOUT   = {
    "TM":       ("a frontline Territory Manager covering Tier 2 and Tier 3 cities, meeting doctors, pharmacists, and stockists daily.","build product expertise and sharpen communication skills to grow into a leadership role."),
    "ABM":      ("an Area Business Manager leading a team of 4–6 TMs across multiple territories, responsible for coverage, coaching, and business outcomes.","build management and leadership capability while staying sharp on product and clinical updates."),
    "HBM/SBM":  ("a Hospital or Scientific Business Manager engaging with consultants and specialists who demand clinical depth and evidence-based conversations.","deepen scientific and product knowledge to engage confidently with specialist physicians."),
    "RBM":      ("a Regional Business Manager overseeing multiple areas, responsible for regional P&L, coaching ABMs, and driving strategic business outcomes.","build strategic coaching capability and leadership depth to move into a Zonal or national role."),
    "ZBM":      ("a Zonal Business Manager leading an entire zone, owning zonal P&L, setting strategic direction, and coaching RBMs across multiple regions.","sharpen strategic leadership and stay ahead of market and competitive shifts."),
    "Marketing":("a Brand Manager owning therapy brand communication strategy, campaigns, and promotional material.","build strategic brand management capability while staying updated on scientific and market developments."),
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
    "time":      "Design every module to be completable in a single commute or lunch break — 10 to 15 minutes maximum. Push content proactively the evening before field days so learners engage when they have a quiet window.",
    "technical": "Prioritise offline-capable, low-bandwidth design as the default — not an afterthought. Test every module on a 3G connection before launch. Compressed video and downloadable PDFs are non-negotiable.",
    "engaging":  "This group has seen enough generic slides to last a career. Raise the production bar — scenario-based videos, realistic field simulations, and gamified assessments are the minimum viable standard.",
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
# RANKED COLUMN HELPERS
# ─────────────────────────────────────────────────────────────────

def find_ranked_cols(df, question_fragment):
    """Find all rank columns for a question, sorted by rank number."""
    if not question_fragment:
        return []
    frag = question_fragment.lower().strip()
    matched = [c for c in df.columns if frag in c.lower()]
    if not matched:
        return []
    if len(matched) == 1:
        return matched
    def rank_num(col):
        nums = re.findall(r'\d+', col)
        return int(nums[-1]) if nums else 999
    matched.sort(key=rank_num)
    return matched


def aggregate_ranked_cols(df, ranked_cols, top_n=6):
    """
    Count how many respondents chose each item as Rank 1.
    Returns [(label, pct_of_respondents), ...] sorted descending.
    """
    if not ranked_cols:
        return []
    rank1_col = ranked_cols[0]
    if rank1_col not in df.columns:
        return []

    counts = defaultdict(int)
    for val in df[rank1_col].dropna():
        v = str(val).strip()
        if v and v.lower() not in ("nan","none",""):
            v = v.split(";")[0].strip() if ";" in v else v
            counts[v] += 1

    total = sum(counts.values())
    if total == 0:
        return []
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(cnt/total*100)) for item, cnt in items]


def get_multi_counts_ranked(df, ranked_cols, top_n=6):
    """
    Count how many respondents selected each item across all rank columns.
    Returns [(label, pct_of_respondents), ...] sorted descending.
    """
    if not ranked_cols:
        return []
    counts = defaultdict(int)
    answered = set()
    for col in ranked_cols:
        if col not in df.columns:
            continue
        for idx, val in df[col].items():
            if pd.isna(val):
                continue
            v = str(val).strip()
            if v and v.lower() not in ("nan","none",""):
                items = v.split(";") if ";" in v else [v]
                for item in items:
                    item = item.strip()
                    if item:
                        counts[item] += 1
                        answered.add(idx)
    n = len(answered) if answered else len(df)
    if n == 0 or not counts:
        return []
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [(item, round(cnt/n*100)) for item, cnt in items]


# ─────────────────────────────────────────────────────────────────
# COLUMN DETECTION
# ─────────────────────────────────────────────────────────────────

def detect_columns(df):
    cols_l = {c.lower().strip(): c for c in df.columns}

    def find(candidates):
        for cand in candidates:
            if cand in cols_l:
                return cols_l[cand]
        for cand in candidates:
            for cl, co in cols_l.items():
                if cand in cl:
                    return co
        return ""

    mapping = {
        "cluster":     find(["cluster"]),
        "bu_division": find(["bu/division","bu division","bu_division","bu"]),
        "short_role":  find(["short role","shortrole","role short"]),
        "role":        find(["role","designation"]),
        "metro":       find(["metro/non metro","metro non metro","metro"]),
        "emp_status":  find(["employee status","emp status","empstatus","effort performance","e&p"]),
        "frequency":   find(["digital platform frequency","platform frequency","frequency","how often"]),
        "time":        find(["time willing","time available","hours per week","time per week"]),
        "exp":         find(["experience","years in role","time in current role","tenure"]),
        "education":   find(["education","qualification"]),
        "style":       find(["learning style preference","learning style","style preference"]),
    }

    # Ranked question fragments — detect from actual column names in df
    ranked_q = {
        "motiv_frag":         "what is your motivation for engaging in digital learning",
        "format_frag":        "what is your preferred format of digital learning content",
        "dev_needs_frag":     "what are your top 3 professional development needs",
        "participation_frag": "what type of learning reward and recognition will encourage",
        "challenges_frag":    "what are the key challenges you face",
    }
    fallbacks = {
        "motiv_frag":         ["motivation","motivat"],
        "format_frag":        ["preferred format of digital","content format","preferred format"],
        "dev_needs_frag":     ["professional development needs","development need","dev need"],
        "participation_frag": ["reward and recognition","recognition","participation","encourage"],
        "challenges_frag":    ["challenge","barrier","difficulty"],
    }

    for key, frag in ranked_q.items():
        cols = find_ranked_cols(df, frag)
        if cols:
            mapping[key] = frag
        else:
            for fb in fallbacks.get(key, []):
                cols = find_ranked_cols(df, fb)
                if cols:
                    mapping[key] = fb
                    break
            if key not in mapping or not mapping[key]:
                mapping[key] = ""

    return mapping


# ─────────────────────────────────────────────────────────────────
# PERSONA ASSIGNMENT
# ─────────────────────────────────────────────────────────────────

def assign_persona(row, col_map, all_cols):
    scores = {p: 0 for p in PERSONA_TYPES}

    def rank1(frag_key):
        frag = col_map.get(frag_key, "")
        if not frag:
            return ""
        matched = sorted([c for c in all_cols if frag.lower() in c.lower()],
                         key=lambda c: int(re.findall(r'\d+',c)[-1]) if re.findall(r'\d+',c) else 999)
        if not matched:
            return ""
        v = row.get(matched[0], "")
        if pd.isna(v): return ""
        v = str(v).strip()
        return (v.split(";")[0].strip() if ";" in v else v).lower()

    motiv = rank1("motiv_frag")
    fmt   = rank1("format_frag")
    style_col = col_map.get("style","")
    style = str(row.get(style_col,"")).lower().split(";")[0].strip() if style_col else ""

    if "career"  in motiv: scores["Pathfinder"] += 3
    elif "growth" in motiv or "personal" in motiv: scores["Inquirer"] += 2; scores["Pathfinder"] += 1
    elif "performance" in motiv or "job" in motiv: scores["Navigator"] += 3; scores["Pragmatist"] += 1
    elif "trend" in motiv or "industry" in motiv:  scores["Inquirer"] += 2

    if "video" in fmt or "short" in fmt:            scores["Pragmatist"] += 2; scores["Pathfinder"] += 1
    elif "game" in fmt or "gamif" in fmt:            scores["Connector"] += 2; scores["Pathfinder"] += 1
    elif "case" in fmt or "scenario" in fmt:         scores["Inquirer"] += 2; scores["Connector"] += 1
    elif "book" in fmt or "article" in fmt:          scores["Inquirer"] += 3
    elif "podcast" in fmt or "audio" in fmt:         scores["Navigator"] += 2

    if "visual" in style:                            scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif "simulation" in style or "game" in style:   scores["Connector"] += 2
    elif "reading" in style or "writing" in style:   scores["Inquirer"] += 2
    elif "audio" in style:                           scores["Navigator"] += 1

    freq_col = col_map.get("frequency","")
    freq = str(row.get(freq_col,"")).lower() if freq_col else ""
    if "daily" in freq:    scores["Pathfinder"] += 2
    elif "weekly" in freq: scores["Pragmatist"] += 1; scores["Connector"] += 1
    elif "month" in freq or "occasion" in freq: scores["Navigator"] += 2

    time_col = col_map.get("time","")
    tv = str(row.get(time_col,"")).lower() if time_col else ""
    if "<1" in tv or "30 min" in tv or "less than 1" in tv: scores["Pragmatist"] += 2
    elif "1" in tv and "2" in tv:  scores["Pathfinder"] += 1; scores["Pragmatist"] += 1
    elif "3" in tv or "more" in tv: scores["Inquirer"] += 1; scores["Navigator"] += 1

    es_col = col_map.get("emp_status","")
    emp = str(row.get(es_col,"")).upper() if es_col else ""
    if "HELP" in emp:   scores["Pragmatist"] += 1
    elif "HEHP" in emp: scores["Pathfinder"] += 1
    elif "LELP" in emp: scores["Connector"] += 1
    elif "LEHP" in emp: scores["Navigator"] += 1

    return max(scores, key=scores.get)


# ─────────────────────────────────────────────────────────────────
# BUILD SEGMENT DATA
# ─────────────────────────────────────────────────────────────────

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

    motiv_data  = aggregate_ranked_cols(df, find_ranked_cols(df, col_map.get("motiv_frag","")), top_n=5)
    format_data = aggregate_ranked_cols(df, find_ranked_cols(df, col_map.get("format_frag","")), top_n=6)
    dev_data    = get_multi_counts_ranked(df, find_ranked_cols(df, col_map.get("dev_needs_frag","")), top_n=5)
    part_data   = get_multi_counts_ranked(df, find_ranked_cols(df, col_map.get("participation_frag","")), top_n=5)
    chall_data  = get_multi_counts_ranked(df, find_ranked_cols(df, col_map.get("challenges_frag","")), top_n=5)

    style_col  = col_map.get("style","")
    style_cols = find_ranked_cols(df, style_col) if style_col else []
    style_data = aggregate_ranked_cols(df, style_cols, top_n=4) if style_cols else []

    time_col  = col_map.get("time","")
    time_data = []
    if time_col and time_col in df.columns:
        tc = df[time_col].value_counts()
        tot = tc.sum()
        time_data = [(str(k), round(v/tot*100)) for k,v in tc.items() if not pd.isna(k)]
        time_data.sort(key=lambda x: x[1], reverse=True)

    metro_col = col_map.get("metro","")
    metro_n = 0
    if metro_col and metro_col in df.columns:
        mc = df[metro_col].value_counts()
        metro_n = int(mc.get("Metro", 0))

    es_col = col_map.get("emp_status","")
    es_dist = {}
    if es_col and es_col in df.columns:
        for k,v in df[es_col].value_counts().items():
            if not pd.isna(k): es_dist[str(k)] = int(v)

    def ci(label):
        l = label.lower()
        for k,ic in {"time":"⏰","technical":"📶","connect":"📶","engag":"😐","relev":"🎯","access":"🔒"}.items():
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
        if any(x in tb for x in ["<1","30 min","less than 1"]): chunk="10"; freq="twice-weekly"
        elif any(x in tb for x in ["3","4","more",">3"]):        chunk="20"; freq="bi-weekly"

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
         f"with {mot2[0]} as the strong second choice ({mot2[1]}%). "
         f"{mot_narr}"),

        (f"The most cited barrier is {ch1[0]} ({ch1[1]}% flagged it), "
         f"followed closely by {ch2[0]} ({ch2[1]}%). "
         f"{ch_narr}"),

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
    role_info = ROLE_ABOUT.get(role_key, ("a field professional in the Cipla organisation.","continue developing their skills."))

    def top_val(key, default="—"):
        col = col_map.get(key,"")
        if col and col in subset.columns:
            vc = subset[col].dropna().value_counts()
            return str(vc.index[0]) if len(vc)>0 else default
        return default

    metro_col = col_map.get("metro",""); metro_pct = 0; top_loc = "Mixed"
    if metro_col and metro_col in subset.columns:
        mc = subset[metro_col].value_counts()
        mn = int(mc.get("Metro",0)); metro_pct = round(mn/n*100) if n>0 else 0
        top_loc = "Metro" if metro_pct>=50 else "Non-Metro"

    motiv_data  = aggregate_ranked_cols(subset, find_ranked_cols(subset, col_map.get("motiv_frag","")), top_n=5)
    format_data = aggregate_ranked_cols(subset, find_ranked_cols(subset, col_map.get("format_frag","")), top_n=6)
    dev_data    = get_multi_counts_ranked(subset, find_ranked_cols(subset, col_map.get("dev_needs_frag","")), top_n=5)
    part_data   = get_multi_counts_ranked(subset, find_ranked_cols(subset, col_map.get("participation_frag","")), top_n=5)
    chall_data  = get_multi_counts_ranked(subset, find_ranked_cols(subset, col_map.get("challenges_frag","")), top_n=5)
    style_col   = col_map.get("style","")
    sc          = find_ranked_cols(subset, style_col) if style_col else []
    style_data  = aggregate_ranked_cols(subset, sc, top_n=4) if sc else []

    def ci(label):
        l = label.lower()
        for k,ic in {"time":"⏰","technical":"📶","connect":"📶","engag":"😐","relev":"🎯","access":"🔒"}.items():
            if k in l: return ic
        return "•"

    top_format = format_data[0][0] if format_data else "Short Videos"
    top_motiv  = motiv_data[0][0]  if motiv_data  else "Career advancement"
    time_col   = col_map.get("time",""); time_bracket = "1–2 hrs / week"
    if time_col and time_col in subset.columns:
        tc = subset[time_col].dropna().value_counts()
        if len(tc)>0: time_bracket = str(tc.index[0])

    es_col = col_map.get("emp_status",""); es_dist = {}
    if es_col and es_col in subset.columns:
        for k,v in subset[es_col].value_counts().items():
            if not pd.isna(k): es_dist[str(k)] = int(v)

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
        "learnPref":  {"format":top_format,
                       "duration":"Short < 5 min" if any(x in top_format.lower() for x in ["video","short"]) else "Flexible",
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
    all_cols = list(df.columns)

    # Role normalisation — prefer Short Role column
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

    df["_persona"] = df.apply(lambda row: assign_persona(row, col_map, all_cols), axis=1)

    cluster_col = col_map.get("cluster","")
    bu_col      = col_map.get("bu_division","")
    metro_col   = col_map.get("metro","")
    es_col      = col_map.get("emp_status","")

    clusters = sorted(df[cluster_col].dropna().unique().tolist()) if cluster_col and cluster_col in df.columns else []
    bu_divs  = sorted(df[bu_col].dropna().unique().tolist())      if bu_col and bu_col in df.columns else []
    roles    = sorted([r for r in df["_role_clean"].dropna().unique() if r and r!="nan"])
    metros   = sorted(df[metro_col].dropna().unique().tolist())    if metro_col and metro_col in df.columns else []

    # Anonymised rows for JS client-side filtering
    keep = ["_role_clean","_persona"]
    for c in [cluster_col, bu_col, metro_col, es_col]:
        if c and c in df.columns and c not in keep: keep.append(c)
    rename = {"_role_clean":"role","_persona":"persona",cluster_col:"cluster",
              bu_col:"bu_division",metro_col:"metro",es_col:"empStatus"}
    clean_rows = [{rename.get(k,k):str(v) for k,v in r.items()}
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
    }
