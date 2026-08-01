"""
AI Social Media Manager — Research & Trends Engine
Deep company research + real-time platform trend discovery, both powered by
Gemini's Google Search grounding tool.

Pattern used for both `research_company()` and `fetch_trends()`:
  Step 1 (grounded pass)  — call Gemini WITH the google_search tool, low temperature,
                             to gather real, current, sourced findings as free text.
  Step 2 (structuring pass) — call Gemini again WITHOUT tools but WITH
                             response_mime_type="application/json" to turn the
                             grounded findings into a clean, predictable schema.
  (Gemini does not reliably support forcing structured JSON output *and* tool use
  in the same call, hence the two-step split.)
"""

import json
from datetime import datetime, timezone

from google import genai
from google.genai import types

CACHE_TTL_HOURS = 6


def _client(api_key: str):
    return genai.Client(api_key=api_key)


def _grounding_tool():
    return types.Tool(google_search=types.GoogleSearch())


def _extract_sources(response) -> list:
    """Best-effort extraction of grounding source links from a grounded response.
    Gemini's grounding_metadata shape can vary slightly between SDK versions, so
    this is defensive and simply returns [] if the expected fields aren't there.
    """
    sources = []
    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            meta = getattr(cand, "grounding_metadata", None)
            if not meta:
                continue
            chunks = getattr(meta, "grounding_chunks", None) or []
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if web and getattr(web, "uri", None):
                    sources.append({
                        "title": getattr(web, "title", "") or web.uri,
                        "url": web.uri,
                    })
    except Exception as e:
        print(f"⚠️ Failed to extract grounding sources: {e}")
    # De-dupe while preserving order
    seen = set()
    deduped = []
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            deduped.append(s)
    return deduped[:8]


def _strip_json_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        if raw.rstrip().endswith("```"):
            raw = raw.rstrip()[:-3]
    return raw.strip()


# ──────────────────────────────────────────────────────────
# Deep company research
# ──────────────────────────────────────────────────────────

def research_company(
    name: str,
    website_url: str = "",
    industry_hint: str = "",
    socials_hint: str = "",
    api_key: str = None,
    model_name: str = "gemini-2.5-flash",
) -> dict:
    """Research a business from its name/website/socials and return a dict ready
    to populate a company profile: business_context, target_audience, brand_voice,
    content_pillars, cta_suggestion, industry, summary, confidence, sources.
    """
    if not api_key:
        raise ValueError("Gemini API key is required for research")

    client = _client(api_key)

    identity_lines = [f"Business name: {name}"]
    if website_url:
        identity_lines.append(f"Website: {website_url}")
    if industry_hint:
        identity_lines.append(f"Known industry: {industry_hint}")
    if socials_hint:
        identity_lines.append(f"Known social handles / links: {socials_hint}")
    identity_block = "\n".join(identity_lines)

    step1_prompt = f"""You are a business research analyst. Use web search to research this business as
thoroughly as you can:

{identity_block}

Find and report on:
1. What the business actually does — products/services, how they deliver, what makes them different
2. Target customer — who buys from them, demographics, pain points, where they're based
3. Brand tone/voice — how they communicate (check their website copy, social captions, About page)
4. Pricing/positioning signals — premium vs budget, any offers or guarantees mentioned
5. Notable proof points — testimonials, results, notable clients, reviews, follower counts if visible
6. Anything distinctive that should shape a content strategy for them

Be specific and factual. Cite what you actually found — do not invent details you couldn't verify.
If you can't find much, say so plainly rather than guessing."""

    response1 = client.models.generate_content(
        model=model_name,
        contents=step1_prompt,
        config=types.GenerateContentConfig(
            tools=[_grounding_tool()],
            temperature=0.3,
        ),
    )
    findings = (response1.text or "").strip()
    sources = _extract_sources(response1)

    step2_prompt = f"""Based ONLY on the research findings below, produce a JSON object describing this
business for a social media content strategy. If the findings are thin, make reasonable,
clearly-generic fallbacks rather than fabricating specifics.

RESEARCH FINDINGS:
{findings if findings else "(No usable findings were returned — produce sensible generic defaults and set confidence to 'low'.)"}

Return ONLY a JSON object with EXACTLY these keys:
- "industry": short industry label (string)
- "business_context": 2-4 sentences describing what the business does and what makes it different (string)
- "target_audience": who they should be speaking to — demographics, pain points, goals (string)
- "brand_voice": 1-2 sentences describing the tone/voice content should use (string)
- "content_pillars": an array of 8-10 tailored content pillar strings for this specific business (not generic placeholders)
- "cta_suggestion": one concrete call-to-action line suited to this business (string)
- "summary": a punchy 1-2 sentence summary of the research, suitable to show a user as "here's what we found" (string)
- "confidence": one of "high", "medium", "low" based on how much real information was found

Return ONLY valid JSON. No markdown, no explanations, no extra text."""

    response2 = client.models.generate_content(
        model=model_name,
        contents=step2_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
        ),
    )
    parsed = json.loads(_strip_json_fences(response2.text))

    parsed["sources"] = sources
    parsed["researched_at"] = datetime.now(timezone.utc).isoformat()
    return parsed


