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
        print("Instagram credentials missing.")
        return False, "Instagram Credentials Missing in GitHub Secrets."

    # Step 1: Pre-warm image URL
    try:
        pre_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(pre_req, timeout=30) as pre_resp:
            pre_resp.read()
    except Exception as e:
        print(f"Image pre-warm note: {e}")

    time.sleep(3)

    # Step 2: Create Media Container
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
        print(f"Container Created: {container_id}")
    except Exception as e:
        print(f"Error creating media container: {e}")
        return False, f"Media Container Error: {str(e)}"

    time.sleep(5)

    # Step 3: Publish Container
    publish_url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
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


def get_recent_media(limit=5):
    """
    Returns a list of recent media items: [{"id": ..., "caption": ...}, ...]
    """
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        print("Instagram credentials missing.")
        return []

    url = (
        f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
        f"?fields=id,caption,timestamp&limit={limit}&access_token={INSTAGRAM_ACCESS_TOKEN}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching recent media: {e}")
        return []


def get_comments_for_media(media_id):
    """
    Returns comments on a media item, each including any existing replies,
    so callers can skip comments we've already replied to.
    """
    url = (
        f"{GRAPH_BASE}/{media_id}/comments"
        f"?fields=id,text,username,replies{{id,text,username}}"
        f"&access_token={INSTAGRAM_ACCESS_TOKEN}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching comments for {media_id}: {e}")
        return []


def has_our_reply(comment, our_username):
    """
    Checks a comment's existing replies for one already posted by our own account,
    so we never reply to the same comment twice.
    """
    replies = comment.get("replies", {}).get("data", [])
    our_username_clean = our_username.lstrip("@").lower()
    for reply in replies:
        if reply.get("username", "").lower() == our_username_clean:
            return True
    return False


def reply_to_comment(comment_id, message_text):
    if not INSTAGRAM_ACCESS_TOKEN:
        return False, "Instagram Access Token Missing."

    url = f"{GRAPH_BASE}/{comment_id}/replies"
    payload = urllib.parse.urlencode({
        "message": message_text[:2200],
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
        reply_id = res_data.get("id")
        if reply_id:
            print(f"Replied to comment {comment_id}: {reply_id}")
            return True, reply_id
        else:
            return False, f"Reply error: {res_data}"
    except Exception as e:
        print(f"Error replying to comment {comment_id}: {e}")
        return False, str(e)
