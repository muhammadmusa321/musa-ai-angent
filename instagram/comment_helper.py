import json
import os
import urllib.request
import urllib.parse

INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
GRAPH_BASE = "https://graph.facebook.com/v19.0"

def get_recent_media(limit=5):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        return []

    url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media?fields=id,caption,timestamp&limit={limit}&access_token={INSTAGRAM_ACCESS_TOKEN}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching recent media: {e}")
        return []

def get_comments_for_media(media_id):
    url = f"{GRAPH_BASE}/{media_id}/comments?fields=id,text,username,replies{{id,text,username}}&access_token={INSTAGRAM_ACCESS_TOKEN}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching comments for {media_id}: {e}")
        return []

def has_our_reply(comment, our_username):
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
            return True, reply_id
        else:
            return False, f"Reply error: {res_data}"
    except Exception as e:
        return False, str(e)
