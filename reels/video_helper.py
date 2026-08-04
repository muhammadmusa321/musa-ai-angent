import os
import subprocess
from ai.poster_generator import generate_vertical_poster


def _get_audio_duration(path, default=8.0, max_cap=60.0):
    """Reads real audio length via ffprobe (bundled free with ffmpeg) so the
    video is never cut short or padded with silence like the old hardcoded 8s.
    Capped at max_cap as a safety net against runaway render times."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15
        )
        duration = float(result.stdout.strip())
        if duration <= 0:
            return default
        return min(duration, max_cap)
    except Exception as e:
        print(f"Could not read audio duration, using default {default}s: {e}")
        return default


def build_reel_video(image_url, audio_file="voice.mp3", output_mp4="reel.mp4", headline="AI REEL UPDATE", script_text=None):
    try:
        # No bullet text on the reel background itself -- the burned-in
        # captions below now carry the spoken message, so the poster stays
        # clean (just the AI background + headline + handle).
        generate_vertical_poster(
            headline,
            bullets=[],
            output_path="bg.jpg",
            image_prompt=f"cinematic dark-mode tech background, {headline}"
        )
    except Exception as e:
        print(f"AI Background Generation Note: {e}")

    if not os.path.exists("bg.jpg"):
        return False, "Background image missing."

    if not os.path.exists(audio_file):
        return False, f"Audio file {audio_file} missing."

    duration = _get_audio_duration(audio_file, default=8.0)
    srt_file = "voice.srt"
    has_captions = os.path.exists(srt_file) and os.path.getsize(srt_file) > 0
    fade_out_start = max(duration - 1.2, 0)

    # fps kept moderate (24) -- zoompan recomputes the full frame each step,
    # so a lower fps noticeably cuts render time on constrained CI runners
    # while still looking smooth for a short vertical Reel.
    fps = 24

    # --- Video chain: Ken Burns slow zoom (100% free, built into ffmpeg) ---
    video_chain = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0009,1.3)':d=1:s=1080x1920:fps={fps}"
    )
    if has_captions:
        video_chain += (
            f",subtitles={srt_file}:force_style='FontName=DejaVu Sans,FontSize=15,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,"
            "Outline=2,Shadow=0,Alignment=2,MarginV=190'"
        )
    video_chain += "[v]"

    # --- Audio chain: voice + a soft synthesized ambient pad (free, no
    # downloaded/licensed music -- generated on the fly with ffmpeg's
    # built-in sine-wave source, so there's zero copyright or cost risk) ---
    audio_chain = (
        "[2:a][3:a][4:a]amix=inputs=3:duration=first,"
        "lowpass=f=900,volume=0.05,"
        "afade=t=in:st=0:d=1.5,"
        f"afade=t=out:st={fade_out_start}:d=1.2[pad];"
        "[1:a][pad]amix=inputs=2:duration=first:normalize=0[aout]"
    )

    filter_complex = f"{video_chain};{audio_chain}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", "bg.jpg",
        "-i", audio_file,
        "-f", "lavfi", "-i", f"sine=frequency=130.81:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=164.81:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=196.00:duration={duration}",
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-t", str(duration),
        "-shortest",
        output_mp4
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=480)
        if res.returncode != 0:
            print(f"Full ffmpeg stderr: {res.stderr}")
            return False, f"FFmpeg Error: {res.stderr[-300:]}"
        print("MP4 Reel Video created successfully (Ken Burns zoom + captions + ambient pad)!")
        return True, "Success"
    except subprocess.TimeoutExpired:
        print("ffmpeg render exceeded the 480s time limit.")
        return False, "Video rendering took too long (over 8 minutes) and was stopped. This can happen on a slow CI runner -- try again, or shorten the Reel script."
    except Exception as e:
        print(f"Error creating MP4 video: {e}")
        return False, f"FFmpeg Exception: {str(e)[:300]}"
