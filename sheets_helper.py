import json
import os
import urllib.request

SHEETS_WEBHOOK_URL = os.environ.get("SHEETS_WEBHOOK_URL", "")

def log_to_sheets(command, model, sections, image_url):
    if not SHEETS_WEBHOOK_URL:
        return False
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
        req = urllib.request.Request(SHEETS_WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True
    except Exception as e:
        print(f"ERROR logging to Sheets: {e}")
        return False
