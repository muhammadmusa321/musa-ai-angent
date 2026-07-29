import json
import os
import urllib.request
import urllib.parse

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = text[:4000]
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except Exception as e:
        print(f"ERROR sending to Telegram: {e}")

def send_telegram_photo(photo_url, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "photo": photo_url, "caption": caption[:1024]}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True
    except Exception:
        pass

    try:
        req = urllib.request.Request(photo_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=35) as resp:
            img_bytes = resp.read()

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = []
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{CHAT_ID}".encode("utf-8"))
        if caption:
            body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption[:1024]}".encode("utf-8"))
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"image.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode("utf-8") + img_bytes)
        body.append(f"--{boundary}--\r\n".encode("utf-8"))
        
        payload = b"\r\n".join(body)
        tg_req = urllib.request.Request(url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(tg_req, timeout=30) as resp:
            resp.read()
        return True
    except Exception as e:
        print(f"Bytes photo send failed: {e}")
        return False

def get_latest_message():
    trigger_event = os.environ.get("TRIGGER_EVENT", "").strip()
    
    # If triggered automatically by daily Cron schedule, default to auto-post command
    if trigger_event == "schedule":
        print("Daily Scheduled Cron Triggered -> Running auto-post!")
        return "Create today's Instagram post"

    try:
        with open("updates.json", "r") as f:
            updates = json.load(f)
        return updates["result"][-1]["message"]["text"]
    except Exception as e:
        print(f"Updates JSON empty or unreadable ({e}) -> Defaulting to auto-post command.")
        return "Create today's Instagram post"
