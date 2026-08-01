"""
AI Social Media Manager — Core Agent
Multi-company, multi-platform content generation, data access, and Excel export.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from google import genai
from google.genai import types
from dotenv import load_dotenv

from platforms import PLATFORM_LABELS

load_dotenv()

DATA_DIR = "data"
OUTPUT_FILE = "content_calendar.xlsx"

DEFAULT_CONTENT_PILLARS = [
    "Before/After transformation",
    "Educational (how it works)",
    "Client result / testimonial",
    "Trending / viral hook",
    "Offer / CTA-driven post",
    "Behind-the-scenes",
    "Product / service showcase",
    "Myth-busting post",
    "POV / relatable content",
]

DEFAULT_BEST_TIMES = [
    ("Tuesday",  "11:00 AM IST (7:30 AM CEST / 6:30 AM GMT)"),
    ("Thursday", "07:00 PM IST (3:30 PM CEST / 2:30 PM GMT)"),
    ("Friday",   "12:00 PM IST (8:30 AM CEST / 7:30 AM GMT)"),
    ("Saturday", "10:00 AM IST (6:30 AM CEST / 5:30 AM GMT)"),
    ("Sunday",   "06:00 PM IST (2:30 PM CEST / 1:30 PM GMT)"),
]

PLATFORM_FORMAT_GUIDANCE = {
    "instagram": """
- 80% Reels (MANDATORY), 20% Carousel or Static Image
- reel_or_static must be one of: "Reel", "Static Image", "Carousel"
- Hooks must create a curiosity gap, use numbers, sound shocking, or call out the audience
- Hashtags: exactly 25, highly targeted
- Captions: conversational, bold, punchy — 4-8 lines
""",
    "facebook": """
- Mix of "Post" (photo/text), "Reel", and "Carousel" — reel_or_static must be one of those three
- Captions can be slightly longer and more conversational than Instagram, written for community engagement (shares, comments) rather than just views
- Hashtags: 3-8 relevant ones (Facebook does not reward hashtag stuffing) — still fill the hashtags field but keep it short
- Hooks should work for an older/broader demographic than Instagram
""",
    "linkedin": """
- reel_or_static must be one of: "Text Post", "Carousel (PDF)", "Document"
- Professional but not corporate-boring tone; thought-leadership, results, and behind-the-scenes-of-the-business angles perform best
- Captions are longer-form (short paragraphs, line breaks, a hook line first) — aim for value/insight, not hard-sell
- Hashtags: exactly 3-5, industry-relevant
- No emoji-heavy hooks; open with a strong first line since LinkedIn truncates after ~2 lines
""",
    "google_business": """
