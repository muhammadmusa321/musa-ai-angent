import os
import time
from utils.telegram_helper import send_telegram_message, get_latest_message
from utils.pipeline_helper import generate_instagram_post, generate_instagram_reel, reply_to_comments


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
