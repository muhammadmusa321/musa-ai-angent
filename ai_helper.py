import json
import os
import random
import time
import urllib.request
import urllib.parse
import urllib.error

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
MODEL_FALLBACK_ORDER = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-lite-latest"]
MAX_RETRIES_PER_MODEL = 3
BASE_BACKOFF_SECONDS = 5


def load_persona():
    try:
        with open("persona.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "system_prompt": "Generate an engaging Instagram post about modern AI tools.",
            "topics": ["AI Tools & Automation"],
            "image_style_prefix": "3D dark-mode tech graphic: "
        }


def call_gemini_model(model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()

    for attempt in range(1, MAX_RETRIES_PER_MODEL + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES_PER_MODEL:
                time.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                continue
            raise RuntimeError(f"{model} failed HTTP {e.code}")
        except Exception as e:
            if attempt < MAX_RETRIES_PER_MODEL:
                time.sleep(BASE_BACKOFF_SECONDS)
                continue
            raise RuntimeError(f"{model} failed: {e}")
    raise RuntimeError(f"{model} failed")


def parse_post_sections(generated_text):
    sections = {"headline": "", "caption": "", "hashtags": "", "image_prompt": ""}
    current_key = None
    label_map = {"HEADLINE:": "headline", "CAPTION:": "caption", "HASHTAGS:": "hashtags", "IMAGE_PROMPT:": "image_prompt"}

    for line in generated_text.splitlines():
        stripped = line.strip()
        matched = False
        for label, key in label_map.items():
            if stripped.startswith(label):
                current_key = key
                sections[key] = stripped[len(label):].strip()
                matched = True
                break
        if not matched and current_key and stripped:
            sections[current_key] += " " + stripped
    return sections


def build_image_url(image_prompt, style_prefix=""):
    combined_prompt = f"{style_prefix} {image_prompt}"[:250]
    encoded_prompt = urllib.parse.quote(combined_prompt)
    random_seed = random.randint(1000, 999999)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed={random_seed}"


def generate_comment_reply(persona, comment_text, commenter_username):
    """
    Generates a short, friendly, on-persona reply to a single Instagram comment.
    Tries each model in MODEL_FALLBACK_ORDER until one succeeds.
    """
    account_name = persona.get("account_name", "the creator")
    niche = persona.get("niche", "AI and automation")

    prompt = (
        f"You are replying to a comment on an Instagram post, as {account_name}, "
        f"a creator in the '{niche}' niche. "
        f"A follower named '{commenter_username}' commented: \"{comment_text}\"\n\n"
        "Write a short, warm, genuine reply (1-2 sentences max, 1 emoji max). "
        "Sound like a real person, not a bot. Do not repeat the commenter's words back robotically. "
        "Do not include quotation marks, labels, or any prefix — respond with ONLY the reply text itself."
    )

    last_error = None
    for model in MODEL_FALLBACK_ORDER:
        try:
            reply_text = call_gemini_model(model, prompt)
            return reply_text.strip().strip('"')
        except RuntimeError as e:
            last_error = e
            continue

    raise RuntimeError(f"All models failed to generate a reply: {last_error}")
