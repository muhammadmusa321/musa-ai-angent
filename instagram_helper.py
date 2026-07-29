import json
import os
import time
import urllib.request
import urllib.parse

INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()

def publish_to_instagram(image_url, caption):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        print("Instagram credentials missing.")
        return False, "Instagram Credentials Missing in Secrets."

    # Step 1: Create Media Container
    create_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
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
        print(f"Container Created: {container_id}")
    except Exception as e:
        print(f"Error creating media container: {e}")
        return False, f"Media Container Error: {str(e)}"

    # Wait 5 seconds for Meta servers to process the image URL
    time.sleep(5)

    # Step 2: Publish Media Container
    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        pub_req = urllib.request.Request(publish_url, data=publish_payload)
        with urllib.request.urlopen(pub_req, timeout=45) as pub_resp:
            pub_res = json.loads(pub_resp.read().decode("utf-8"))
        post_id = pub_res.get("id")
        if post_id:
            print(f"Published to Instagram successfully! Post ID: {post_id}")
            return True, post_id
        else:
            return False, f"Publish error: {pub_res}"
    except Exception as e:
        print(f"Error publishing to Instagram: {e}")
        return False, f"Publish Error: {str(e)}"