- reel_or_static must be one of: "Update", "Offer", "Event", "Product"
- Very short copy (under 1500 characters, ideally 2-3 sentences) — these are local search/discovery posts, not social feed content
- Always end with a clear, local action (call, visit, book, redeem offer)
- hashtags field should be an empty string "" — Google Business Profile posts don't use hashtags
""",
}


def _company_dir(company_id: str) -> str:
    path = os.path.join(DATA_DIR, str(company_id))
    os.makedirs(path, exist_ok=True)
    return path


# ──────────────────────────────────────────────────────────
# Local (no-Supabase) fallback storage
# ──────────────────────────────────────────────────────────

COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")


def load_companies_local():
    if os.path.exists(COMPANIES_FILE):
        with open(COMPANIES_FILE) as f:
            return json.load(f)
    return []


def save_companies_local(companies):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(COMPANIES_FILE, "w") as f:
        json.dump(companies, f, indent=2)


def create_company_local(data: dict) -> dict:
    companies = load_companies_local()
    company = {
        "id": str(uuid.uuid4()),
        "slug": data.get("slug") or data["name"].lower().replace(" ", "-"),
        "name": data["name"],
        "industry": data.get("industry", ""),
        "business_context": data.get("business_context", ""),
        "target_audience": data.get("target_audience", ""),
        "brand_voice": data.get("brand_voice", ""),
        "content_pillars": data.get("content_pillars") or DEFAULT_CONTENT_PILLARS,
        "cta_text": data.get("cta_text", ""),
        "best_times": data.get("best_times") or DEFAULT_BEST_TIMES,
        "website_url": data.get("website_url", ""),
        "auto_research": data.get("auto_research", False),
        "last_researched_at": data.get("last_researched_at"),
        "research_summary": data.get("research_summary", ""),
        "research_sources": data.get("research_sources") or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    companies.append(company)
    save_companies_local(companies)
    return company


def update_company_local(company_id: str, data: dict):
    companies = load_companies_local()
    for c in companies:
        if c["id"] == company_id:
            c.update({k: v for k, v in data.items() if v is not None})
            save_companies_local(companies)
            return c
    return None


def delete_company_local(company_id: str):
    companies = [c for c in load_companies_local() if c["id"] != company_id]
    save_companies_local(companies)


def load_history_local(company_id: str, platform: str):
    path = os.path.join(_company_dir(company_id), f"history_{platform}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"posts": []}


def save_history_local(company_id: str, platform: str, posts: list):
    path = os.path.join(_company_dir(company_id), f"history_{platform}.json")
    with open(path, "w") as f:
        json.dump({"posts": posts}, f, indent=2)


def load_calendar_local(company_id: str) -> list:
    path = os.path.join(_company_dir(company_id), "calendar.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_calendar_local(company_id: str, posts: list):
    path = os.path.join(_company_dir(company_id), "calendar.json")
    with open(path, "w") as f:
        json.dump(posts, f, indent=2)


def load_connections_local(company_id: str) -> dict:
    path = os.path.join(_company_dir(company_id), "connections.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_connection_local(company_id: str, platform: str, credentials: dict, auth_type: str = "password"):
    connections = load_connections_local(company_id)
    connections[platform] = {
        "auth_type": auth_type,
        "credentials": credentials,
        "status": "connected",
        "connected_at": datetime.utcnow().isoformat(),
    }
    path = os.path.join(_company_dir(company_id), "connections.json")
    with open(path, "w") as f:
        json.dump(connections, f, indent=2)


def delete_connection_local(company_id: str, platform: str):
    connections = load_connections_local(company_id)
    connections.pop(platform, None)
    path = os.path.join(_company_dir(company_id), "connections.json")
    with open(path, "w") as f:
        json.dump(connections, f, indent=2)


def load_trend_cache_local(company_id: str, platform: str):
    path = os.path.join(_company_dir(company_id), f"trends_{platform}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_trend_cache_local(company_id: str, platform: str, trend_data: dict):
    path = os.path.join(_company_dir(company_id), f"trends_{platform}.json")
    with open(path, "w") as f:
        json.dump(trend_data, f, indent=2)


# ──────────────────────────────────────────────────────────
# Supabase-backed storage
# ──────────────────────────────────────────────────────────

import requests


def get_supabase_config():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return url.strip().rstrip("/"), key.strip()
    return None, None


def supabase_headers(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# -- Operator-level settings (Gemini key, dashboard password hash) --

def fetch_settings_supabase():
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/system_settings?id=eq.default"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            rows = res.json()
            if rows:
                return rows[0]
        else:
            print(f"⚠️ Supabase fetch settings failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase fetch settings failed: {e}")
    return None


def save_settings_supabase(gemini_key=None, dashboard_password_hash=None):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        existing = fetch_settings_supabase() or {"id": "default"}
        payload = {
            "id": "default",
            "gemini_api_key": gemini_key if gemini_key is not None else existing.get("gemini_api_key"),
            "dashboard_password_hash": dashboard_password_hash if dashboard_password_hash is not None else existing.get("dashboard_password_hash"),
        }
        req_url = f"{url}/rest/v1/system_settings"
        headers = supabase_headers(key)
        headers["Prefer"] = "resolution=merge-duplicates"
        res = requests.post(req_url, json=payload, headers=headers, timeout=5)
        if res.status_code in (200, 201):
            return True
        print(f"⚠️ Supabase save settings failed with status {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"⚠️ Supabase save settings failed: {e}")
        return False


# -- Companies --

def list_companies_supabase():
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/companies?select=*&order=created_at.asc"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            return res.json()
        print(f"⚠️ Supabase list companies failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase list companies failed: {e}")
    return None


def create_company_supabase(data: dict):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        payload = {
            "slug": data.get("slug") or data["name"].lower().replace(" ", "-"),
            "name": data["name"],
            "industry": data.get("industry", ""),
            "business_context": data.get("business_context", ""),
            "target_audience": data.get("target_audience", ""),
            "brand_voice": data.get("brand_voice", ""),
            "content_pillars": data.get("content_pillars") or DEFAULT_CONTENT_PILLARS,
            "cta_text": data.get("cta_text", ""),
            "best_times": data.get("best_times") or DEFAULT_BEST_TIMES,
            "website_url": data.get("website_url", ""),
            "auto_research": data.get("auto_research", False),
            "last_researched_at": data.get("last_researched_at"),
            "research_summary": data.get("research_summary", ""),
            "research_sources": data.get("research_sources") or [],
        }
        res = requests.post(f"{url}/rest/v1/companies", json=payload, headers=supabase_headers(key), timeout=5)
        if res.status_code in (200, 201):
            rows = res.json()
            return rows[0] if rows else None
        print(f"⚠️ Supabase create company failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase create company failed: {e}")
    return None


def update_company_supabase(company_id: str, data: dict):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        payload = {k: v for k, v in data.items() if v is not None}
        req_url = f"{url}/rest/v1/companies?id=eq.{company_id}"
        res = requests.patch(req_url, json=payload, headers=supabase_headers(key), timeout=5)
        if res.status_code in (200, 201):
            rows = res.json()
            return rows[0] if rows else None
        print(f"⚠️ Supabase update company failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase update company failed: {e}")
    return None


def delete_company_supabase(company_id: str):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        req_url = f"{url}/rest/v1/companies?id=eq.{company_id}"
        res = requests.delete(req_url, headers=supabase_headers(key), timeout=5)
        return res.status_code in (200, 204)
    except Exception as e:
        print(f"⚠️ Supabase delete company failed: {e}")
        return False


# -- Platform connections --

def list_connections_supabase(company_id: str):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/platform_connections?company_id=eq.{company_id}&select=*"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            return res.json()
        print(f"⚠️ Supabase list connections failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase list connections failed: {e}")
    return None


def save_connection_supabase(company_id: str, platform: str, credentials: dict, auth_type: str = "password"):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        payload = {
            "company_id": company_id,
            "platform": platform,
            "auth_type": auth_type,
            "credentials": credentials,
            "status": "connected",
        }
        headers = supabase_headers(key)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        res = requests.post(f"{url}/rest/v1/platform_connections", json=payload, headers=headers, timeout=5)
        if res.status_code in (200, 201):
            return True
        print(f"⚠️ Supabase save connection failed with status {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"⚠️ Supabase save connection failed: {e}")
        return False


def delete_connection_supabase(company_id: str, platform: str):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        req_url = f"{url}/rest/v1/platform_connections?company_id=eq.{company_id}&platform=eq.{platform}"
        res = requests.delete(req_url, headers=supabase_headers(key), timeout=5)
        return res.status_code in (200, 204)
    except Exception as e:
        print(f"⚠️ Supabase delete connection failed: {e}")
        return False


# -- Trend cache (per company + platform) --

def load_trend_cache_supabase(company_id: str, platform: str):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/trend_cache?company_id=eq.{company_id}&platform=eq.{platform}&select=*"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            rows = res.json()
            return rows[0] if rows else None
        print(f"⚠️ Supabase load trend cache failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase load trend cache failed: {e}")
    return None


def save_trend_cache_supabase(company_id: str, platform: str, trend_data: dict):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        payload = {
            "company_id": company_id,
            "platform": platform,
            "trends": trend_data.get("trends", []),
            "sources": trend_data.get("sources", []),
            "fetched_at": trend_data.get("fetched_at"),
        }
        headers = supabase_headers(key)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        res = requests.post(f"{url}/rest/v1/trend_cache", json=payload, headers=headers, timeout=5)
        if res.status_code in (200, 201):
            return True
        print(f"⚠️ Supabase save trend cache failed with status {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"⚠️ Supabase save trend cache failed: {e}")
        return False


# -- Posts history (per company + platform, powers the anti-repetition engine) --

def load_history_supabase(company_id: str, platform: str):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/posts_history?company_id=eq.{company_id}&platform=eq.{platform}&select=*&order=created_at.asc"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            return {"posts": res.json()}
        print(f"⚠️ Supabase load history failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase load history failed: {e}")
    return None


def save_history_supabase(company_id: str, platform: str, history_posts: list):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        headers = supabase_headers(key)
        del_url = f"{url}/rest/v1/posts_history?company_id=eq.{company_id}&platform=eq.{platform}"
        del_res = requests.delete(del_url, headers=headers, timeout=5)
        if del_res.status_code not in (200, 204):
            print(f"⚠️ Supabase clear history failed with status {del_res.status_code}: {del_res.text}")

        payload = [{
            "company_id": company_id,
            "platform": platform,
            "date": p.get("date"),
            "post_type": p.get("post_type"),
            "idea_summary": p.get("idea_summary"),
            "reel_or_static": p.get("reel_or_static"),
        } for p in history_posts]

        if not payload:
            return True

        res = requests.post(f"{url}/rest/v1/posts_history", json=payload, headers=headers, timeout=5)
        if res.status_code in (200, 201):
            return True
        print(f"⚠️ Supabase save history failed with status {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"⚠️ Supabase save history failed: {e}")
        return False


# -- Current calendar (per company, spans all platforms — each row carries its own 'platform') --

def load_calendar_supabase(company_id: str):
    url, key = get_supabase_config()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/current_calendar?company_id=eq.{company_id}&select=*&order=post_number.asc"
        res = requests.get(req_url, headers=supabase_headers(key), timeout=5)
        if res.status_code == 200:
            return res.json()
        print(f"⚠️ Supabase load calendar failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"⚠️ Supabase load calendar failed: {e}")
    return None


def save_calendar_supabase(company_id: str, scheduled_posts: list):
    url, key = get_supabase_config()
    if not url or not key:
        return False
    try:
        headers = supabase_headers(key)
        del_url = f"{url}/rest/v1/current_calendar?company_id=eq.{company_id}"
        del_res = requests.delete(del_url, headers=headers, timeout=5)
        if del_res.status_code not in (200, 204):
            print(f"⚠️ Supabase clear calendar failed with status {del_res.status_code}: {del_res.text}")

        payload = [{
            "company_id": company_id,
            "platform": p.get("platform", "instagram"),
            "post_number": p.get("post_number"),
            "date": p.get("date"),
            "day": p.get("day"),
            "time": p.get("time"),
            "post_type": p.get("post_type"),
            "reel_or_static": p.get("reel_or_static"),
            "hook": p.get("hook"),
            "caption": p.get("caption"),
            "hashtags": p.get("hashtags"),
            "image_prompt": p.get("image_prompt"),
            "cta": p.get("cta"),
            "notes_for_creator": p.get("notes_for_creator"),
            "script": p.get("script", ""),
            "editing_style": p.get("editing_style", ""),
            "is_done": p.get("is_done", False),
        } for p in scheduled_posts]

        if not payload:
            return True

        res = requests.post(f"{url}/rest/v1/current_calendar", json=payload, headers=headers, timeout=5)
        if res.status_code in (200, 201):
            return True
        print(f"⚠️ Supabase save calendar failed with status {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"⚠️ Supabase save calendar failed: {e}")
        return False


# ──────────────────────────────────────────────────────────
# AI content generation
# ──────────────────────────────────────────────────────────

def build_history_summary(history):
    posts = history.get("posts", []) if history else []
    if not posts:
        return "No posts have been created yet. This is the first batch."
    lines = [f"- [{p['date']}] {p['post_type']} | Idea: {p['idea_summary']}" for p in posts[-30:]]
    return "\n".join(lines)


def build_trend_context(trend_data: dict) -> str:
    """Turn a cached trends payload into a prompt-ready block. Returns "" if empty."""
    trends = (trend_data or {}).get("trends") or []
    if not trends:
        return ""
    lines = []
    for i, t in enumerate(trends, start=1):
        lines.append(
            f"{i}. TREND: \"{t.get('title', 'Untitled trend')}\"\n"
            f"   Formats: {t.get('format', 'any format')}\n"
            f"   What is happening: {t.get('description', '')}\n"
            f"   Why it works now: {t.get('why_it_works', '')}\n"
            f"   Required brand angle: {t.get('brand_angle', '')}"
        )
    return "\n".join(lines)


def generate_posts(company: dict, platform: str, history: dict, num_posts: int, api_key=None, model_name="gemini-2.5-flash", custom_pillars=None, trend_context: str = ""):
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        api_key_env = os.environ.get("GEMINI_API_KEY")
        if not api_key_env:
            raise ValueError("GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY environment variable or configure it in the dashboard settings.")
        client = genai.Client(api_key=api_key_env)

    history_summary = build_history_summary(history)
    pillars = custom_pillars if custom_pillars else (company.get("content_pillars") or DEFAULT_CONTENT_PILLARS)
    pillars_str = "\n".join(f"- {p}" for p in pillars)
    format_guidance = PLATFORM_FORMAT_GUIDANCE.get(platform, PLATFORM_FORMAT_GUIDANCE["instagram"])
    platform_label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())

    trend_rules = ""
    if trend_context:
        trend_rules = f"""
