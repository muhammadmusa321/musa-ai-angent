import os
import re
from PIL import Image, ImageDraw, ImageFont


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


def _generate_infographic_core(headline, bullets, output_path, handle="@muhammad_musa125001", is_vertical=False):
    width = 1080
    height = 1920 if is_vertical else 1080

    img = Image.new("RGB", (width, height), color=(10, 15, 29))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52 if is_vertical else 46)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except Exception:
        font_title = font_body = font_small = ImageFont.load_default()

    draw.rectangle([50, 40, width - 50, 48], fill=(255, 102, 0))

    y_offset = 100
    words = headline.upper().split()
    line = ""
    for word in words:
        if len(line + " " + word) < 20:
            line += " " + word
        else:
            draw.text((60, y_offset), line.strip(), fill=(255, 255, 255), font=font_title)
            y_offset += 65
            line = word
    if line:
        draw.text((60, y_offset), line.strip(), fill=(255, 102, 0), font=font_title)
        y_offset += 85

    card_colors = [(255, 102, 0), (255, 51, 102), (153, 51, 255)]
    card_y = y_offset + 30

    for i, bullet in enumerate(bullets[:3]):
        box_color = card_colors[i % 3]
        draw.rounded_rectangle([60, card_y, width - 60, card_y + 140], radius=15, fill=(18, 25, 45), outline=box_color, width=3)
        display_text = bullet if bullet.startswith(("•", "-")) else f"• {bullet}"
        draw.text((90, card_y + 45), display_text[:55], fill=(240, 240, 240), font=font_body)
        card_y += 170

    draw.text((60, height - 120), "SAVE for later 📌  |  Comment below ⬇️", fill=(255, 153, 51), font=font_small)
    draw.text((60, height - 60), handle, fill=(150, 160, 180), font=font_small)

    # Always saved as JPEG regardless of the extension in output_path -- callers
    # should pass a .jpg path to keep the filename consistent with the actual
    # file content.
    img.save(output_path, "JPEG", quality=95)
    print(f"Generated Clean Text Infographic: {output_path}")
    return output_path


def generate_square_poster(headline, bullets, output_path="infographic.jpg", handle="@muhammad_musa125001"):
    return _generate_infographic_core(headline, bullets, output_path, handle=handle, is_vertical=False)


def generate_vertical_poster(headline, bullets, output_path="bg.jpg", handle="@muhammad_musa125001"):
    return _generate_infographic_core(headline, bullets, output_path, handle=handle, is_vertical=True)


def generate_clean_infographic(headline, caption_text="", handle="@muhammad_musa125001", output_path="infographic.jpg", is_vertical=False):
    bullets = extract_bullets_from_text(caption_text, max_bullets=3)
    return _generate_infographic_core(headline, bullets, output_path, handle=handle, is_vertical=is_vertical)
