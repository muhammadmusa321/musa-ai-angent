import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Tried in order. Each has its own separate free-tier quota (Google tracks
# rate limits per model, not just per key), so falling back to the next
# model on a 429 is a genuine workaround, not just a repeat of the same call.
MODEL_FALLBACK_ORDER = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-flash-lite-latest",
]

MAX_RETRIES_PER_MODEL = 3
BASE_BACKOFF_SECONDS = 5


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = text[:4000]  # Telegram's message length limit
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
    """
    Calls one Gemini model with retry + exponential backoff on 429.
    Returns the generated text on success.
    Raises RuntimeError if this model is exhausted after retries,
    so the caller can move on to the next model in the fallback list.
    """
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
                # Non-429 HTTP error (bad request, invalid model name, etc.)
                # No point retrying this model — fail fast to the next one.
                raise RuntimeError(f"{model} failed with HTTP {e.code}: {error_body}")

        except Exception as e:
            print(f"[{model}] Unexpected error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES_PER_MODEL:
                time.sleep(BASE_BACKOFF_SECONDS)
                continue
            raise RuntimeError(f"{model} failed after {MAX_RETRIES_PER_MODEL} attempts: {e}")

    raise RuntimeError(f"{model} failed for an unknown reason")


def generate_instagram_post():
    prompt = (
        "Generate content for an Instagram post from an AI-persona lifestyle "
        "account. Respond in exactly this format:\n\n"
        "HEADLINE: <a short catchy headline>\n\n"
        "CAPTION: <an engaging Instagram caption, 2-4 sentences, with relevant emojis>\n\n"
        "HASHTAGS: <5 to 10 relevant hashtags, space separated>\n\n"
        "IMAGE_PROMPT: <a detailed prompt suitable for an AI image generator "
        "to create the accompanying visual>"
    )

    last_error = None

    for model in MODEL_FALLBACK_ORDER:
        try:
            print(f"Trying model: {model}")
            generated_text = call_gemini_model(model, prompt)
            print(f"Success with {model}:\n{generated_text}")
            send_telegram_message(f"✅ Today's Instagram post (via {model}):\n\n{generated_text}")
            return
        except RuntimeError as e:
            print(f"Model {model} failed: {e}")
            last_error = e
            continue

    # If we reach here, every model in the fallback list failed
    send_telegram_message(
        "⚠️ All AI models are currently rate-limited or unavailable on the "
        "free tier. This usually clears within a minute (per-minute limit) "
        "or resets tomorrow (daily limit). Check the Actions log for the "
        f"exact error. Last error: {last_error}"
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