🔥 TREND EXECUTION RULES (MANDATORY WHEN TRENDS ARE PROVIDED):

You MUST use the trend context below as an execution brief, not loose inspiration.

Batch-level requirements:
- Every generated post must clearly apply at least ONE named trend.
- Rotate trends across the batch. If the number of posts allows it, cover EVERY trend at least once.
- Do not let all posts become only "cinematic luxury visuals"; include hooks, formats, scripts, and production notes that prove the specific trend was used.
- In notes_for_creator, start with: "Trend used: [exact trend title(s)]." Then give production notes.

Specific quality requirements for this trend set:
- If "Authentic AI Visuals" appears in the trend context, at least one visual prompt or script must explicitly include natural human skin texture, visible pores, film grain, imperfect lighting, raw phone-shot energy, or curated imperfection.
- If "Extended Educational Reels" appears in the trend context, at least one Reel script must be 60-180 seconds with a real teaching structure, not a 15-second montage.
- If "Share-Prompting Hooks" appears in the trend context, at least one hook must explicitly ask the viewer to "Send this to..." or "Tag..." a specific type of brand/person.
- If "Niche Cinematic AI Visuals" appears in the trend context, use specific niches like bridal jewellery, saree edits, beauty products, fashion campaigns, or premium product visualization.
- If "Detailed Visual Carousels" appears in the trend context and the platform supports carousels, include at least one detailed carousel with slide-by-slide value, not just a visual gallery.
- If "Emotion-Led Product Reveals" appears in the trend context, at least one Reel must open with an unresolved brand-owner pain/conflict before revealing AI as the resolution.

