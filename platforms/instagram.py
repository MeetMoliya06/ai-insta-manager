"""Instagram connector.

Two auth modes, picked per-connection by which credentials are present:

- Graph API (official): `access_token` + `ig_user_id` in credentials. Used
  for stats, recent-post history, and publishing. Requires an Instagram
  Business/Creator account linked to a Facebook Page, a Meta developer app,
  and a Page access token with instagram_basic/instagram_content_publish
  permissions.
- `instagrapi` (unofficial, username/password login): fallback for accounts
  without Graph API access. Stats/history only — `publish()` raises for this
  mode, since automated posting through an unofficial/private login is
  unreliable and risks the account.
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from .base import PlatformConnector

SESSION_DIR = "instagram_sessions"
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def _session_path(username: str) -> str:
    os.makedirs(SESSION_DIR, exist_ok=True)
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")) or "default"
    return os.path.join(SESSION_DIR, f"{safe_username}.json")


def _patch_instagrapi_extractors():
    """Patch instagrapi media extractors to tolerate missing video/image fields.

    instagrapi raises TypeError/IndexError on some accounts' media payloads
    when 'video_versions' or 'image_versions2' come back null; strip those
    fields before they reach the (unpatched) extractor functions.
    """
    import sys
    import instagrapi.extractors

    if hasattr(instagrapi.extractors, "_patched_by_newgen"):
        return

    _orig_extract_media_v1 = instagrapi.extractors.extract_media_v1
    _orig_extract_resource_v1 = instagrapi.extractors.extract_resource_v1
    _orig_extract_direct_media = instagrapi.extractors.extract_direct_media
    _orig_extract_story_v1 = instagrapi.extractors.extract_story_v1

    def clean_media_dict(data):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "video_versions" in data and not data["video_versions"]:
            data.pop("video_versions", None)
        if "image_versions2" in data:
            val = data["image_versions2"]
            if not val or not isinstance(val, dict) or not val.get("candidates"):
                data.pop("image_versions2", None)
        # Instagram's newer GraphQL ("XDT") response format sometimes omits 'pk' on
        # carousel resource items, which instagrapi's Resource model requires — derive
        # one from 'id' (format "<media_pk>_<user_pk>") so parsing doesn't crash.
        if not data.get("pk"):
            raw_id = data.get("id")
            data["pk"] = str(raw_id).split("_")[0] if raw_id else "0"
        return data

    patched_extract_media_v1 = lambda data: _orig_extract_media_v1(clean_media_dict(data))
    patched_extract_resource_v1 = lambda data: _orig_extract_resource_v1(clean_media_dict(data))
    patched_extract_direct_media = lambda data: _orig_extract_direct_media(clean_media_dict(data))
    patched_extract_story_v1 = lambda data: _orig_extract_story_v1(clean_media_dict(data))

    instagrapi.extractors.extract_media_v1 = patched_extract_media_v1
    instagrapi.extractors.extract_resource_v1 = patched_extract_resource_v1
    instagrapi.extractors.extract_direct_media = patched_extract_direct_media
    instagrapi.extractors.extract_story_v1 = patched_extract_story_v1
    instagrapi.extractors._patched_by_newgen = True

    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith("instagrapi"):
            if hasattr(mod, "extract_media_v1"):
                mod.extract_media_v1 = patched_extract_media_v1
            if hasattr(mod, "extract_resource_v1"):
                mod.extract_resource_v1 = patched_extract_resource_v1
            if hasattr(mod, "extract_direct_media"):
                mod.extract_direct_media = patched_extract_direct_media
            if hasattr(mod, "extract_story_v1"):
                mod.extract_story_v1 = patched_extract_story_v1


def get_client(username: str, password: str):
    try:
        _patch_instagrapi_extractors()
    except Exception as patch_err:
        print(f"⚠️ Failed to patch instagrapi extractors: {patch_err}")

    from instagrapi import Client
    cl = Client()
    cl.delay_range = [1, 3]

    session_path = _session_path(username)
    if os.path.exists(session_path):
        try:
            cl.load_settings(session_path)
            cl.get_timeline_feed()
            return cl
        except Exception as e:
            print(f"⚠️ Session load failed or expired: {e}. Attempting fresh login...")
            try:
                os.remove(session_path)
            except OSError:
                pass

    cl.login(username, password)
    try:
        cl.dump_settings(session_path)
    except Exception as e:
        print(f"⚠️ Failed to dump Instagram settings: {e}")
    return cl


class InstagramGraphAPI:
    """Thin wrapper over the official Instagram Graph API (Meta)."""

    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = access_token
        self.ig_user_id = ig_user_id

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = dict(params or {})
        params["access_token"] = self.access_token
        resp = requests.get(f"{GRAPH_API_BASE}/{path}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = dict(data or {})
        data["access_token"] = self.access_token
        resp = requests.post(f"{GRAPH_API_BASE}/{path}", data=data, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def user_info(self) -> Dict[str, Any]:
        return self._get(self.ig_user_id, {
            "fields": "username,name,followers_count,follows_count,media_count",
        })

    def recent_media(self, amount: int = 15) -> List[Dict[str, Any]]:
        data = self._get(f"{self.ig_user_id}/media", {
            "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
            "limit": amount,
        })
        return data.get("data", [])

    def publish_photo(self, image_url: str, caption: str) -> Dict[str, Any]:
        container = self._post(f"{self.ig_user_id}/media", {"image_url": image_url, "caption": caption})
        return self._post(f"{self.ig_user_id}/media_publish", {"creation_id": container["id"]})

    def publish_video(self, video_url: str, caption: str, is_reel: bool = True) -> Dict[str, Any]:
        media_type = "REELS" if is_reel else "VIDEO"
        container = self._post(f"{self.ig_user_id}/media", {
            "video_url": video_url,
            "caption": caption,
            "media_type": media_type,
        })
        creation_id = container["id"]

        # Video containers process async server-side — poll until ready before publishing.
        for _ in range(30):
            status = self._get(creation_id, {"fields": "status_code"})
            if status.get("status_code") == "FINISHED":
                break
            if status.get("status_code") == "ERROR":
                raise RuntimeError(f"Instagram video processing failed for creation_id={creation_id}")
            time.sleep(5)

        return self._post(f"{self.ig_user_id}/media_publish", {"creation_id": creation_id})


class InstagramConnector(PlatformConnector):
    platform_id = "instagram"

    def _graph_client(self) -> Optional[InstagramGraphAPI]:
        access_token = self.credentials.get("access_token")
        ig_user_id = self.credentials.get("ig_user_id")
        if access_token and ig_user_id:
            return InstagramGraphAPI(access_token, ig_user_id)
        return None

    def _client(self):
        username = self.credentials.get("username")
        password = self.credentials.get("password")
        if username and password:
            return get_client(username, password), username
        if username:
            scraper_username = os.environ.get("INSTAGRAM_SCRAPER_USERNAME")
            scraper_password = os.environ.get("INSTAGRAM_SCRAPER_PASSWORD")
            if not scraper_username or not scraper_password:
                raise ValueError(
                    "Public profile analysis (username only, no password) needs a server-side "
                    "viewer account — set INSTAGRAM_SCRAPER_USERNAME/INSTAGRAM_SCRAPER_PASSWORD."
                )
            return get_client(scraper_username, scraper_password), username
        raise ValueError("Instagram username not configured")

    def fetch_stats(self) -> Dict[str, Any]:
        graph = self._graph_client()
        if graph:
            info = graph.user_info()
            return {
                "username": info.get("username", ""),
                "full_name": info.get("name") or info.get("username", ""),
                "followers": info.get("followers_count", 0),
                "following": info.get("follows_count", 0),
                "posts_count": info.get("media_count", 0),
                "views": "0",
            }

        cl, username = self._client()
        user_id = cl.user_id_from_username(username)
        info = cl.user_info(user_id)

        if info.is_private and not self.credentials.get("password"):
            raise ValueError(f"@{username} is a private account — public analysis needs it to be public.")

        total_views = 0
        try:
            medias = cl.user_medias(user_id, amount=6)
            for media in medias:
                if media.media_type == 2:  # Video/Reel
                    total_views += media.view_count or 0
        except Exception as e:
            print(f"⚠️ Failed to fetch recent media metrics: {e}")

        views_display = f"{total_views:,}" if total_views > 0 else "0"

        return {
            "username": username,
            "full_name": info.full_name or username,
            "followers": info.follower_count,
            "following": info.following_count,
            "posts_count": info.media_count,
            "views": views_display,
        }

    def fetch_recent_posts(self, amount: int = 15) -> List[Dict[str, Any]]:
        graph = self._graph_client()
        if graph:
            history_posts = []
            for m in graph.recent_media(amount):
                ts = m.get("timestamp", "")
                try:
                    date_str = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%d %b %Y")
                except ValueError:
                    date_str = ts
                caption = m.get("caption") or ""
                idea_summary = " ".join(caption.split()[:15]) if caption else "Live Instagram post without caption"
                media_type = {
                    "IMAGE": "Static Image",
                    "VIDEO": "Reel",
                    "CAROUSEL_ALBUM": "Carousel",
                }.get(m.get("media_type", ""), "Reel")

                history_posts.append({
                    "date": date_str,
                    "post_type": "Instagram Live Post",
                    "idea_summary": idea_summary,
                    "reel_or_static": media_type,
                })
            return history_posts

        cl, username = self._client()
        user_id = cl.user_id_from_username(username)
        medias = cl.user_medias(user_id, amount=amount)

        history_posts = []
        for media in medias:
            date_str = media.taken_at.strftime("%d %b %Y")
            caption = media.caption_text or ""
            idea_summary = " ".join(caption.split()[:15]) if caption else "Live Instagram post without caption"

            if media.media_type == 1:
                media_type = "Static Image"
            elif media.media_type == 2:
                media_type = "Reel"
            elif media.media_type == 8:
                media_type = "Carousel"
            else:
                media_type = "Reel"

            history_posts.append({
                "date": date_str,
                "post_type": "Instagram Live Post",
                "idea_summary": idea_summary,
                "reel_or_static": media_type,
            })
        return history_posts

    def publish(self, post: Dict[str, Any]) -> Dict[str, Any]:
        graph = self._graph_client()
        if not graph:
            raise NotImplementedError(
                "Automated Instagram publishing needs the official Instagram Graph API — "
                "instagrapi's unofficial login isn't used for posting. Connect this account "
                "with a Page access_token + ig_user_id instead of username/password."
            )

        caption = post.get("caption", "")
        video_url = post.get("video_url")
        image_url = post.get("image_url")

        if video_url:
            return graph.publish_video(video_url, caption, is_reel=post.get("is_reel", True))
        if image_url:
            return graph.publish_photo(image_url, caption)
        raise ValueError("post needs 'image_url' or 'video_url' (publicly reachable) to publish via the Graph API")
