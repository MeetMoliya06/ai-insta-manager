import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv, set_key

import social_media_agent as agent
import research_agent
import content_generator
from platforms import get_connector, PLATFORMS, PLATFORM_LABELS

load_dotenv()

ENV_PATH = ".env"
EXPORT_DIR = "exports"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(agent.DATA_DIR, exist_ok=True)
    yield


app = FastAPI(title="AI Social Media Manager Dashboard", lifespan=lifespan)


@app.middleware("http")
async def no_cache(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def supabase_configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"))


# ──────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────

class GeminiConfigRequest(BaseModel):
    api_key: str


class SupabaseConfigRequest(BaseModel):
    url: str
    key: str


class CompanyRequest(BaseModel):
    name: str
    industry: str = ""
    business_context: str = ""
    target_audience: str = ""
    brand_voice: str = ""
    content_pillars: List[str] = []
    cta_text: str = ""
    best_times: List[List[str]] = []
    website_url: str = ""
    auto_research: bool = False


class ResearchRequest(BaseModel):
    website_url: Optional[str] = None
    socials_hint: Optional[str] = None


class ConnectionRequest(BaseModel):
    credentials: Dict[str, Any]
    auth_type: str = "password"


class GenerateRequest(BaseModel):
    platform: str = "instagram"
    weeks: int = 2
    posts_per_week: int = 4
    pillars: List[str] = []
    model_name: str = "gemini-2.5-flash"
    append_to_existing: bool = True
    use_trends: bool = False


class IdeaGenerateRequest(BaseModel):
    idea: str
    platform: str = "instagram"
    model_name: str = "gemini-2.5-flash"
    use_trends: bool = False


class PostItem(BaseModel):
    post_number: int
    platform: str = "instagram"
    date: str
    day: str
    time: str
    post_type: str
    idea_summary: str = ""
    reel_or_static: str
    hook: str
    caption: str
    hashtags: str
    image_prompt: str
    script: str = ""
    editing_style: str = ""
    cta: str
    notes_for_creator: str
    is_done: bool = False
    image_url: Optional[str] = None


class SaveRequest(BaseModel):
    posts: List[PostItem]


class GenerateImageRequest(BaseModel):
    post_index: int


# ──────────────────────────────────────────────────────────
# Operator-level settings (Gemini key, Supabase connection)
# ──────────────────────────────────────────────────────────

@app.get("/api/config")
def get_config():
    has_supabase = supabase_configured()
    api_key = None

    if has_supabase:
        settings = agent.fetch_settings_supabase()
        if settings and settings.get("gemini_api_key"):
            api_key = settings["gemini_api_key"]
            os.environ["GEMINI_API_KEY"] = api_key

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    return {
        "has_api_key": bool(api_key),
        "default_pillars": agent.DEFAULT_CONTENT_PILLARS,
        "default_best_times": agent.DEFAULT_BEST_TIMES,
        "platforms": PLATFORMS,
        "platform_labels": PLATFORM_LABELS,
        "has_supabase": has_supabase,
        "supabase_url": os.environ.get("SUPABASE_URL"),
    }


@app.post("/api/config")
def update_gemini_config(data: GeminiConfigRequest):
    key = data.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")
    set_key(ENV_PATH, "GEMINI_API_KEY", key)
    os.environ["GEMINI_API_KEY"] = key
    agent.save_settings_supabase(gemini_key=key)
    return {"status": "success", "message": "Gemini API Key updated successfully"}


@app.post("/api/supabase/config")
def update_supabase_config(data: SupabaseConfigRequest):
    url = data.url.strip()
    key = data.key.strip()
    if not url or not key:
        raise HTTPException(status_code=400, detail="Supabase URL and Anon Key cannot be empty")

    set_key(ENV_PATH, "SUPABASE_URL", url)
    set_key(ENV_PATH, "SUPABASE_KEY", key)
    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_KEY"] = key

    try:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        agent.save_settings_supabase(gemini_key=gemini_api_key)
    except Exception as e:
        print(f"⚠️ Settings sync failed: {e}")

    return {"status": "success", "message": "Supabase connected successfully!"}


# ──────────────────────────────────────────────────────────
# Company data-access helpers (Supabase-first, local-file fallback)
# ──────────────────────────────────────────────────────────

def list_companies() -> List[dict]:
    if supabase_configured():
        rows = agent.list_companies_supabase()
        if rows is not None:
            return rows
    return agent.load_companies_local()


def find_company(company_id: str) -> dict:
    for c in list_companies():
        if str(c.get("id")) == str(company_id):
            return c
    raise HTTPException(status_code=404, detail="Company not found")


def create_company(data: dict) -> dict:
    if supabase_configured():
        row = agent.create_company_supabase(data)
        if row:
            return row
    return agent.create_company_local(data)


def update_company(company_id: str, data: dict) -> dict:
    if supabase_configured():
        row = agent.update_company_supabase(company_id, data)
        if row:
            return row
    row = agent.update_company_local(company_id, data)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def delete_company(company_id: str):
    if supabase_configured():
        agent.delete_company_supabase(company_id)
    agent.delete_company_local(company_id)


def get_connections_map(company_id: str) -> Dict[str, dict]:
    if supabase_configured():
        rows = agent.list_connections_supabase(company_id)
        if rows is not None:
            return {r["platform"]: r for r in rows}
    local = agent.load_connections_local(company_id)
    return {platform: {**info, "platform": platform} for platform, info in local.items()}


def save_connection(company_id: str, platform: str, credentials: dict, auth_type: str = "password"):
    if supabase_configured():
        agent.save_connection_supabase(company_id, platform, credentials, auth_type)
    agent.save_connection_local(company_id, platform, credentials, auth_type)


def delete_connection(company_id: str, platform: str):
    if supabase_configured():
        agent.delete_connection_supabase(company_id, platform)
    agent.delete_connection_local(company_id, platform)


def get_calendar(company_id: str) -> List[dict]:
    if supabase_configured():
        cal = agent.load_calendar_supabase(company_id)
        if cal is not None:
            return cal
    return agent.load_calendar_local(company_id)


def save_calendar(company_id: str, posts: List[dict]):
    if supabase_configured():
        agent.save_calendar_supabase(company_id, posts)
    agent.save_calendar_local(company_id, posts)


def get_history(company_id: str, platform: str) -> dict:
    connections = get_connections_map(company_id)
    conn = connections.get(platform)
    if conn and platform == "instagram":
        try:
            connector = get_connector(platform, conn.get("credentials", {}))
            return {"posts": connector.fetch_recent_posts()}
        except Exception as e:
            print(f"⚠️ Live {platform} history fetch failed: {e}. Falling back to stored history.")

    if supabase_configured():
        hist = agent.load_history_supabase(company_id, platform)
        if hist is not None:
            return hist
    return agent.load_history_local(company_id, platform)


def save_history(company_id: str, platform: str, posts: List[dict]):
    if supabase_configured():
        agent.save_history_supabase(company_id, platform, posts)
    agent.save_history_local(company_id, platform, posts)


def get_trend_cache(company_id: str, platform: str) -> Optional[dict]:
    if supabase_configured():
        cached = agent.load_trend_cache_supabase(company_id, platform)
        if cached is not None:
            return cached
        return None
    return agent.load_trend_cache_local(company_id, platform)


def save_trend_cache(company_id: str, platform: str, trend_data: dict):
    if supabase_configured():
        agent.save_trend_cache_supabase(company_id, platform, trend_data)
    agent.save_trend_cache_local(company_id, platform, trend_data)


def get_gemini_api_key() -> Optional[str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    if supabase_configured():
        settings = agent.fetch_settings_supabase()
        if settings and settings.get("gemini_api_key"):
            os.environ["GEMINI_API_KEY"] = settings["gemini_api_key"]
            return settings["gemini_api_key"]
    return None


# ──────────────────────────────────────────────────────────
# Company CRUD endpoints
# ──────────────────────────────────────────────────────────

@app.get("/api/companies")
def api_list_companies():
    return list_companies()


@app.post("/api/companies")
def api_create_company(req: CompanyRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Company name is required")
    company = create_company(req.model_dump())

    if req.auto_research and req.website_url.strip():
        api_key = get_gemini_api_key()
        if api_key:
            try:
                result = research_agent.research_company(
                    name=company.get("name", req.name),
                    website_url=req.website_url.strip(),
                    industry_hint=req.industry,
                    api_key=api_key,
                )
                update_payload = {
                    "industry": result.get("industry") or company.get("industry", ""),
                    "business_context": result.get("business_context", ""),
                    "target_audience": result.get("target_audience", ""),
                    "brand_voice": result.get("brand_voice", ""),
                    "content_pillars": result.get("content_pillars") or company.get("content_pillars"),
                    "cta_text": result.get("cta_suggestion") or company.get("cta_text", ""),
                    "last_researched_at": result.get("researched_at"),
                    "research_summary": result.get("summary", ""),
                    "research_sources": result.get("sources", []),
                }
                company = update_company(company["id"], update_payload)
            except Exception as e:
                # Auto-research failing shouldn't block company creation — the user can re-run manually.
                print(f"⚠️ Auto-research failed for new company '{req.name}': {e}")

    return company


@app.get("/api/companies/{company_id}")
def api_get_company(company_id: str):
    return find_company(company_id)


@app.put("/api/companies/{company_id}")
def api_update_company(company_id: str, req: CompanyRequest):
    find_company(company_id)
    return update_company(company_id, req.model_dump())


@app.delete("/api/companies/{company_id}")
def api_delete_company(company_id: str):
    find_company(company_id)
    delete_company(company_id)
    return {"status": "success"}


@app.post("/api/companies/{company_id}/research")
def api_research_company(company_id: str, req: ResearchRequest):
    company = find_company(company_id)
    website_url = (req.website_url or company.get("website_url") or "").strip()
    if not website_url:
        raise HTTPException(status_code=400, detail="Add a website URL before running research.")

    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is not set. Please set it in the Settings panel.")

    try:
        result = research_agent.research_company(
            name=company.get("name", ""),
            website_url=website_url,
            industry_hint=company.get("industry", ""),
            socials_hint=req.socials_hint or "",
            api_key=api_key,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

    update_payload = {
        "website_url": website_url,
        "industry": result.get("industry") or company.get("industry", ""),
        "business_context": result.get("business_context", ""),
        "target_audience": result.get("target_audience", ""),
        "brand_voice": result.get("brand_voice", ""),
        "content_pillars": result.get("content_pillars") or company.get("content_pillars"),
        "cta_text": result.get("cta_suggestion") or company.get("cta_text", ""),
        "last_researched_at": result.get("researched_at"),
        "research_summary": result.get("summary", ""),
        "research_sources": result.get("sources", []),
    }
    return update_company(company_id, update_payload)


@app.get("/api/companies/{company_id}/trends")
def api_get_trends(company_id: str, platform: str = "instagram", refresh: bool = False):
    company = find_company(company_id)
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform '{platform}'")

    cached = get_trend_cache(company_id, platform)
    if cached and not refresh and research_agent.is_cache_fresh(cached.get("fetched_at")):
        return {**cached, "from_cache": True}

    api_key = get_gemini_api_key()
    if not api_key:
        if cached:
            # Serve stale cache rather than failing outright if there's nothing else we can do.
            return {**cached, "from_cache": True, "stale": True}
        raise HTTPException(status_code=400, detail="Gemini API Key is not set. Please set it in the Settings panel.")

    try:
        platform_label = PLATFORM_LABELS.get(platform, platform.replace("_", " ").title())
        trend_data = research_agent.fetch_trends(
            company=company,
            platform=platform,
            platform_label=platform_label,
            api_key=api_key,
        )
        save_trend_cache(company_id, platform, trend_data)
        return {**trend_data, "from_cache": False}
    except Exception as e:
        if cached:
            return {**cached, "from_cache": True, "stale": True}
        raise HTTPException(status_code=500, detail=f"Trend fetch failed: {str(e)}")


# ──────────────────────────────────────────────────────────
# Platform connection endpoints
# ──────────────────────────────────────────────────────────

def connection_public_view(platform: str, conn: Optional[dict]) -> dict:
    if not conn:
        return {"platform": platform, "status": "not_connected"}
    view = {
        "platform": platform,
        "status": conn.get("status", "connected"),
        "auth_type": conn.get("auth_type", "password"),
        "connected_at": conn.get("connected_at"),
    }
    creds = conn.get("credentials") or {}
    if "username" in creds:
        view["username"] = creds["username"]
    elif "ig_user_id" in creds:
        view["username"] = creds["ig_user_id"]
    return view


@app.get("/api/companies/{company_id}/connections")
def api_list_connections(company_id: str):
    find_company(company_id)
    connections = get_connections_map(company_id)
    return [connection_public_view(p, connections.get(p)) for p in PLATFORMS]


@app.post("/api/companies/{company_id}/connections/{platform}")
def api_save_connection(company_id: str, platform: str, req: ConnectionRequest):
    find_company(company_id)
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform '{platform}'")
    if platform != "instagram":
        raise HTTPException(
            status_code=400,
            detail=f"{PLATFORM_LABELS.get(platform, platform)} isn't connectable yet — it needs an official developer app (see project docs)."
        )
    has_username_auth = bool(req.credentials.get("username"))
    has_graph_auth = req.credentials.get("access_token") and req.credentials.get("ig_user_id")
    if not has_username_auth and not has_graph_auth:
        raise HTTPException(
            status_code=400,
            detail="Provide an Instagram username (with password for full login, or alone for public profile analysis), or access_token + ig_user_id for the official Graph API",
        )
    auth_type = req.auth_type
    if has_username_auth and not has_graph_auth:
        auth_type = "password" if req.credentials.get("password") else "public"
    save_connection(company_id, platform, req.credentials, auth_type)
    return {"status": "success", "message": f"{PLATFORM_LABELS.get(platform, platform)} connected successfully"}


@app.delete("/api/companies/{company_id}/connections/{platform}")
def api_delete_connection(company_id: str, platform: str):
    find_company(company_id)
    delete_connection(company_id, platform)
    return {"status": "success"}


@app.get("/api/companies/{company_id}/connections/{platform}/stats")
def api_connection_stats(company_id: str, platform: str):
    find_company(company_id)
    connections = get_connections_map(company_id)
    conn = connections.get(platform)
    if not conn:
        return {"status": "offline", "message": f"{PLATFORM_LABELS.get(platform, platform)} is not connected."}
    try:
        connector = get_connector(platform, conn.get("credentials", {}))
        return {"status": "online", "data": connector.fetch_stats()}
    except NotImplementedError as e:
        return {"status": "not_implemented", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}


# ──────────────────────────────────────────────────────────
# History / Calendar / Generation endpoints
# ──────────────────────────────────────────────────────────

@app.get("/api/companies/{company_id}/history")
def api_get_history(company_id: str, platform: str = "instagram"):
    find_company(company_id)
    try:
        return get_history(company_id, platform)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")


@app.get("/api/companies/{company_id}/calendar")
def api_get_calendar(company_id: str):
    find_company(company_id)
    return get_calendar(company_id)


@app.post("/api/companies/{company_id}/calendar/generate-image")
def api_generate_post_image(company_id: str, req: GenerateImageRequest):
    find_company(company_id)

    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is not set. Please set it in the Settings panel.")

    calendar = get_calendar(company_id)
    if req.post_index < 0 or req.post_index >= len(calendar):
        raise HTTPException(status_code=404, detail="Post not found")

    post = calendar[req.post_index]
    try:
        image_url = content_generator.generate_post_image(
            prompt=post.get("image_prompt", ""),
            api_key=api_key,
            company_id=company_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    post["image_url"] = image_url
    save_calendar(company_id, calendar)
    return {"image_url": image_url}


@app.post("/api/companies/{company_id}/generate")
def api_generate_calendar(company_id: str, req: GenerateRequest):
    company = find_company(company_id)

    if req.platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform '{req.platform}'")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is not set. Please set it in the Settings panel.")

    try:
        history = get_history(company_id, req.platform)
        num_posts = req.weeks * req.posts_per_week

        trend_context = ""
        if req.use_trends:
            cached_trends = get_trend_cache(company_id, req.platform)
            if cached_trends:
                trend_context = agent.build_trend_context(cached_trends)

        raw_posts = agent.generate_posts(
            company=company,
            platform=req.platform,
            history=history,
            num_posts=num_posts,
            api_key=api_key,
            model_name=req.model_name,
            custom_pillars=req.pillars if req.pillars else None,
            trend_context=trend_context,
        )
        for p in raw_posts:
            p["platform"] = req.platform

        existing_calendar = get_calendar(company_id)
        existing_for_platform = [p for p in existing_calendar if p.get("platform") == req.platform]

        start_date = None
        start_post_number = 1
        if req.append_to_existing and existing_for_platform:
            start_post_number = max(p.get("post_number", 0) for p in existing_for_platform) + 1
            latest_date = None
            for p in existing_for_platform:
                if p.get("date"):
                    try:
                        d = datetime.strptime(p["date"], "%d %b %Y")
                        if latest_date is None or d > latest_date:
                            latest_date = d
                    except Exception:
                        pass
            if latest_date:
                start_date = latest_date + timedelta(days=1)
        elif not req.append_to_existing:
            existing_calendar = [p for p in existing_calendar if p.get("platform") != req.platform]

        scheduled_posts = agent.build_schedule(
            raw_posts,
            best_times=company.get("best_times"),
            start_date=start_date,
            start_post_number=start_post_number,
        )

        full_calendar = existing_calendar + scheduled_posts
        save_calendar(company_id, full_calendar)
        return full_calendar
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/companies/{company_id}/generate-from-idea")
def api_generate_from_idea(company_id: str, req: IdeaGenerateRequest):
    company = find_company(company_id)

    if req.platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform '{req.platform}'")
    idea = req.idea.strip()
    if not idea:
        raise HTTPException(status_code=400, detail="Idea cannot be empty")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is not set. Please set it in the Settings panel.")

    try:
        history = get_history(company_id, req.platform)

        trend_context = ""
        if req.use_trends:
            cached_trends = get_trend_cache(company_id, req.platform)
            if cached_trends:
                trend_context = agent.build_trend_context(cached_trends)

        raw_post = agent.generate_post_from_idea(
            company=company,
            platform=req.platform,
            idea=idea,
            history=history,
            api_key=api_key,
            model_name=req.model_name,
            trend_context=trend_context,
        )
        raw_post["platform"] = req.platform

        existing_calendar = get_calendar(company_id)
        existing_for_platform = [p for p in existing_calendar if p.get("platform") == req.platform]

        start_post_number = 1
        start_date = None
        if existing_for_platform:
            start_post_number = max(p.get("post_number", 0) for p in existing_for_platform) + 1
            latest_date = None
            for p in existing_for_platform:
                if p.get("date"):
                    try:
                        d = datetime.strptime(p["date"], "%d %b %Y")
                        if latest_date is None or d > latest_date:
                            latest_date = d
                    except Exception:
                        pass
            if latest_date:
                start_date = latest_date + timedelta(days=1)

        scheduled = agent.build_schedule(
            [raw_post],
            best_times=company.get("best_times"),
            start_date=start_date,
            start_post_number=start_post_number,
        )

        full_calendar = existing_calendar + scheduled
        save_calendar(company_id, full_calendar)
        return full_calendar
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/companies/{company_id}/save")
def api_save_calendar(company_id: str, req: SaveRequest):
    find_company(company_id)
    try:
        posts_dict = [p.model_dump() for p in req.posts]
        save_calendar(company_id, posts_dict)
        return {"status": "success", "message": "Calendar changes saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save changes: {str(e)}")


@app.post("/api/companies/{company_id}/export")
def api_export_calendar(company_id: str, req: SaveRequest):
    company = find_company(company_id)
    try:
        posts_dict = [p.model_dump() for p in req.posts]
        save_calendar(company_id, posts_dict)

        output_path = os.path.join(EXPORT_DIR, f"{company.get('slug', company_id)}_content_calendar.xlsx")
        agent.create_excel(company, posts_dict, output_path=output_path)

        posts_by_platform: Dict[str, List[dict]] = {}
        for post in posts_dict:
            posts_by_platform.setdefault(post.get("platform", "instagram"), []).append(post)

        for platform, platform_posts in posts_by_platform.items():
            history = get_history(company_id, platform)
            history_posts = history.get("posts", [])
            history_keys = {(p.get("date"), p.get("idea_summary")) for p in history_posts}

            added = False
            for post in platform_posts:
                key = (post["date"], post["idea_summary"])
                if key not in history_keys:
                    history_posts.append({
                        "date": post["date"],
                        "post_type": post["post_type"],
                        "idea_summary": post["idea_summary"],
                        "reel_or_static": post["reel_or_static"],
                    })
                    added = True

            if added:
                save_history(company_id, platform, history_posts)

        if os.path.exists(output_path):
            return FileResponse(
                path=output_path,
                filename=os.path.basename(output_path),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        raise HTTPException(status_code=500, detail="Excel file was not created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Serve frontend static files
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
