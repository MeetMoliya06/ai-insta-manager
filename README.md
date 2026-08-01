# 🤖 AI Social Media Manager

A multi-company, multi-platform agentic AI content planner and dashboard. Manage content strategy for as many client brands as you want from one dashboard — each with its own business context, target audience, content pillars, calendar, and platform connections.

---

## ✨ Features

- **🏢 Multi-Company**: Add unlimited companies/brands, each with its own business context, target audience, brand voice, content pillars, and CTA. Switch between them from the header.
- **📣 Multi-Platform Content**: Generate platform-tailored content for **Instagram**, **Facebook**, **LinkedIn**, and **Google Business Profile** — the AI prompt adapts format, tone, hashtag count, and caption length per platform.
- **🔐 Password-Protected Dashboard**: A single operator password gates the whole dashboard (first run walks you through setting it).
- **🧠 Gemini AI Post Generator**: Structured JSON generation via Google Gemini, producing hooks, captions, hashtags, CTAs, and detailed visual generation prompts (for Midjourney/Runway/Kling).
- **📸 Instagram Live Stats**: Connects to Instagram (via `instagrapi`) per company to pull live follower/post stats and recent-post history for the anti-repetition engine.
- **☁️ Supabase Cloud Sync**: Optional — stores companies, platform connections, calendars, and history centrally so the dashboard can be deployed anywhere. Without it, everything still works using local JSON files under `data/`.
- **📊 Premium Excel Export**: Per-company, multi-sheet `.xlsx` export (Content Calendar, AI Image Prompts, Caption & Hashtag Bank).
- **🚫 Anti-Repetition Engine**: Tracks past posts per company + platform so the AI never repeats topics, hooks, or themes.

---

## 📣 Platform Support Status

| Platform | Content Generation | Live Stats / Auto-Publish |
|---|---|---|
| Instagram | ✅ | ✅ Live stats (via `instagrapi`, unofficial login) — publishing not supported |
| Facebook | ✅ | 🚧 Needs a Meta developer app (Graph API) |
| LinkedIn | ✅ | 🚧 Needs LinkedIn Community Management API access |
| Google Business Profile | ✅ | 🚧 Needs a Google Cloud project with Business Profile API access |

**Content generation works for all four platforms today** — Gemini writes platform-appropriate captions, hashtags, and formats that you copy into each platform's native scheduler or the Excel export.

**Live stats and automated publishing** require an official developer app per platform, which only the account owner can register and get approved:
- **Facebook + Instagram**: create a Meta app at [developers.facebook.com](https://developers.facebook.com), add "Facebook Login for Business," and request `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish` (subject to Meta App Review).
- **LinkedIn**: create an app at [linkedin.com/developers](https://linkedin.com/developers) and request Community Management API access (needed to post as a Company Page).
- **Google Business Profile**: create a Google Cloud project, enable the Business Profile APIs, and request production access via Google's access request form.

Once you have credentials for a platform, the connector interface in `platforms/` is ready to be filled in (see `platforms/facebook.py`, `platforms/linkedin.py`, `platforms/google_business.py`).

---

## 📂 Project Architecture

```bash
├── main.py                    # ⚡ FastAPI application, auth, and company-scoped API endpoints
├── social_media_agent.py      # 🤖 Dynamic prompt builder, data access (Supabase + local), Excel exporter
├── platforms/                 # 🔌 Per-platform connector interface (stats / history / publish)
│   ├── base.py                #   └─ PlatformConnector interface
│   ├── instagram.py           #   └─ Live Instagram stats via instagrapi
│   ├── facebook.py            #   └─ Stub — needs Meta Graph API credentials
│   ├── linkedin.py            #   └─ Stub — needs LinkedIn Community Management API access
│   └── google_business.py     #   └─ Stub — needs Google Business Profile API access
├── schema.sql                 # ⚡ SQL migrations to configure Supabase tables (companies, connections, etc.)
├── static/                    # 🎨 Dashboard web frontend
│   ├── index.html             #   └─ Interactive HTML structure
│   ├── style.css              #   └─ Custom styling & dynamic layout
│   └── app.js                 #   └─ Frontend controller & API fetch logic
├── data/                      # 📅 Local fallback storage (companies, calendars, history) when Supabase isn't configured
├── requirements.txt           # 📦 Python package dependencies
├── .env                       # 🔑 Sensitive credentials (local only)
└── .gitignore
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Python 3.9+ and `pip`.

### 2. Setup Environment

```bash
cd ai_social_media_manager
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```ini
# 🔑 Gemini API Credentials (required)
GEMINI_API_KEY="your_gemini_api_key"

# ☁️ Supabase Cloud Sync (optional — recommended for real multi-company use)
SUPABASE_URL="https://your-supabase-project.supabase.co"
SUPABASE_KEY="your-anon-public-key"
```

*Instagram credentials, the dashboard password, and everything else are configured from the dashboard itself — no need to hand-edit `.env` for those.*

---

## ⚡ Supabase Setup (Optional but Recommended)

Without Supabase, all data (companies, calendars, history, connections) is stored in local JSON files under `data/` — fine for a single machine, but it won't survive a redeploy or be shared across environments.

1. Create a free project on [Supabase](https://supabase.com).
2. Open the **SQL Editor** and paste in the contents of `schema.sql`, then **Run**. It's safe to re-run.
3. Copy your project's **API URL** and **Anon public key** into the dashboard's **Settings** panel (or `.env`).

---

## 🚀 Running the Application

```bash
python main.py
```

Then open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

**First run**: you'll be asked to set a dashboard password (protects every `/api/*` route with a session cookie), then create your first company. From there:
- Switch companies via the header dropdown, or add new ones with the **+** button.
- Edit a company's business context, audience, brand voice, pillars, and CTA — this is what drives the AI prompt, replacing what used to be hardcoded.
- Pick the active platform from the header dropdown before generating — Instagram, Facebook, LinkedIn, or Google Business Profile.
- Use the **plug icon** to manage platform connections per company (Instagram username/password today; the other three show what's needed to connect once you have official API credentials).
- Generate, edit in the Studio panel, save, and export to Excel — same workflow as before, now per company and per platform.

---

## 🛡️ License

Custom proprietary software. All rights reserved.
