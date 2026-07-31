import os
import random
import time
from telegram_helper import send_telegram_message, send_telegram_photo, get_latest_message
from ai.persona_helper import load_persona
from ai.gemini_helper import call_gemini_model, MODEL_FALLBACK_ORDER
from ai.parser_helper import parse_post_sections
from ai.image_prompt_helper import build_image_url
from ai.comment_reply_helper import generate_comment_reply
from sheets_helper import log_to_sheets, log_reply_to_sheets
from instagram_helper import (
    publish_to_instagram,
    get_recent_media,
    get_comments_for_media,
    has_our_reply,
    reply_to_comment,
)
from reels.voice_helper import create_voiceover
from reels.video_helper import build_reel_video
from reels.uploader_helper import upload_video_to_telegram_cdn
from reels.reel_helper import publish_reel_to_instagram

OUR_USERNAME = "muhammad_musa125001"


def generate_instagram_reel():
    persona = load_persona()
    topics_list = persona.get("topics", ["AI Tools & Automation"])
    chosen_topic = random.choice(topics_list)

    script_prompt = (
        f"Write a 15-second viral Instagram Reel script voiceover for '{chosen_topic}'. "
        "Keep it punchy, high-energy, educational, and under 35 words total. "
        "Do not include brackets, scene descriptions, or labels. Return ONLY the spoken voiceover text."
    )

    voiceover_text = None
    for model in MODEL_FALLBACK_ORDER:
        try:
            print(f"Generating Reel script with model: {model}")
            voiceover_text = call_gemini_model(model, script_prompt)
            if voiceover_text:
                break
        except Exception as e:
            print(f"Model {model} failed for script: {e}")
            continue

    if not voiceover_text:
        send_telegram_message("⚠️ All AI models rate-limited while generating Reel script. Please try again in 1 minute.")
        return

    voice_created, v_err = create_voiceover(voiceover_text, "voice.mp3")
    if not voice_created:
        send_telegram_message(f"⚠️ AI Voiceover Error: {v_err}")
        return

    style_prefix = persona.get("image_style_prefix", "")
    image_url = build_image_url(f"Vertical 1080x1920 poster for {chosen_topic}", style_prefix)
    
    reel_created, r_err = build_reel_video(image_url, "voice.mp3", "reel.mp4")
    if not reel_created:
        send_telegram_message(f"⚠️ Video Build Details: {r_err}")
        return

    public_video_url = upload_video_to_telegram_cdn("reel.mp4")
    if not public_video_url:
        send_telegram_message("⚠️ Failed to upload Reel MP4 to Telegram CDN.")
        return

    caption = f"🎬 {chosen_topic}\n\n{voiceover_text}\n\n#AICreator #AITools #Reels #Automation #PakistanTech"
    published, reel_result = publish_reel_to_instagram(public_video_url, caption)

    if published:
        send_telegram_message(f"🎥 **AI REEL PUBLISHED TO INSTAGRAM!**\n\n**Topic:** {chosen_topic}\n**Script:** \"{voiceover_text}\"\n**Reel ID:** {reel_result}")
    else:
        send_telegram_message(f"⚠️ Reel Publishing Status: {reel_result}")