TREND CONTEXT:
{trend_context}

---
"""

    prompt = f"""You are an ELITE {platform_label} Growth Strategist & Content Director for {company.get('name', 'this brand')}.

Your job is NOT to generate generic content.
Your job is to create high-converting {platform_label} content that attracts {company.get('target_audience', 'the target audience')} and converts them into customers.

You think like:
- A performance marketer
- A brand strategist
- A platform-native content creator who deeply understands {platform_label}'s algorithm and audience behavior

---

🔥 BUSINESS CONTEXT:

{company.get('business_context', 'No business context provided.')}

---

🎯 TARGET AUDIENCE (CRITICAL):

{company.get('target_audience', 'General audience.')}

Speak DIRECTLY to their pain points and goals in every post.

---

🗣️ BRAND VOICE:

{company.get('brand_voice', 'Confident, clear, helpful.')}

---

⚠️ CORE RULE:

Every piece of content must make the viewer think:
"I NEED THIS"

---

🔥 {platform_label.upper()} FORMAT RULES:
{format_guidance}

---
{trend_rules}
📌 CONTENT PILLARS TO ROTATE THROUGH:
{pillars_str}

---

3. HOOK WRITING (CRITICAL):

Hooks MUST create curiosity, use numbers, sound surprising, or call out the audience directly.
Never use generic hooks like "Elevate your brand" or "Beautiful [product], reimagined."
When using a share-prompting trend, the hook must be a direct share/tag command, such as "Send this to..." or "Tag a...".

