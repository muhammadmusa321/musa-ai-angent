import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SHEETS_WEBHOOK_URL = os.environ["SHEETS_WEBHOOK_URL"]

MODEL_FALLBACK_ORDER = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-flash-lite-latest",
]

MAX_RETRIES_PER_MODEL = 3
BASE_BACKOFF_SECONDS = 5


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = text[:4000]
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text
    }).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        print(f"Sent to Telegram: {text[:80]}...")
    except Exception as e:
        print(f"ERROR sending to Telegram: {e}")


def send_telegram_photo(photo_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption[:1024]
    }).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
        print(f"Sent photo to Telegram: {photo_url}")
        return True
    except Exception as e:
        print(f"ERROR sending photo to Telegram: {e}")
        return False


def get_latest_message():
    try:
        with open("updates.json", "r") as f:
            updates = json.load(f)
        message = updates["result"][-1]["message"]["text"]
        print(f"Extracted message: {message}")
        return message
    except Exception as e:
        print(f"ERROR extracting message: {e}")
        send_telegram_message(f"⚠️ Error reading Telegram message: {e}")
        raise SystemExit(1)


def call_gemini_model(model, prompt):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = json.dumps({
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }).encode()

    for attempt in range(1, MAX_RETRIES_PER_MODEL + 1):
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            return result["candidates"][0]["content"]["parts"][0]["text"]

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"[{model}] HTTP {e.code} on attempt {attempt}: {error_body}")

            if e.code == 429:
                if attempt < MAX_RETRIES_PER_MODEL:
                    wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    print(f"[{model}] Rate limited. Waiting {wait}s before retry...")
                    time.sleep(wait)
                    continue
                else:
                    raise RuntimeError(f"{model} exhausted after {MAX_RETRIES_PER_MODEL} attempts (429)")
            else:
                raise RuntimeError(f"{model} failed with HTTP {e.code}: {error_body}")

        except Exception as e:
            print(f"[{model}] Unexpected error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES_PER_MODEL:
                time.sleep(BASE_BACKOFF_SECONDS)
                continue
            raise RuntimeError(f"{model} failed after {MAX_RETRIES_PER_MODEL} attempts: {e}")

    raise RuntimeError(f"{model} failed for an unknown reason")


def parse_post_sections(generated_text):
    sections = {"headline": "", "caption": "", "hashtags": "", "image_prompt": ""}
    current_key = None
    label_map = {
        "HEADLINE:": "headline",
        "CAPTION:": "caption",
        "HASHTAGS:": "hashtags",
        "IMAGE_PROMPT:": "image_prompt",
    }

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


def build_image_url(image_prompt):
    encoded_prompt = urllib.parse.quote(image_prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        "?width=1024&height=1024&nologo=true"
    )


def log_to_sheets(command, model, sections, image_url):
    payload = json.dumps({
        "command": command,
        "model": model,
        "headline": sections.get("headline", ""),
        "caption": sections.get("caption", ""),
        "hashtags": sections.get("hashtags", ""),
        "image_prompt": sections.get("image_prompt", ""),
        "image_url": image_url,
    }).encode()

    try:
        req = urllib.request.Request(
            SHEETS_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        print("Logged to Google Sheets successfully.")
        return True
    except Exception as e:
        print(f"ERROR logging to Sheets: {e}")
        return False


def generate_instagram_post():
    # Tailored specifically for @muhammad_musa125001 (AI Creator & Automation)
    prompt = (
        "You are the official AI Content Creator for 'Muhammad Musa' (@muhammad_musa125001), "
        "a top AI Creator and Automation Specialist. Generate a viral, professional Instagram post "
        "about AI tools, content automation, AI agents, or futuristic tech updates.\n\n"
        "Respond in EXACTLY this format:\n\n"
        "HEADLINE: <a short, punchy 3-6 word viral tech headline>\n\n"
        "CAPTION: <an engaging, high-value caption explaining the AI tool or concept with 3 key bullet points, relevant emojis, and a strong Call-To-Action asking followers to SAVE or SHARE this post>\n\n"
        "HASHTAGS: #AICreator #AITools #Automation #AIAgents #NoCode #TechUpdates #ArtificialIntelligence #ContentAutomation #BuildInPublic #PakistanTech\n\n"
        "IMAGE_PROMPT: <a detailed prompt for a 3D dark-mode minimalist tech infographic poster, featuring glowing neon blue and purple UI elements, sleek futuristic digital icons, 8k resolution, cinematic lighting, modern cyber graphic design>"
    )

    last_error = None

    for model in MODEL_FALLBACK_ORDER:
        try:
            print(f"Trying model: {model}")
            generated_text = call_gemini_model(model, prompt)
            print(f"Success with {model}:\n{generated_text}")

            sections = parse_post_sections(generated_text)

            image_url = ""
            photo_sent = False
            if sections.get("image_prompt"):
                image_url = build_image_url(sections["image_prompt"])
                print(f"Generated image URL: {image_url}")
                photo_caption = sections.get("headline", "")[:1024]
                photo_sent = send_telegram_photo(image_url, caption=photo_caption)

            logged = log_to_sheets("Create today's Instagram post", model, sections, image_url)

            log_note = "📝 Logged to memory." if logged else "⚠️ Post generated, but logging to Sheets failed."
            image_note = "" if photo_sent else "\n⚠️ Image could not be sent to Telegram."

            send_telegram_message(
                f"✅ Today's Instagram post (via {model}):\n\n{generated_text}\n\n{log_note}{image_note}"
            )
            return
        except RuntimeError as e:
            print(f"Model {model} failed: {e}")
            last_error = e
            continue

    send_telegram_message(
        f"⚠️ All AI models failed. Last error: {last_error}"
    )


def main():
    message = get_latest_message()

    if message.strip() == "Create today's Instagram post":
        send_telegram_message("🤖 Command Recognized! Generating Instagram Post with AI Brain...")
        generate_instagram_post()
    else:
        print(f"No matching command found for: {message}")
        send_telegram_message(f"❓ Unrecognized Command: {message}")


if __name__ == "__main__":
    main()
