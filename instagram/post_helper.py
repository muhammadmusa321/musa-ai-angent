import json
import os
import time
import urllib.request
import urllib.parse

INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
GRAPH_BASE = "https://graph.facebook.com/v19.0"

def publish_to_instagram(image_url, caption):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        return False, "Instagram Credentials Missing in GitHub Secrets."

    try:
        pre_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(pre_req, timeout=30) as pre_resp:
            pre_resp.read()
    except Exception as e:
        print(f"Image pre-warm note: {e}")

    time.sleep(3)

    create_url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = urllib.parse.urlencode({
        "image_url": image_url,
        "caption": caption[:2100],
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        req = urllib.request.Request(create_url, data=payload)
        with urllib.request.urlopen(req, timeout=45) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
        container_id = res_data.get("id")
        if not container_id:
            return False, f"Container Error: {res_data}"
    except Exception as e:
        return False, f"Media Container Exception: {str(e)}"

    time.sleep(5)

    publish_url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    pub_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        pub_req = urllib.request.Request(publish_url, data=pub_payload)
        with urllib.request.urlopen(pub_req, timeout=45) as pub_resp:
            pub_res = json.loads(pub_resp.read().decode("utf-8"))
        post_id = pub_res.get("id")
        if post_id:
            return True, post_id
        else:
            return False, f"Publish error: {pub_res}"
    except Exception as e:
        return False, f"Publish Exception: {str(e)}"
