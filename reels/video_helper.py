import os
import subprocess
import urllib.request

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
        print("MP4 Reel Video created successfully!")
        return True, "Success"
    except Exception as e:
        print(f"Error creating MP4 video: {e}")
        return False, f"FFmpeg Exception: {str(e)[:100]}"
