import asyncio
import json
import os
import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error

INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GRAPH_BASE = "https://graph.facebook.com/v19.0"

LITTERBOX_API_URL = "https://litterbox.catbox.moe/resources/internals/api.php"


def create_voiceover(text, output_file="voice.mp3"):
    try:
        import edge_tts

        async def generate_voiceover_async():
            voice = "en-US-ChristopherNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

        asyncio.run(generate_voiceover_async())
        return True, "Success"
    except Exception as e:
        print(f"Error generating AI voiceover: {e}")
        return False, str(e)


def build_reel_video(image_url, audio_file="voice.mp3", output_mp4="reel.mp4"):
    try:
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            with open("bg.jpg", "wb") as f:
                f.write(resp.read())
    except Exception as e:
        return False, f"Image Download Failed: {str(e)[:100]}"

    if not os.path.exists(audio_file):
        return False, f"Audio file {audio_file} missing."

    try:
        vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", "bg.jpg",
            "-i", audio_file,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-vf", vf_filter,
            "-t", "8",
            output_mp4
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"FFmpeg Error: {res.stderr[:150]}"
        print("MP4 Reel Video created successfully for Meta Reels!")
        return True, "Success"
    except Exception as e:
        print(f"Error creating MP4 video: {e}")
        return False, f"FFmpeg Exception: {str(e)[:100]}"


def upload_to_catbox(file_path):
    """
    Uploads the rendered MP4 to litterbox.catbox.moe, which returns a
    direct raw binary file URL (no redirects, no landing page) --
    required for Meta's facebookexternalhit crawler to fetch and
    process the video successfully.

    Files expire after 1 hour on litterbox -- more than enough time
    for Meta to fetch and process the container, and we don't need
    permanent hosting since the file's only job is to get published.
    """
    try:
        boundary = "----HermesAgentReelUpload"
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        def field(name, value):
            return (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{value}\r\n"
            ).encode("utf-8")

        body = b""
        body += field("reqtype", "fileupload")
        body += field("time", "1h")
        body += (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"fileToUpload\"; filename=\"reel.mp4\"\r\n"
            f"Content-Type: video/mp4\r\n\r\n"
        ).encode("utf-8") + file_bytes + b"\r\n"
        body += f"--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            LITTERBOX_API_URL,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Mozilla/5.0"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            direct_url = resp.read().decode("utf-8").strip()

        if direct_url.startswith("https://litterbox.catbox.moe/"):
            print(f"Uploaded Reel MP4 to Litterbox: {direct_url}")
            return direct_url
        else:
            print(f"Unexpected Litterbox response: {direct_url}")
            return None

    except Exception as e:
        print(f"Error uploading to Litterbox: {e}")
        return None


def publish_reel_to_instagram(video_url, caption):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        return False, "Instagram Credentials Missing."

    create_url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = urllib.parse.urlencode({
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption[:2100],
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        req = urllib.request.Request(create_url, data=payload)
        with urllib.request.urlopen(req, timeout=45) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
        container_id = res_data.get("id")
        if not container_id:
            return False, f"Reel Container Error: {res_data}"
        print(f"Reel Container Created: {container_id}")
    except Exception as e:
        return False, f"Reel Container Exception: {str(e)}"

    status_url = f"{GRAPH_BASE}/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}"
    for _ in range(12):
        time.sleep(5)
        try:
            s_req = urllib.request.Request(status_url)
            with urllib.request.urlopen(s_req, timeout=30) as s_resp:
                s_data = json.loads(s_resp.read().decode("utf-8"))
            code = s_data.get("status_code")
            print(f"Reel processing status: {code}")
            if code == "FINISHED":
                break
            elif code == "ERROR":
                return False, "Meta failed to process video reel."
        except Exception:
            pass

    publish_url = f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    pub_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }).encode("utf-8")

    try:
        pub_req = urllib.request.Request(publish_url, data=pub_payload)
        with urllib.request.urlopen(pub_req, timeout=45) as pub_resp:
            pub_res = json.loads(pub_resp.read().decode("utf-8"))
        reel_id = pub_res.get("id")
        if reel_id:
            print(f"Published Reel successfully! Reel ID: {reel_id}")
            return True, reel_id
        else:
            return False, f"Publish Reel Error: {pub_res}"
    except Exception as e:
        return False, f"Publish Reel Exception: {str(e)}"
