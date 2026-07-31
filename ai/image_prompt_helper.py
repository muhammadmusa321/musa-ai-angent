import random
import urllib.parse
from ai.poster_generator import generate_square_poster

def build_image_url(image_prompt, style_prefix="", headline="", caption_text=""):
    try:
        bullets = []
        if caption_text:
            for l in caption_text.splitlines():
                l_strip = l.strip()
                if l_strip.startswith("•") or l_strip.startswith("-") or l_strip.startswith("*"):
                    bullets.append(l_strip)
        
        if not bullets:
            bullets = [
                "• 10x Content Output with AI Workers",
                "• No Coding Required & Fast Setup",
                "• Automate Repetitive Daily Tasks"
            ]

        poster_title = headline if headline else "AI AUTOMATION UPDATE"
        poster_path = generate_square_poster(poster_title, bullets, output_path="infographic.png")
        return poster_path
    except Exception as e:
        print(f"Pillow Poster Generation Fallback: {e}")
        combined_prompt = f"{style_prefix} {image_prompt}"[:250]
        encoded_prompt = urllib.parse.quote(combined_prompt)
        random_seed = random.randint(1000, 999999)
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed={random_seed}"