# ──────────────────────────────────────────────────────────
# Real-time trend discovery
# ──────────────────────────────────────────────────────────

def fetch_trends(
    company: dict,
    platform: str,
    platform_label: str,
    api_key: str = None,
    model_name: str = "gemini-2.5-flash",
) -> dict:
    """Find what's actually trending RIGHT NOW on a given platform for a brand's niche
    — formats, sounds/audio, hooks, topics — not generic evergreen advice.
    Returns {"trends": [...], "fetched_at": iso, "sources": [...]}.
    """
    if not api_key:
        raise ValueError("Gemini API key is required for trend fetching")

    client = _client(api_key)
    today = datetime.now(timezone.utc).strftime("%d %B %Y")

    industry = company.get("industry") or "this industry"
    audience = company.get("target_audience") or "the target audience"
    niche_block = f"Industry / niche: {industry}\nTarget audience: {audience}"

    step1_prompt = f"""You are a {platform_label} trend researcher. Today's date is {today}.

Use web search to find what is ACTUALLY trending on {platform_label} RIGHT NOW (this week / this month) —
specifically for content relevant to this niche:

{niche_block}

Look for:
1. Trending formats/edit styles currently getting reach on {platform_label}
2. Trending sounds, audio trends, or meme formats currently in use (if applicable to this platform)
3. Trending hooks, opening lines, or caption styles performing well right now
4. Trending topics or conversations relevant to this niche right now
5. Any {platform_label}-specific algorithm shifts or format pushes happening currently

Be specific with dates/timeframes where you can, and be honest that trends move fast — flag anything
you're unsure is still current. Do not describe generic evergreen best practices as if they were
"trending" — only report things genuinely tied to the current moment."""

    response1 = client.models.generate_content(
        model=model_name,
        contents=step1_prompt,
        config=types.GenerateContentConfig(
            tools=[_grounding_tool()],
            temperature=0.4,
        ),
    )
    findings = (response1.text or "").strip()
    sources = _extract_sources(response1)

    step2_prompt = f"""Based ONLY on the research findings below, produce a JSON array of the most
useful current {platform_label} trends for this brand to consider. If findings are thin, return
fewer, honest items rather than padding with generic advice.

RESEARCH FINDINGS:
{findings if findings else "(No usable findings were returned.)"}

Return ONLY a JSON array (3-7 items). Each item must be an object with EXACTLY these keys:
- "title": short trend name (string)
- "format": the content format this applies to, e.g. "Reel", "Carousel", "Text Post" (string)
- "description": 1-2 sentences describing the trend itself (string)
- "why_it_works": 1 sentence on why it's performing right now (string)
- "brand_angle": 1 concrete sentence on how THIS brand specifically could use it, given its niche/audience (string)

Return ONLY valid JSON. No markdown, no explanations, no extra text."""

    response2 = client.models.generate_content(
        model=model_name,
        contents=step2_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.5,
        ),
    )
    trends = json.loads(_strip_json_fences(response2.text))
    if isinstance(trends, dict):
        trends = [trends]

    return {
        "trends": trends,
        "sources": sources,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def is_cache_fresh(fetched_at_iso: str, ttl_hours: float = CACHE_TTL_HOURS) -> bool:
    if not fetched_at_iso:
        return False
    try:
        fetched_at = datetime.fromisoformat(fetched_at_iso.replace("Z", "+00:00"))
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
        return age_hours < ttl_hours
    except Exception:
        return False
