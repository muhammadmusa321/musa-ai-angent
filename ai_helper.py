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