---

4. CTA (MANDATORY):

End EVERY caption with EXACTLY:
{company.get('cta_text') or 'Learn more — link in bio.'}

---

🚨 QUALITY CONTROL (VERY IMPORTANT):

After generating posts, evaluate EACH post on:
1. Hook Strength (1–10)
2. Platform-fit / Virality Potential (1–10)
3. Conversion Potential (1–10)
4. Trend Execution (1–10) — if trends were provided, the selected trend must be obvious from the hook, format, script, image prompt, or notes_for_creator.

If ANY score is below 8, REWRITE that post completely. Do NOT output weak content.
If trends were provided and the full batch does not cover the mandatory trend requirements above, REWRITE the batch before returning it.

---

📬 OUTPUT FORMAT:

Generate EXACTLY {num_posts} posts in a JSON array. Each object must include:
- post_type: one of the content pillars above
- idea_summary (max 15 words)
- reel_or_static: the post format, following the {platform_label} format rules above
- hook (max 12 words, VERY STRONG)
- caption (high-converting, length appropriate for {platform_label} per the format rules above)
- hashtags (per the {platform_label} format rules above — as a single comma-separated string, or "" if not applicable)
- image_prompt (cinematic, detailed, 40-60 word visual generation prompt for Midjourney/Runway/Kling)
- cta: the call to action
- notes_for_creator (production notes: cuts, pacing, text overlays, or posting tips as relevant to {platform_label}; if trends were provided, start with "Trend used: [exact trend title(s)].")
- script: a full shooting/writing script for this specific post, ADAPTED TO ITS FORMAT —
  for a Reel/video format give shot-by-shot beats with approximate timestamps (e.g. "0-2s: ...");
  if using an extended educational Reel trend, use 60-180 seconds with clear sections like hook, setup,
  teaching steps, example, recap, and CTA;
  for a Carousel give slide-by-slide text/visual breakdown (e.g. "Slide 1: ..."); for a static
  image or text post give the on-screen copy plus visual direction. Be concrete, not generic.
