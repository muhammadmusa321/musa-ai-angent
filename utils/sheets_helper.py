import json
import os
import urllib.request

SHEETS_WEBHOOK_URL = os.environ.get("SHEETS_WEBHOOK_URL", "").strip()

def log_to_sheets(command, model, sections, image_url):
    if not SHEETS_WEBHOOK_URL:
        return False
    payload = json.dumps({
        "type": "post",
        "command": command,
        "model": model,
        "headline": sections.get("headline", ""),
        "caption": sections.get("caption", ""),
        "hashtags": sections.get("hashtags", ""),
        "image_prompt": sections.get("image_prompt", ""),
        "image_url": image_url,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(SHEETS_WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            if resp.status != 200:
                print(f"Sheets webhook returned status {resp.status}: {body[:200]}")
                return False
        return True
    except Exception as e:
        print(f"ERROR logging to Sheets: {e}")
        return False

def log_reply_to_sheets(media_id, comment_id, commenter_username, comment_text, reply_text):
    if not SHEETS_WEBHOOK_URL:
        return False
    payload = json.dumps({
        "type": "reply",
        "media_id": media_id,
        "comment_id": comment_id,
        "commenter_username": commenter_username,
        "comment_text": comment_text,
        "reply_text": reply_text,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(SHEETS_WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            if resp.status != 200:
                print(f"Sheets webhook returned status {resp.status}: {body[:200]}")
                return False
        return True
    except Exception as e:
        print(f"ERROR logging reply to Sheets: {e}")
        return False
