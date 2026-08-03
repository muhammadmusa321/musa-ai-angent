import io
import random
import re
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageOps


def extract_bullets_from_text(text, max_bullets=3):
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    bullets = []

    bullet_pattern = re.compile(r"^\s*(?:[•\-\*]|\d+[.)])\s*(.+)")
    for line in lines:
        match = bullet_pattern.match(line)
        if match:
            cleaned = match.group(1).strip()
            if cleaned:
                bullets.append(cleaned)
        if len(bullets) >= max_bullets:
            return bullets[:max_bullets]

    if bullets:
        return bullets[:max_bullets]

    flat_text = " ".join(line.strip() for line in lines if line.strip())
    clauses = re.split(r"(?<=[.!?])\s+", flat_text)
    clauses = [c.strip() for c in clauses if c.strip()]

    return clauses[:max_bullets]


def _load_fonts(is_vertical):
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56 if is_vertical else 46)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font_title = font_body = font_small = ImageFont.load_default()
    return font_title, font_body, font_small


def _fetch_pollinations_image(prompt, width, height, timeout=45):
    """100% free — no API key. Pollinations.ai generates a real AI image from a text prompt."""
    encoded_prompt = urllib.parse.quote((prompt or "modern AI technology")[:250])
    seed = random.randint(1, 999999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&nologo=true&model=flux&seed={seed}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        img_bytes = resp.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return ImageOps.fit(img, (width, height), method=Image.LANCZOS)


def _solid_gradient_fallback(width, height):
    """Used only if Pollinations.ai is unreachable -- keeps the pipeline free and always working."""
    img = Image.new("RGB", (width, height), color=(10, 15, 29))
    draw = ImageDraw.Draw(img)
    top_color = (12, 18, 38)
    bottom_color = (35, 15, 60)
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def _draw_text_overlay(img, headline, bullets, handle, is_vertical):
    width, height = img.size
    img = img.convert("RGBA")
    font_title, font_body, font_small = _load_fonts(is_vertical)

    panel_height = int(height * (0.46 if is_vertical else 0.4)) if bullets else int(height * 0.22)
    gradient = Image.new("L", (1, panel_height), color=0)
    for y in range(panel_height):
        gradient.putpixel((0, y), int(235 * (y / panel_height)))
    gradient = gradient.resize((width, panel_height))
    black_panel = Image.new("RGBA", (width, panel_height), (5, 8, 20, 255))
    black_panel.putalpha(gradient)
    img.paste(black_panel, (0, height - panel_height), black_panel)

    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([50, 40, width - 50, 48], fill=(255, 102, 0, 255))

    y_offset = 90
    words = headline.upper().split()
    line = ""
    max_chars = 18 if is_vertical else 20
    headline_lines = []
    for word in words:
        if len(line + " " + word) < max_chars:
            line += " " + word
        else:
            headline_lines.append(line.strip())
            line = word
    if line:
        headline_lines.append(line.strip())

    for i, hl in enumerate(headline_lines):
        color = (255, 102, 0, 255) if i == len(headline_lines) - 1 else (255, 255, 255, 255)
        draw.text((60, y_offset), hl, fill=color, font=font_title)
        y_offset += 66 if is_vertical else 56

    if bullets:
        bullet_y = height - panel_height + 40
        for bullet in bullets[:3]:
            display_text = bullet if bullet.startswith(("•", "-")) else f"• {bullet}"
            draw.text((60, bullet_y), display_text[:58], fill=(240, 240, 240, 255), font=font_body)
            bullet_y += 46

    draw.text((60, height - 55), handle, fill=(150, 160, 180, 255), font=font_small)
    return img.convert("RGB")


def generate_ai_poster(image_prompt, headline, bullets, output_path, width=1080, height=1080, handle="@muhammad_musa125001"):
    try:
        bg = _fetch_pollinations_image(image_prompt or headline, width, height)
        print("Using free Pollinations.ai AI-generated background.")
    except Exception as e:
        print(f"Pollinations.ai unavailable, using gradient fallback (still free): {e}")
        bg = _solid_gradient_fallback(width, height)

    final_img = _draw_text_overlay(bg, headline, bullets, handle, is_vertical=(height > width))
    final_img.save(output_path, "JPEG", quality=92)
    print(f"Generated AI poster: {output_path}")
    return output_path


def generate_square_poster(headline, bullets, output_path="infographic.jpg", handle="@muhammad_musa125001", image_prompt=None):
    return generate_ai_poster(image_prompt or headline, headline, bullets, output_path, width=1080, height=1080, handle=handle)


def generate_vertical_poster(headline, bullets, output_path="bg.jpg", handle="@muhammad_musa125001", image_prompt=None):
    return generate_ai_poster(image_prompt or headline, headline, bullets, output_path, width=1080, height=1920, handle=handle)


def generate_clean_infographic(headline, caption_text="", handle="@muhammad_musa125001", output_path="infographic.jpg", is_vertical=False, image_prompt=None):
    bullets = extract_bullets_from_text(caption_text, max_bullets=3)
    width, height = (1080, 1920) if is_vertical else (1080, 1080)
    return generate_ai_poster(image_prompt or headline, headline, bullets, output_path, width=width, height=height, handle=handle)
