# 🤖 New Gen Studios — AI Social Media Manager

Welcome to the **New Gen Studios AI Social Media Manager**, a state-of-the-art agentic AI content planner and beautiful web dashboard designed specifically for luxury brand social media curation. 

**New Gen Studios (@newgenstudios.ai)** is an AI-powered creative agency based in Surat, India. We specialize in producing luxury product photoshoots and cinematic Instagram Reels for high-end jewellery and fashion brands (saree, ethnic wear, apparel) using advanced AI technologies. This tool automates the core workflows of our social media strategy—content ideation, dynamic scheduling, copy generation, and metric tracking.

---

## ✨ Features

- **📺 Interactive Web Dashboard**: A premium, custom-styled frontend interface serving real-time analytics, settings management, calendar previews, editing blocks, and instant Excel exports.
- **🧠 Gemini AI Post Generator**: Seamlessly interfaces with the Google Gemini API (`gemini-2.5-flash` or newer) utilizing structured JSON generation. Generates high-converting, scroll-stopping hooks, hashtags, CTAs, and highly detailed visual generation prompts (customized for Midjourney, Runway, and Kling).
- **📸 Instagram Live Sync (`instagrapi`)**: Connects securely to Instagram to dynamically retrieve live profile statistics (followers, following, post counts) and video views from recent Reels.
- **☁️ Supabase Cloud Synchronization**: Features real-time bidirectional sync. Instantly replicates local configuration keys, post histories, and scheduled calendars to a cloud database, providing seamless state persistence across multiple environments.
- **📊 Premium Multi-Sheet Excel Export**: Exports content calendars using highly customized `openpyxl` style maps (corporate teal, warm amber, and elegant lavender). The export contains three dedicated sheets:
  1. **Content Calendar**: Full timeline calendar with formatting indicators and checkboxes.
  2. **AI Image Prompts**: Standalone prompts optimized for copy-pasting directly into Midjourney/Leonardo (images) and RunwayML/Kling (videos).
  3. **Caption & Hashtag Bank**: Direct, ready-to-copy captions paired with exactly 25 highly targeted hashtags.
- **🚫 Anti-Repetition Engine**: Automatically loads past posts to build a strategic historical context block, ensuring the AI never repeats topics, themes, or hook formulas.

---

## 📂 Project Architecture

```bash
├── main.py                    # ⚡ FastAPI application & dashboard endpoints
├── social_media_agent.py      # 🤖 Core agent logic, Google GenAI, Instagrapi, & Excel exporter
├── schema.sql                 # ⚡ SQL migrations to configure Supabase tables
├── static/                    # 🎨 Dashboard web frontend
│   ├── index.html             #   └─ Interactive HTML structure
│   ├── style.css              #   └─ Custom styling & dynamic layout
│   └── app.js                 #   └─ Frontend controller & API fetch logic
├── requirements.txt           # 📦 Python package dependencies
├── .env                       # 🔑 Sensitive credentials (local only)
├── .gitignore                 # 🚫 Git ignoring environments, XLSX, & sessions
├── current_calendar.json      # 📅 Local temporary calendar cache
└── posts_history.json         # 📚 Local backup of post histories
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.9+** and `pip` installed on your machine.

### 2. Clone the Repository & Setup Environment
Navigate to your project directory and initialize a virtual environment:

```bash
# Clone the repository and enter the directory
cd ai_social_media_manager

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root of the project (already ignored in `.gitignore`) and define the following variables:

```ini
# 🔑 Gemini API Credentials
GEMINI_API_KEY="your_gemini_api_key"

# 📸 Instagram Credentials (Optional)
INSTAGRAM_USERNAME="newgenstudios.ai"
INSTAGRAM_PASSWORD="your_instagram_password"

# ☁️ Supabase Cloud Sync (Optional)
SUPABASE_URL="https://your-supabase-project.supabase.co"
SUPABASE_KEY="your-anon-public-key"
```
*Note: You can also configure these settings dynamically from the Settings panel directly inside the web dashboard.*

---

## ⚡ Supabase Setup (Optional but Recommended)

To leverage the real-time cloud synchronization features:
1. Create a free project on [Supabase](https://supabase.com).
2. Open the **SQL Editor** in your Supabase dashboard.
3. Paste the contents of `schema.sql` into the SQL Editor and click **Run**.
4. Copy your project's **API URL** and **Anon public key** into the Dashboard Settings under **Supabase Sync Setup**.
5. Once saved, your local data will automatically synchronize and back up to the cloud!

---

## 🚀 Running the Application

### Option A: The Interactive Web Dashboard (Recommended)
Launch the FastAPI development server to interact with the visual dashboard:

```bash
python main.py
```
After the server boots up, open your web browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*From the dashboard, you can:*
- View real-time Instagram metrics.
- Modify Gemini models, post frequency, and custom content pillars.
- Review and live-edit generated captions, hooks, and prompts before saving.
- Download the final high-quality Excel spreadsheet instantly.

---

### Option B: The CLI Agent
If you prefer running the generator directly from your terminal:

```bash
python social_media_agent.py
```
This script will:
1. Retrieve historical data from your active database.
2. Direct-generate `8` fresh posts (defaulting to a 2-week plan of 4 posts per week).
3. Schedule them on best-performing days (Tuesday, Thursday, Friday, Saturday, Sunday).
4. Save the beautiful styled Excel template as `content_calendar.xlsx`.
5. Update your local `posts_history.json` so it remembers them for future runs.

---

## 🛡️ License

This project is custom proprietary software developed for **New Gen Studios** (Surat, India). All rights reserved.
