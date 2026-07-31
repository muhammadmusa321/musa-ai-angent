import json
import os
import urllib.request

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

def _build_multipart_body(fields, file_field_name, filename, file_bytes, file_content_type):
    boundary = "----HermesAgentBoundary7f3a9c"
    parts = []
    for name, value in fields.items():
        parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode("utf-8"))
    parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field_name}\"; filename=\"{filename}\"\r\nContent-Type: {file_content_type}\r\n\r\n").encode("utf-8"))
    parts.append(file_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), boundary

def upload_video_to_telegram_cdn(file_path):
    if not BOT_TOKEN or not CHAT_ID:
        return None
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        body, boundary = _build_multipart_body({"chat_id": CHAT_ID}, "document", "reel.mp4", file_bytes, "video/mp4")

        req = urllib.request.Request(send_url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        res_dict = data.get("result", {})
        file_id = res_dict.get("document", {}).get("file_id") or res_dict.get("video", {}).get("file_id")
        if not file_id:
            return None

        get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        req_get = urllib.request.Request(get_file_url)
        with urllib.request.urlopen(req_get, timeout=30) as resp_get:
            get_res = json.loads(resp_get.read().decode("utf-8"))

        telegram_file_path = get_res.get("result", {}).get("file_path")
        if not telegram_file_path:
            return None

        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{telegram_file_path}"
    except Exception as e:
        print(f"Error uploading video to Telegram CDN: {e}")
        return None
