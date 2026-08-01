# Setup & Startup Guide

This is the step-by-step guide to get the dashboard running from scratch. For a feature overview, see [README.md](README.md).

---

## 1. Prerequisites

- Python 3.9+
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier works)
- (Optional, recommended) A free [Supabase](https://supabase.com) project — without it, data is stored in local JSON files under `data/` instead of the cloud

---

## 2. Install

```bash
cd ai_social_media_manager

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Configure `.env`

Create a `.env` file in the project root (it's gitignored, so it stays local):

```ini
GEMINI_API_KEY="your_gemini_api_key"

# Optional — only if you're using Supabase for cloud storage
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-anon-public-key"

# Optional — needed only for "public profile" Instagram connections (username, no password).
# A dedicated Instagram account the server logs into once, then uses to read any public
# username's stats/recent posts without that account's own password.
INSTAGRAM_SCRAPER_USERNAME="your_viewer_account_username"
INSTAGRAM_SCRAPER_PASSWORD="your_viewer_account_password"
```

That's the only file you need to hand-edit. Everything else (dashboard password, Instagram credentials, Supabase connection if you'd rather set it later) is configured from inside the dashboard on first run.

---

## 4. (Optional) Set up Supabase

Skip this if you're fine with local-only storage for now — you can add Supabase later from the dashboard's Settings panel without losing data.

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** → **New query**.
3. Paste in the entire contents of [`schema.sql`](schema.sql) and click **Run**.
   - This creates the `companies`, `platform_connections`, `posts_history`, and `current_calendar` tables, and seeds a starter "New Gen Studios" company.
   - The script is safe to re-run any time (e.g. after pulling an update that changes the schema).
4. Copy your project's **Project URL** and **anon public key** (Project Settings → API) into `.env` as shown above, or paste them into the dashboard's Settings panel after you log in.

---

## 5. Start the server

```bash
python main.py
```

Open **http://127.0.0.1:8000** in your browser.

---

## 6. First-run walkthrough

1. **Create a dashboard password.** The first time you open the app, you'll be prompted to set a password — this protects every company's data and credentials behind a login screen. There's no "forgot password" flow, so keep it somewhere safe (you can reset it by deleting the `DASHBOARD_PASSWORD_HASH` line from `.env`, or clearing `dashboard_password_hash` in the Supabase `system_settings` table, and restarting).
2. **Log in** with the password you just set.
3. **Create your first company.** Fill in:
   - Business context (what the company does, what makes it different)
   - Target audience
   - Brand voice
   - Default CTA
   - Content pillars (one per line)
4. **Pick a platform** from the header dropdown (Instagram, Facebook, LinkedIn, or Google Business Profile) — this is what the AI generates content for.
5. **(Optional) Connect Instagram** via the plug icon in the header, if you want live follower/post stats and recent-post history for that company. Facebook/LinkedIn/Google Business Profile show as "Coming Soon" until you've registered a developer app with that platform (see the Platform Support table in the README).
6. **Generate a calendar** with the Strategy Planner, review/edit posts in the Studio panel, then **Save** or **Commit & Export Excel**.

---

## 7. Day-to-day startup

Once everything is configured, starting the app again is just:

```bash
source .venv/bin/activate
python main.py
```

Your companies, calendars, and history persist across restarts (in Supabase if configured, otherwise in the local `data/` folder).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` on startup | Re-run `pip install -r requirements.txt` inside the activated venv |
| Port 8000 already in use | Another process is using it — stop it, or edit the port in the last line of `main.py` |
| "Gemini API Key is not set" | Add it via `.env` or the dashboard's Settings panel, then reload |
| Instagram connect fails / login errors | Instagram sometimes challenges new-device logins — try logging into that account from a browser first, then reconnect. Credentials are stored per-company, not globally |
| Locked out of the dashboard | Delete `DASHBOARD_PASSWORD_HASH` from `.env` (and/or clear `dashboard_password_hash` in Supabase's `system_settings` table), then restart — you'll be prompted to set a new password |
| Data isn't syncing across machines | You're on local-file storage — connect Supabase (Settings panel or `.env`) to centralize storage |