def generate_instagram_post():
    persona = load_persona()
    topics_list = persona.get("topics", ["AI Tools & Automation"])
    chosen_topic = random.choice(topics_list)

    prompt = (
        f"{persona.get('system_prompt', '')}\n\n"
        f"TODAY'S SPECIFIC FOCUS TOPIC: {chosen_topic}\n\n"
        "Respond in EXACTLY this format:\n\n"
        "HEADLINE: <a short, punchy 3-6 word viral tech headline>\n\n"
        "CAPTION: <an engaging caption explaining this specific topic with 3 key bullet points, emojis, and a strong Call-To-Action asking followers to SAVE or SHARE>\n\n"
        "HASHTAGS: #AICreator #AITools #Automation #AIAgents #NoCode #TechUpdates #BuildInPublic #PakistanTech\n\n"
        "IMAGE_PROMPT: <a concise description of visual 3D icons or infographic elements matching this exact topic>"
    )

    last_error = None
    for model in MODEL_FALLBACK_ORDER:
        try:
            generated_text = call_gemini_model(model, prompt)
            sections = parse_post_sections(generated_text)

            image_url = ""
            photo_sent = False
            if sections.get("image_prompt"):
                style_prefix = persona.get("image_style_prefix", "")
                image_url = build_image_url(sections["image_prompt"], style_prefix)
                photo_sent = send_telegram_photo(image_url, caption=sections.get("headline", ""))

            logged = log_to_sheets("Create today's Instagram post", model, sections, image_url)
            log_note = "📝 Logged to memory." if logged else "⚠️ Sheets logging failed."

            full_ig_caption = f"{sections.get('headline', '')}\n\n{sections.get('caption', '')}\n\n{sections.get('hashtags', '')}"
            published, ig_result = publish_to_instagram(image_url, full_ig_caption)
            ig_note = f"📸 Published to Instagram! (Post ID: {ig_result})" if published else f"⚠️ Instagram Publish Status: {ig_result}"

            send_telegram_message(f"✅ Today's Instagram post (via {model}):\n\n{generated_text}\n\n{log_note}\n{ig_note}")
            return
        except RuntimeError as e:
            last_error = e
            continue

    send_telegram_message(f"⚠️ All AI models failed. Last error: {last_error}")


def reply_to_comments():
    persona = load_persona()
    media_items = get_recent_media(limit=5)

    if not media_items:
        send_telegram_message("💬 No recent media found, or Instagram credentials are missing.")
        return

    total_replied = 0
    total_skipped = 0
    total_failed = 0

    for media in media_items:
        media_id = media.get("id")
        comments = get_comments_for_media(media_id)

        for comment in comments:
            comment_id = comment.get("id")
            comment_text = comment.get("text", "")
            commenter_username = comment.get("username", "unknown")

            if commenter_username.lower() == OUR_USERNAME.lower():
                continue

            if has_our_reply(comment, OUR_USERNAME):
                total_skipped += 1
                continue

            try:
                reply_text = generate_comment_reply(persona, comment_text, commenter_username)
            except RuntimeError as e:
                print(f"Failed to generate reply for comment {comment_id}: {e}")
                total_failed += 1
                continue

            success, result = reply_to_comment(comment_id, reply_text)
            if success:
                total_replied += 1
                log_reply_to_sheets(media_id, comment_id, commenter_username, comment_text, reply_text)
            else:
                total_failed += 1
                print(f"Failed to post reply to comment {comment_id}: {result}")

    send_telegram_message(
        f"💬 Comment reply run complete.\n"
        f"✅ Replied: {total_replied}\n"
        f"⏭️ Already replied (skipped): {total_skipped}\n"
        f"⚠️ Failed: {total_failed}"
    )


def main():
    trigger_event = os.environ.get("TRIGGER_EVENT", "").strip()

    if trigger_event == "schedule":
        send_telegram_message("⏰ 4-Hour Autopilot Triggered! Running Post + Reel + Comment Replies...")
        generate_instagram_post()
        time.sleep(5)
        generate_instagram_reel()
        time.sleep(5)
        reply_to_comments()
        return

    message = get_latest_message()
    stripped_message = message.strip()

    if stripped_message == "Create today's Instagram post":
        send_telegram_message("🤖 Command Recognized! Generating Instagram Post with AI Brain...")
        generate_instagram_post()
    elif stripped_message == "Create AI Reel":
        send_telegram_message("🎥 Command Recognized! Generating AI Voiceover Reel Video...")
        generate_instagram_reel()
    elif stripped_message == "Reply to comments":
        send_telegram_message("💬 Command Recognized! Checking recent posts for new comments...")
        reply_to_comments()
    elif stripped_message == "Run full pipeline":
        send_telegram_message("🚀 Running Full Pipeline: Post + Reel + Comment Replies...")
        generate_instagram_post()
        time.sleep(5)
        generate_instagram_reel()
        time.sleep(5)
        reply_to_comments()
    else:
        send_telegram_message(f"❓ Unrecognized Command: {message}")


if __name__ == "__main__":
    main()