- editing_style: concrete editing/production direction matched to the format — for video: pacing,
  cut frequency, transitions, text-overlay timing, music/sound energy; for carousels: slide pacing,
  visual consistency notes, swipe-through logic; for static/text posts: layout, visual hierarchy,
  design treatment. Keep it actionable for whoever is producing the piece.

---

📁 DO NOT REPEAT THESE PAST POSTS:

{history_summary}

---

Return ONLY valid JSON array. No explanations. No markdown. No extra text."""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    raw = response.text.strip()
    parsed = json.loads(raw)
    # Gemini occasionally returns a bare object instead of a single-item array when num_posts=1
    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed


def generate_post_from_idea(company: dict, platform: str, idea: str, history: dict, api_key=None, model_name="gemini-2.5-flash", trend_context: str = ""):
    """Turn a user-supplied idea into one fully produced post (same schema as generate_posts),
    instead of letting the model pick a topic from the content pillars."""
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        api_key_env = os.environ.get("GEMINI_API_KEY")
        if not api_key_env:
            raise ValueError("GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY environment variable or configure it in the dashboard settings.")
        client = genai.Client(api_key=api_key_env)

    history_summary = build_history_summary(history)
    format_guidance = PLATFORM_FORMAT_GUIDANCE.get(platform, PLATFORM_FORMAT_GUIDANCE["instagram"])
    platform_label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())

    trend_block = ""
    if trend_context:
        trend_block = f"""
