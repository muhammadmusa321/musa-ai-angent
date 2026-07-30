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
        # Download HD background image
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            with open("bg.jpg", "wb") as f:
                f.write(resp.read())
    except Exception as e:
        return False, f"Image Download Failed: {str(e)[:100]}"

    if not os.path.exists(audio_file):
        return False, f"Audio file {audio_file} missing."

    try:
        # Clean FFmpeg command
        vf_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", "bg.jpg",
            "-i", audio_file,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", vf_filter,
            "-shortest", output_mp4
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, f"FFmpeg Error: {res.stderr[:150]}"
        print("MP4 Reel Video created successfully!")
        return True, "Success"
    except Exception as e:
        print(f"Error creating MP4 video: {e}")
        return False, f"FFmpeg Exception: {str(e)[:100]}"


def upload_to_catbox(file_path):
    """
    Uploads MP4 video directly to Telegram's native CDN to generate a 100% reliable public URL.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    boundary = "----WebKitFormBoundaryTelegramUpload"
    
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        body = []
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{CHAT_ID}".encode("utf-8"))
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"reel.mp4\"\r\nContent-Type: video/mp4\r\n\r\n".encode("utf-8") + file_bytes)
        body.append(f"--{boundary}--\r\n".encode("utf-8"))
        payload = b"\r\n".join(body)

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        file_id = data["result"]["document"]["file_id"]
        
        # Get public URL from Telegram CDN
        get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        with urllib.request.urlopen(get_file_url, timeout=30) as f_resp:
            f_data = json.loads(f_resp.read().decode("utf-8"))
        
        file_path_on_tg = f_data["result"]["file_path"]
        public_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_on_tg}"
        print(f"Telegram CDN Public Video URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"Error uploading video to Telegram CDN: {e}")
        return None


def publish_reel_to_instagram(video_url, caption):
    if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        return False, "Instagram Credentials Missing."

    # Step 1: Create REELS Container
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

    # Step 2: Poll container status until FINISHED
    status_url = f"{GRAPH_BASE}/{container_id}?fields=status_code&access_token={INSTAGRAM_ACCESS_TOKEN}"
    for _ in range(18):
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

    # Step 3: Publish REELS Container
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
