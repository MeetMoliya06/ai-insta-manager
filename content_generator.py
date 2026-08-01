"""One-click AI image generation for scheduled posts, driven by each post's
`image_prompt` (already produced by `social_media_agent.generate_posts`).
Uses Gemini's native image-generation model — same `google-genai` client
already used for research/trends.
"""

import os
import uuid

from google import genai

IMAGE_MODEL = "gemini-2.5-flash-image"
GENERATED_DIR = os.path.join("static", "generated_images")


def generate_post_image(prompt: str, api_key: str, company_id: str) -> str:
    """Generate an image from a post's image_prompt, save it under static/,
    and return the web-relative URL the frontend can render directly."""
    if not prompt or not prompt.strip():
        raise ValueError("This post has no image_prompt to generate from")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=IMAGE_MODEL, contents=prompt)

    image_bytes = None
    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and inline_data.data:
                image_bytes = inline_data.data
                break
        if image_bytes:
            break

    if not image_bytes:
        raise RuntimeError("Gemini did not return an image for this prompt")

    company_dir = os.path.join(GENERATED_DIR, company_id)
    os.makedirs(company_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    with open(os.path.join(company_dir, filename), "wb") as f:
        f.write(image_bytes)

    return f"/generated_images/{company_id}/{filename}"