🔥 RELEVANT TREND CONTEXT (use it if it strengthens the idea below — don't force it in):

{trend_context}

---
"""

    prompt = f"""You are an ELITE {platform_label} Growth Strategist & Content Director for {company.get('name', 'this brand')}.

The user has a SPECIFIC CONTENT IDEA they want turned into one fully produced, high-converting {platform_label} post. Do NOT replace or drift from their idea — expand and execute it at an elite level.

---

💡 USER'S IDEA (MANDATORY BRIEF — build the post around exactly this):

{idea}

---

🔥 BUSINESS CONTEXT:

{company.get('business_context', 'No business context provided.')}

---

🎯 TARGET AUDIENCE (CRITICAL):

{company.get('target_audience', 'General audience.')}

Speak DIRECTLY to their pain points and goals.

---

🗣️ BRAND VOICE:

{company.get('brand_voice', 'Confident, clear, helpful.')}

---

🔥 {platform_label.upper()} FORMAT RULES:
{format_guidance}

---
{trend_block}
HOOK WRITING (CRITICAL):

Hooks MUST create curiosity, use numbers, sound surprising, or call out the audience directly. Never use generic hooks like "Elevate your brand".

---

CTA (MANDATORY):

End the caption with EXACTLY:
{company.get('cta_text') or 'Learn more — link in bio.'}

---

QUALITY CONTROL (VERY IMPORTANT):

Score the post on Hook Strength, Platform-fit/Virality, and Conversion Potential (1-10 each).
If ANY score is below 8, REWRITE it completely before returning. Do NOT output weak content.

---

📁 DO NOT REPEAT THESE PAST POSTS:

{history_summary}

---

📬 OUTPUT FORMAT:

Return ONE JSON object (not an array) with:
- post_type: the content pillar/category this idea best fits
- idea_summary (max 15 words, grounded in the user's idea)
- reel_or_static: the post format, following the {platform_label} format rules above
- hook (max 12 words, VERY STRONG)
- caption (high-converting, length appropriate for {platform_label} per the format rules above)
- hashtags (per the {platform_label} format rules above — as a single comma-separated string, or "" if not applicable)
- image_prompt (cinematic, detailed, 40-60 word visual generation prompt for Midjourney/Runway/Kling)
- cta: the call to action
- notes_for_creator (production notes: cuts, pacing, text overlays, or posting tips)
- script: a full shooting/writing script adapted to the format —
  for a Reel/video give shot-by-shot beats with approximate timestamps (e.g. "0-2s: ...");
  for a Carousel give slide-by-slide text/visual breakdown (e.g. "Slide 1: ...");
  for a static image or text post give the on-screen copy plus visual direction. Be concrete, not generic.
- editing_style: concrete editing/production direction matched to the format

Return ONLY valid JSON. No explanations. No markdown. No extra text."""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    raw = response.text.strip()
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        parsed = parsed[0]
    return parsed


def build_schedule(posts, best_times=None, start_date=None, start_post_number=1):
    best_times = [tuple(t) for t in (best_times or DEFAULT_BEST_TIMES)]
    start_from = start_date or datetime.now()
    schedule = []
    day_offset = 0

    for i, post in enumerate(posts):
        day_name, time_str = best_times[(i + start_post_number - 1) % len(best_times)]
        while True:
            candidate = start_from + timedelta(days=day_offset)
            if candidate.strftime("%A") == day_name:
                break
            day_offset += 1
        schedule.append({
            **post,
            "date": candidate.strftime("%d %b %Y"),
            "day": day_name,
            "time": time_str,
            "post_number": start_post_number + i,
        })
        day_offset += 1

    return schedule


def create_excel(company: dict, scheduled_posts, output_path=None):
    wb = Workbook()
    company_name = company.get("name", "Content Calendar")
    output_path = output_path or OUTPUT_FILE

    # ── Sheet 1: Content Calendar ──────────────────────────────────────────
    ws = wb.active
    ws.title = "Content Calendar"

    PURPLE   = "7F77DD"
    LAVENDER = "EEEDFE"
    TEAL     = "1D9E75"
    TEAL_LT  = "E1F5EE"
    AMBER    = "BA7517"
    AMBER_LT = "FAEEDA"
    GRAY_LT  = "F8F8F6"
    WHITE    = "FFFFFF"
    DARK     = "2C2C2A"

    def hdr_fill(hex_color):
        return PatternFill("solid", start_color=hex_color, fgColor=hex_color)

    def thin_border():
        s = Side(style="thin", color="D3D1C7")
        return Border(left=s, right=s, top=s, bottom=s)

    def cell_style(ws, row, col, value, bold=False, bg=None, fg=DARK, wrap=False, size=10, align="left"):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(name="Arial", bold=bold, color=fg, size=size)
        if bg:
            c.fill = hdr_fill(bg)
        c.alignment = Alignment(horizontal=align, vertical="top", wrap_text=wrap)
        c.border = thin_border()
        return c

    ws.merge_cells("A1:L1")
    title = ws["A1"]
    title.value = f"{company_name.upper()} — Content Calendar"
    title.font = Font(name="Arial", bold=True, color=WHITE, size=14)
    title.fill = hdr_fill(PURPLE)
    title.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:L2")
    sub = ws["A2"]
    sub.value = f"Generated {datetime.now().strftime('%d %b %Y')} | {len(scheduled_posts)} posts planned"
    sub.font = Font(name="Arial", color=DARK, size=9, italic=True)
    sub.fill = hdr_fill(LAVENDER)
    sub.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    headers = [
        "#", "Date", "Day & Time", "Platform", "Post Type", "Format",
        "Hook (First Line)", "Caption", "Hashtags",
        "Image / Reel Prompt", "Script", "Editing Style", "CTA", "Notes for Creator"
    ]
    col_widths = [4, 12, 28, 14, 22, 14, 28, 55, 40, 50, 55, 40, 30, 38]

    for col, (h, w) in enumerate(zip(headers, col_widths), start=1):
        cell_style(ws, 3, col, h, bold=True, bg=TEAL, fg=WHITE, align="center")
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.row_dimensions[3].height = 18

    for i, post in enumerate(scheduled_posts):
        row = i + 4
        bg = WHITE if i % 2 == 0 else GRAY_LT

        is_done = post.get("is_done", False)
        num_display = f"✓ {post['post_number']}" if is_done else post["post_number"]
        num_bg = TEAL_LT if is_done else bg
        platform_label = PLATFORM_LABELS.get(post.get("platform", "instagram"), str(post.get("platform", "instagram")).replace("_", " ").title())

        cell_style(ws, row, 1,  num_display,              bg=num_bg, align="center")
        cell_style(ws, row, 2,  post["date"],              bg=bg, align="center")
        cell_style(ws, row, 3,  f"{post['day']}\n{post['time']}", bg=bg, wrap=True)
        cell_style(ws, row, 4,  platform_label,            bg=bg, align="center")
        cell_style(ws, row, 5,  post["post_type"],         bg=AMBER_LT, fg=AMBER, wrap=True)
        cell_style(ws, row, 6,  post["reel_or_static"],    bg=bg, align="center")
        cell_style(ws, row, 7,  post["hook"],              bg=bg, bold=True, wrap=True)
        cell_style(ws, row, 8,  post["caption"],           bg=bg, wrap=True)
        cell_style(ws, row, 9,  post["hashtags"],          bg=bg, wrap=True)
        cell_style(ws, row, 10, post["image_prompt"],      bg=TEAL_LT, wrap=True)
        cell_style(ws, row, 11, post.get("script", ""),        bg=bg, wrap=True)
        cell_style(ws, row, 12, post.get("editing_style", ""), bg=bg, wrap=True)
        cell_style(ws, row, 13, post["cta"],               bg=bg, wrap=True)
        cell_style(ws, row, 14, post["notes_for_creator"], bg=bg, wrap=True)

        ws.row_dimensions[row].height = 90

    ws.freeze_panes = "A4"

    # ── Sheet 2: Image Prompts (standalone for easy copy-paste) ────────────
    ws2 = wb.create_sheet("AI Image Prompts")
    ws2.merge_cells("A1:D1")
    t2 = ws2["A1"]
    t2.value = "AI IMAGE & REEL GENERATION PROMPTS — Copy and paste into Midjourney / RunwayML / Kling"
    t2.font = Font(name="Arial", bold=True, color=WHITE, size=12)
    t2.fill = hdr_fill(PURPLE)
    t2.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 28

    h2 = ["#", "Post Type & Hook", "Full Generation Prompt", "Tool Suggestion"]
    w2 = [4, 35, 80, 22]
    for col, (h, w) in enumerate(zip(h2, w2), start=1):
        c = ws2.cell(row=2, column=col, value=h)
        c.font = Font(name="Arial", bold=True, color=WHITE, size=10)
        c.fill = hdr_fill(TEAL)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border()
        ws2.column_dimensions[get_column_letter(col)].width = w
    ws2.row_dimensions[2].height = 18

    for i, post in enumerate(scheduled_posts):
        row = i + 3
        bg = WHITE if i % 2 == 0 else GRAY_LT
        tool = "RunwayML / Kling" if post["reel_or_static"] in ("Reel",) else "Midjourney / Leonardo"

        for col, (val, wrap) in enumerate([
            (post["post_number"], False),
            (f"{post['post_type']}\n\"{post['hook']}\"", True),
            (post["image_prompt"], True),
            (tool, False),
        ], start=1):
            c = ws2.cell(row=row, column=col, value=val)
            c.font = Font(name="Arial", size=10, color=DARK)
            c.fill = hdr_fill(bg)
            c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=wrap)
            c.border = thin_border()
        ws2.row_dimensions[row].height = 70

    ws2.freeze_panes = "A3"

    # ── Sheet 3: Caption Bank ────────────────────────────────────────────
    ws3 = wb.create_sheet("Caption & Hashtag Bank")
    ws3.merge_cells("A1:C1")
    t3 = ws3["A1"]
    t3.value = "CAPTION & HASHTAG BANK — Copy directly to your scheduler"
    t3.font = Font(name="Arial", bold=True, color=WHITE, size=12)
    t3.fill = hdr_fill(PURPLE)
    t3.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 28

    h3 = ["Post # & Date", "Full Caption", "Hashtags (copy separately)"]
    w3 = [20, 80, 55]
    for col, (h, w) in enumerate(zip(h3, w3), start=1):
        c = ws3.cell(row=2, column=col, value=h)
        c.font = Font(name="Arial", bold=True, color=WHITE, size=10)
        c.fill = hdr_fill(TEAL)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border()
        ws3.column_dimensions[get_column_letter(col)].width = w
    ws3.row_dimensions[2].height = 18

    for i, post in enumerate(scheduled_posts):
        row = i + 3
        bg = WHITE if i % 2 == 0 else GRAY_LT
        platform_label = PLATFORM_LABELS.get(post.get("platform", "instagram"), str(post.get("platform", "instagram")).replace("_", " ").title())
        label = f"Post {post['post_number']} — {post['date']}\n{platform_label} / {post['reel_or_static']}"

        for col, (val, wrap) in enumerate([
            (label, True),
            (post["caption"], True),
            (post["hashtags"], True),
        ], start=1):
            c = ws3.cell(row=row, column=col, value=val)
            c.font = Font(name="Arial", size=10, color=DARK)
            c.fill = hdr_fill(bg)
            c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=wrap)
            c.border = thin_border()
        ws3.row_dimensions[row].height = 110

    ws3.freeze_panes = "A3"

    wb.save(output_path)
    print(f"✅ Excel saved: {output_path}")
    return output_path
