import json
import os
import urllib.request
import urllib.parse

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials missing.")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text = text[:4000]
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        if not result.get("ok"):
            print(f"Telegram API error: {result}")
            return False
        return True
    except Exception as e:
        print(f"ERROR sending to Telegram: {e}")
        return False

def send_telegram_photo(photo_url, caption=""):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "photo": photo_url, "caption": caption[:1024]}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        if result.get("ok"):
            return True
        print(f"Telegram sendPhoto by URL failed: {result}")
    except Exception as e:
        print(f"Telegram sendPhoto by URL exception: {e}")

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
            result = json.loads(resp.read().decode())
        if not result.get("ok"):
            print(f"Telegram sendPhoto by bytes failed: {result}")
            return False
        return True
    except Exception as e:
        print(f"Bytes photo send failed: {e}")
        return False

def get_latest_message():
    try:
        with open("updates.json", "r") as f:
            updates = json.load(f)
        return updates["result"][-1]["message"]["text"]
    except Exception as e:
        send_telegram_message(f"⚠️ Error reading Telegram message: {e}")
        raise SystemExit(1)
