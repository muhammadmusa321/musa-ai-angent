from ai.gemini_helper import call_gemini_model, MODEL_FALLBACK_ORDER

def generate_comment_reply(persona, comment_text, commenter_username):
    account_name = persona.get("account_name", "the creator")
    niche = persona.get("niche", "AI and automation")

    prompt = (
        f"You are replying to a comment on an Instagram post, as {account_name}, "
        f"a creator in the '{niche}' niche. "
        f"A follower named '{commenter_username}' commented: \"{comment_text}\"\n\n"
        "Write a short, warm, genuine reply (1-2 sentences max, 1 emoji max). "
        "Sound like a real person, not a bot. Do not repeat the commenter's words back robotically. "
        "Do not include quotation marks, labels, or any prefix — respond with ONLY the reply text itself."
    )

    last_error = None
    for model in MODEL_FALLBACK_ORDER:
        try:
            reply_text = call_gemini_model(model, prompt)
            return reply_text.strip().strip('"')
        except RuntimeError as e:
            last_error = e
            continue

    raise RuntimeError(f"All models failed to generate a reply: {last_error}")
