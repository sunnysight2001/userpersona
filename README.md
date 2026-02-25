# Cipla · Learner Persona Dashboard

An interactive dashboard generator for Cipla's field force and marketing learning data.

Upload a survey Excel → Get a fully interactive persona dashboard HTML → Share with trainers.

---

## How It Works

1. A non-technical person opens the app link in their browser
2. Uploads the Cipla learning survey Excel file
3. Clicks **Generate Dashboard**
4. Downloads a single `cipla_learner_persona_dashboard.html` file
5. Shares that file with trainers — works in any browser, fully offline

**Your data never leaves your session.** The Excel is processed in memory only. Nothing is stored.

---

## Deploying on Streamlit Community Cloud (one-time setup, ~10 minutes)

### Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in (or create a free account)
2. Click **New repository**
3. Name it `cipla-persona-dashboard`
4. Set it to **Private** (recommended)
5. Click **Create repository**
6. Upload these four files into the repository:
   - `app.py`
   - `processor.py`
   - `template.html`
   - `requirements.txt`

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select your repository: `cipla-persona-dashboard`
5. Branch: `main`
6. Main file path: `app.py`
7. Click **Deploy**

Streamlit will build and deploy the app in about 2–3 minutes.

### Step 3 — Share the Link

Once deployed, you get a public URL like:
```
https://your-name-cipla-persona-dashboard-app-xxxxxx.streamlit.app
```

Share this link with whoever needs to generate dashboards.

---

## Making the App Private (Recommended for Cipla)

To restrict access so only approved people can use the app:

1. In Streamlit Community Cloud, go to your app settings
2. Click **Sharing**
3. Set to **Specific people** and add email addresses
4. Only those emails (logged into Streamlit) can access the app

Alternatively, set the GitHub repository to **Private** — the app itself will still be accessible via the link, but the source code will not be visible to the public.

---

## Updating the App

If the survey format changes or the template needs updates:

1. Edit the relevant file locally
2. Upload the updated file to GitHub (replace the old one)
3. Streamlit automatically redeploys — usually within 1–2 minutes

---

## What Each File Does

| File | Purpose |
|------|---------|
| `app.py` | The Streamlit web app — handles upload, display, and download |
| `processor.py` | All data logic — column detection, persona assignment, insight generation |
| `template.html` | The dashboard visual template — data injected by the processor |
| `requirements.txt` | Python libraries needed (installed automatically by Streamlit) |

---

## Column Detection

The app auto-detects columns using flexible matching. If your Excel uses different column names,
edit the `patterns` dictionary in `processor.py` → `detect_columns()` function to add your exact column names.

---

## Persona Types

Each respondent is assigned one of five learner persona types based on their survey responses:

| Persona | Core Driver |
|---------|------------|
| 🧭 Pathfinder | Career advancement, daily learner, structured progression |
| ⚡ Pragmatist | Time-pressured, immediate applicability, bite-sized formats |
| 🔬 Inquirer | Depth-seeking, evidence-hungry, clinical and scientific content |
| 🗺️ Navigator | Experience-rich, self-directed, performance-focused |
| 🤝 Connector | Collaborative, peer-learning, coaching and team scenarios |

Assignment is rule-based across four dimensions: motivation, format preference, learning frequency, and time availability.

---

## Privacy & Data Security

- ✅ Excel files processed in RAM only — never written to disk
- ✅ No database, no logging of uploaded content
- ✅ Session cleared automatically when browser tab closes
- ✅ Output HTML contains only aggregated, anonymous data — no individual names or IDs
- ✅ Strip PII columns (Name, Email, Employee ID) before uploading for maximum safety

---

## Support

For technical issues, contact your L&D Technology team.
For questions about persona methodology, contact the Learning Analytics team.
