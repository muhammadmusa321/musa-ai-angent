import random
from telegram_helper import send_telegram_message, send_telegram_photo, get_latest_message
from ai_helper import load_persona, call_gemini_model, parse_post_sections, build_image_url, MODEL_FALLBACK_ORDER
from sheets_helper import log_to_sheets
from instagram_helper import publish_to_instagram

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

            # Step 11: Auto Publish directly to Instagram
            full_ig_caption = f"{sections.get('headline', '')}\n\n{sections.get('caption', '')}\n\n{sections.get('hashtags', '')}"
            published, ig_result = publish_to_instagram(image_url, full_ig_caption)
            ig_note = f"📸 Published to Instagram! (Post ID: {ig_result})" if published else f"⚠️ Instagram Publish Status: {ig_result}"

            send_telegram_message(f"✅ Today's Instagram post (via {model}):\n\n{generated_text}\n\n{log_note}\n{ig_note}")
            return
        except RuntimeError as e:
            last_error = e
            continue

    send_telegram_message(f"⚠️ All AI models failed. Last error: {last_error}")

def main():
    message = get_latest_message()
    if message.strip() == "Create today's Instagram post":
        send_telegram_message("🤖 Command Recognized! Generating Instagram Post with AI Brain...")
        generate_instagram_post()
    else:
        send_telegram_message(f"❓ Unrecognized Command: {message}")

if __name__ == "__main__":
    main()
