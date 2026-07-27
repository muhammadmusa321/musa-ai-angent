import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


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

    payload = json.dumps({
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }).encode()

    # Try multiple free Gemini models if one is rate-limited
    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]
    generated_text = None
    last_error = ""

    for model_name in models:
        gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={GEMINI_API_KEY}"
        )
        try:
            req = urllib.request.Request(
                gemini_url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            if generated_text:
                break
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            last_error = f"{model_name} (HTTP {e.code}): {error_body[:100]}"
            time.sleep(2)
        except Exception as e:
            last_error = str(e)

    if generated_text:
        print(f"Gemini response:\n{generated_text}")
        send_telegram_message(f"✅ Today's Instagram post:\n\n{generated_text}")
    else:
        send_telegram_message(f"⚠️ Gemini API rate-limited: {last_error}")


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
