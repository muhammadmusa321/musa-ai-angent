import json
import os
import random
import urllib.request
import urllib.parse
from ai.poster_generator import generate_square_poster

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def upload_photo_to_telegram_cdn(file_path):
    if not BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = "----WebKitFormBoundaryTelegramUploadPhoto"
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        body = []
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{CHAT_ID}".encode("utf-8"))
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"infographic.png\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8") + file_bytes)
        body.append(f"--{boundary}--\r\n".encode("utf-8"))
        payload = b"\r\n".join(body)

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        photos = data.get("result", {}).get("photo", [])
        if not photos:
            return None
        
        file_id = photos[-1].get("file_id")
        
        get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        with urllib.request.urlopen(get_file_url, timeout=30) as f_resp:
            f_data = json.loads(f_resp.read().decode("utf-8"))
        
        file_path_on_tg = f_data["result"]["file_path"]
        public_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_on_tg}"
        print(f"Telegram CDN Public Photo URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"Error uploading photo to Telegram CDN: {e}")
        return None


def build_image_url(image_prompt, style_prefix="", headline="", caption_text=""):
    try:
        bullets = []
        if caption_text:
            for l in caption_text.splitlines():
                l_strip = l.strip()
                if l_strip.startswith("•") or l_strip.startswith("-") or l_strip.startswith("*"):
                    bullets.append(l_strip)
        
        if not bullets:
            bullets = [
                "• 10x Content Output with AI Workers",
                "• No Coding Required & Fast Setup",
                "• Automate Repetitive Daily Tasks"
            ]

        poster_title = headline if headline else "AI AUTOMATION UPDATE"
        local_path = generate_square_poster(poster_title, bullets, output_path="infographic.png")
        
        # Convert local image to public URL for Meta API
        public_url = upload_photo_to_telegram_cdn(local_path)
        if public_url:
            return public_url
        return local_path
    except Exception as e:
        print(f"Pillow Poster Generation Fallback: {e}")
        encoded_prompt = urllib.parse.quote(image_prompt[:200])
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"
