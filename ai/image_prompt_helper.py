import random
import urllib.parse

def build_image_url(image_prompt, style_prefix=""):
    combined_prompt = f"{style_prefix} {image_prompt}"[:250]
    encoded_prompt = urllib.parse.quote(combined_prompt)
    random_seed = random.randint(1000, 999999)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed={random_seed}"
