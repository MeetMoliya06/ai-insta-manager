import json
import os
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv, set_key

# Import functions from social_media_agent
import social_media_agent as agent

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if supabase_url and supabase_key:
        print("☁️ Supabase configured. Checking cloud data synchronization...")
        try:
            # Check if settings are synced
            settings = agent.fetch_settings_supabase()
            if not settings:
                print("🔄 Initializing Supabase cloud sync & replicating local data...")
                gemini_api_key = os.environ.get("GEMINI_API_KEY")
                insta_user = os.environ.get("INSTAGRAM_USERNAME")
                insta_pass = os.environ.get("INSTAGRAM_PASSWORD")
                agent.save_settings_supabase(gemini_key=gemini_api_key, insta_user=insta_user, insta_pass=insta_pass)
                
                # Sync history
                local_history = agent.load_history()
                if local_history and local_history.get("posts"):
                    agent.save_history_supabase(local_history["posts"])
                    
                # Sync calendar
                local_calendar = load_current_calendar()
                if local_calendar:
                    agent.save_calendar_supabase(local_calendar)
                print("✅ Supabase cloud database synchronization complete!")
            else:
                print("✅ Supabase cloud settings found and loaded.")
        except Exception as e:
            print(f"⚠️ Automatic Supabase sync failed on startup: {e}")
    yield

