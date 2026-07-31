import os
import time
from utils.telegram_helper import send_telegram_message, get_latest_message
from utils.pipeline_helper import generate_instagram_post, generate_instagram_reel, reply_to_comments

TOPIC_PREFIXES = ["topic:", "Topic:"]


def extract_custom_topic(message):
    stripped = message.strip()
    lower = stripped.lower()
    if lower.startswith("topic:"):
        return stripped[len("topic:"):].strip()
    return None


def main():
    trigger_event = os.environ.get("TRIGGER_EVENT", "").strip()

    if trigger_event == "schedule":
        send_telegram_message("⏰ Autopilot Triggered! Running Post + Reel + Comment Replies...")
        generate_instagram_post()
        time.sleep(5)
        generate_instagram_reel()
        time.sleep(5)
        reply_to_comments()
        return

    message = get_latest_message()
    stripped_message = message.strip()

    custom_topic = extract_custom_topic(stripped_message)

    if custom_topic is not None:
        if not custom_topic:
            send_telegram_message("⚠️ Please include a topic after 'Topic:', e.g. 'Topic: Top 3 Claude Prompts'.")
            return
        send_telegram_message(f"🎯 Custom Topic Recognized: \"{custom_topic}\"\nGenerating Post + Reel for this topic...")
        generate_instagram_post(custom_topic=custom_topic)
        time.sleep(5)
        generate_instagram_reel(custom_topic=custom_topic)
    elif stripped_message == "Create today's Instagram post":
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