app = FastAPI(
    title="New Gen Studios — AI Social Media Manager Dashboard",
    lifespan=lifespan
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


CALENDAR_FILE = "current_calendar.json"

class ConfigResponse(BaseModel):
    has_api_key: bool
    default_pillars: List[str]
    has_instagram: bool
    instagram_username: Optional[str] = None
    has_supabase: bool
    supabase_url: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    api_key: str

class InstagramConfigRequest(BaseModel):
    username: str
    password: str

class SupabaseConfigRequest(BaseModel):
    url: str
    key: str



class GenerateRequest(BaseModel):
    weeks: int = 2
    posts_per_week: int = 4
    pillars: List[str] = []
    model_name: str = "gemini-2.5-flash"

class PostItem(BaseModel):
    post_number: int
    date: str
    day: str
    time: str
    post_type: str
    reel_or_static: str
    hook: str
    caption: str
    hashtags: str
    image_prompt: str
    cta: str
    notes_for_creator: str
    is_done: bool = False

class SaveRequest(BaseModel):
    posts: List[PostItem]

# Ensure files exist or load them
def load_current_calendar() -> List[dict]:
    # 1. Try loading from Supabase first
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if supabase_url and supabase_key:
        calendar = agent.load_calendar_supabase()
        if calendar is not None:
            return calendar

    # 2. Local fallback
    if os.path.exists(CALENDAR_FILE):
        try:
            with open(CALENDAR_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_current_calendar(posts: List[dict]):
    # 1. Try saving to Supabase first
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if supabase_url and supabase_key:
        agent.save_calendar_supabase(posts)

    # 2. Local backup
    with open(CALENDAR_FILE, "w") as f:
        json.dump(posts, f, indent=2)


@app.get("/api/config", response_model=ConfigResponse)
def get_config():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    has_supabase = bool(supabase_url and supabase_key)
    
    api_key = None
    insta_user = None
    insta_pass = None
    
    # If Supabase is connected, dynamically load all settings from Supabase
    if has_supabase:
        settings = agent.fetch_settings_supabase()
        if settings:
            api_key = settings.get("gemini_api_key")
            insta_user = settings.get("instagram_username")
            insta_pass = settings.get("instagram_password")
            
            # Keep process env synchronized so libraries work seamlessly
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
            if insta_user:
                os.environ["INSTAGRAM_USERNAME"] = insta_user
            if insta_pass:
                os.environ["INSTAGRAM_PASSWORD"] = insta_pass

    # Local fallback/secondary source
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not insta_user:
        insta_user = os.environ.get("INSTAGRAM_USERNAME")
    if not insta_pass:
        insta_pass = os.environ.get("INSTAGRAM_PASSWORD")

    return {
        "has_api_key": bool(api_key),
        "default_pillars": agent.CONTENT_PILLARS,
        "has_instagram": bool(insta_user and insta_pass),
        "instagram_username": insta_user,
        "has_supabase": has_supabase,
        "supabase_url": supabase_url
    }


@app.post("/api/config")
def update_config(data: ConfigUpdateRequest):
    key = data.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")
    
    # 1. Save locally to .env
    env_path = ".env"
    set_key(env_path, "GEMINI_API_KEY", key)
    os.environ["GEMINI_API_KEY"] = key
    
    # 2. Save to Supabase if active
    agent.save_settings_supabase(gemini_key=key)
    
    return {"status": "success", "message": "Gemini API Key updated successfully"}

@app.post("/api/instagram/config")
def update_instagram_config(data: InstagramConfigRequest):
    username = data.username.strip()
    password = data.password.strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Instagram Username and Password cannot be empty")
    
    # 1. Save locally to .env
    env_path = ".env"
    set_key(env_path, "INSTAGRAM_USERNAME", username)
    set_key(env_path, "INSTAGRAM_PASSWORD", password)
    
    # Update current process environment
    os.environ["INSTAGRAM_USERNAME"] = username
    os.environ["INSTAGRAM_PASSWORD"] = password
    
    # Clean old session if credentials change
    if os.path.exists(agent.SESSION_FILE):
        try:
            os.remove(agent.SESSION_FILE)
        except Exception:
            pass
            
    # 2. Save to Supabase if active
    agent.save_settings_supabase(insta_user=username, insta_pass=password)
            
    return {"status": "success", "message": "Instagram credentials updated successfully"}

@app.post("/api/supabase/config")
def update_supabase_config(data: SupabaseConfigRequest):
    url = data.url.strip()
    key = data.key.strip()
    if not url or not key:
        raise HTTPException(status_code=400, detail="Supabase URL and Anon Key cannot be empty")
        
    # 1. Save locally to .env
    env_path = ".env"
    set_key(env_path, "SUPABASE_URL", url)
    set_key(env_path, "SUPABASE_KEY", key)
    
    # 2. Update process environment
    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_KEY"] = key
    
    # 3. Auto-sync existing local data to newly connected Supabase cloud database
    try:
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        insta_user = os.environ.get("INSTAGRAM_USERNAME")
        insta_pass = os.environ.get("INSTAGRAM_PASSWORD")
        agent.save_settings_supabase(gemini_key=gemini_api_key, insta_user=insta_user, insta_pass=insta_pass)
    except Exception as e:
        print(f"⚠️ Settings sync failed: {e}")
        
    try:
        local_history = agent.load_history()
        if local_history and local_history.get("posts"):
            agent.save_history_supabase(local_history["posts"])
    except Exception as e:
        print(f"⚠️ History sync failed: {e}")
        
    try:
        local_calendar = load_current_calendar()
        if local_calendar:
            agent.save_calendar_supabase(local_calendar)
    except Exception as e:
        print(f"⚠️ Calendar sync failed: {e}")
        
    return {"status": "success", "message": "Supabase connected and local database synchronized to cloud successfully!"}


@app.get("/api/instagram/profile")
def get_instagram_profile():
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    if not username or not password:
        return {"status": "offline", "message": "Instagram credentials not configured."}
        
    try:
        profile_data = agent.fetch_instagram_profile_data(username, password)
        return {"status": "online", "data": profile_data}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

@app.get("/api/history")
def get_history():
    try:
        # 1. Instagram live check first
        insta_user = os.environ.get("INSTAGRAM_USERNAME")
        insta_pass = os.environ.get("INSTAGRAM_PASSWORD")
        if insta_user and insta_pass:
            try:
                return agent.fetch_instagram_history(insta_user, insta_pass)
            except Exception as e:
                print(f"⚠️ Dynamic Instagram history load failed: {e}. Falling back to database/file.")

        # 2. Try loading from Supabase history
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if supabase_url and supabase_key:
            history = agent.load_history_supabase()
            if history is not None:
                return history
                
        # 3. Fallback to local posts_history.json
        return agent.load_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")


@app.get("/api/calendar")
def get_calendar():
    return load_current_calendar()

@app.post("/api/generate")
def generate_calendar(req: GenerateRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400, 
            detail="Gemini API Key is not set. Please set it in the Settings panel."
        )
    
    try:
        # 1. Load history dynamically from Instagram/Supabase if configured, fallback to local json
        insta_user = os.environ.get("INSTAGRAM_USERNAME")
        insta_pass = os.environ.get("INSTAGRAM_PASSWORD")
        history = None
        
        if insta_user and insta_pass:
            try:
                print("Retrieving Instagram post history dynamically...")
                history = agent.fetch_instagram_history(insta_user, insta_pass)
            except Exception as e:
                print(f"⚠️ Dynamic Instagram history fetch failed: {e}. Falling back to database/file.")
                
        if not history:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            if supabase_url and supabase_key:
                history = agent.load_history_supabase()
                
        if not history:
            history = agent.load_history()


        
        # 2. Run LLM generation
        num_posts = req.weeks * req.posts_per_week
        raw_posts = agent.generate_posts(
            history=history,
            num_posts=num_posts,
            api_key=api_key,
            model_name=req.model_name,
            custom_pillars=req.pillars if req.pillars else None
        )
        
        # 3. Apply schedule
        # Temp override BEST_TIMES or POSTS_PER_WEEK if needed, but build_schedule works out-of-the-box
        scheduled_posts = agent.build_schedule(raw_posts)
        
        # 4. Save to temporary current calendar (so user can edit in dashboard before exporting/committing)
        save_current_calendar(scheduled_posts)
        
        return scheduled_posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/save")
def save_calendar(req: SaveRequest):
    try:
        posts_dict = [p.model_dump() for p in req.posts]
        save_current_calendar(posts_dict)
        return {"status": "success", "message": "Calendar changes saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save changes: {str(e)}")

@app.post("/api/export")
def export_calendar(req: SaveRequest):
    try:
        posts_dict = [p.model_dump() for p in req.posts]
        
        # 1. Save current state to current_calendar.json
        save_current_calendar(posts_dict)
        
        # 2. Create the styled Excel workbook
        agent.create_excel(posts_dict)
        
        # 3. Add new posts to history (deduplicated by date + idea_summary)
        history = None
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if supabase_url and supabase_key:
            history = agent.load_history_supabase()
            
        if not history:
            history = agent.load_history()
            
        history_posts = history.get("posts", [])
        history_keys = {(p.get("date"), p.get("idea_summary")) for p in history_posts}
        
        added_count = 0
        for post in posts_dict:
            key = (post["date"], post["idea_summary"])
            if key not in history_keys:
                history_posts.append({
                    "date": post["date"],
                    "post_type": post["post_type"],
                    "idea_summary": post["idea_summary"],
                    "reel_or_static": post["reel_or_static"],
                })
                added_count += 1
        
        if added_count > 0:
            history["posts"] = history_posts
            if supabase_url and supabase_key:
                agent.save_history_supabase(history_posts)
            # Save local as backup
            agent.save_history(history)

            
        # 4. Return the Excel file for download
        if os.path.exists(agent.OUTPUT_FILE):
            return FileResponse(
                path=agent.OUTPUT_FILE, 
                filename=agent.OUTPUT_FILE, 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise HTTPException(status_code=500, detail="Excel file was not created successfully")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Serve frontend static files
# Make sure the static folder exists
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Automatically running on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
