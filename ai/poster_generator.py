import os
import re
import textwrap
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS_DIR = "fonts"
FONT_BOLD_PATH = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")
FONT_REGULAR_PATH = os.path.join(FONTS_DIR, "Montserrat-Regular.ttf")

FONT_BOLD_URL = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf"
FONT_REGULAR_URL = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Regular.ttf"

# Brand colors
NAVY_BG = (10, 14, 39)
NAVY_BG_LIGHT = (18, 24, 58)
ORANGE = (255, 140, 46)
WHITE = (245, 245, 250)
CARD_GLOW = (255, 140, 46, 60)
CARD_FILL = (24, 30, 66)


def _ensure_fonts():
    os.makedirs(FONTS_DIR, exist_ok=True)
    if not os.path.exists(FONT_BOLD_PATH):
        urllib.request.urlretrieve(FONT_BOLD_URL, FONT_BOLD_PATH)
    if not os.path.exists(FONT_REGULAR_PATH):
        urllib.request.urlretrieve(FONT_REGULAR_URL, FONT_REGULAR_PATH)


def _load_font(path, size):
    return ImageFont.truetype(path, size)


def _wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def extract_bullets_from_text(text, max_bullets=3, min_len=6, max_len=70):
    """
    Pulls short, poster-ready bullet points out of arbitrary AI-generated
    text (a caption paragraph or a voiceover script).

    Strategy:
    1. First look for lines that already use bullet markers (•, -, *, or
       "1." / "2)" numbering) -- these are the cleanest source when present.
    2. If that yields fewer than `max_bullets`, fall back to splitting the
       text into sentence-like clauses and using those -- this is what
       actually fixes the bug, since Gemini often returns flowing
       paragraphs with no literal bullet characters at all.
    3. Never returns the old hardcoded placeholder text -- if truly
       nothing usable is found, returns an empty list, and the caller
       is responsible for a topic-aware fallback (never a generic one).
    """
    if not text:
        return []

    bullets = []

    for line in text.splitlines():
        stripped = line.strip()
        cleaned = None

        for marker in ("•", "-", "*"):
            if stripped.startswith(marker):
                cleaned = stripped[1:].strip()
                break

        if cleaned is None:
            numbered = re.match(r"^\d+[\.\)]\s*(.+)", stripped)
            if numbered:
                cleaned = numbered.group(1).strip()

        if cleaned and min_len <= len(cleaned) <= max_len:
            bullets.append(cleaned)
        elif cleaned and len(cleaned) > max_len:
            trimmed = cleaned[:max_len - 3].rsplit(" ", 1)[0] + "..."
            bullets.append(trimmed)

        if len(bullets) >= max_bullets:
            return bullets[:max_bullets]

    # Fallback: sentence-level split, since most Gemini captions/scripts
    # arrive as flowing prose rather than literal bulleted lines
    raw = re.sub(r"\s+", " ", text).strip()
    clauses = re.split(r"(?<=[.!?])\s+", raw)

    for clause in clauses:
        clause = clause.strip().strip("#").strip()
        if not clause or len(clause) < min_len:
            continue
        if clause in bullets:
            continue
        if len(clause) > max_len:
            clause = clause[:max_len - 3].rsplit(" ", 1)[0] + "..."
        bullets.append(clause)
        if len(bullets) >= max_bullets:
            break

    return bullets[:max_bullets]


def _draw_glow_card(base_img, xy, size, radius=30):
    """Draws a soft glowing rounded rectangle card behind content."""
    x, y = xy
    w, h = size

    glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle(
        [x - 8, y - 8, x + w + 8, y + h + 8],
        radius=radius + 8,
        fill=CARD_GLOW
    )
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(18))
    base_img.alpha_composite(glow_layer)

    card_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=radius,
        fill=(*CARD_FILL, 255),
        outline=(*ORANGE, 180),
        width=2
    )
    base_img.alpha_composite(card_layer)


def _background(size):
    img = Image.new("RGBA", size, (*NAVY_BG, 255))
    draw = ImageDraw.Draw(img)
    for i in range(size[1]):
        blend = i / size[1]
        r = int(NAVY_BG[0] + (NAVY_BG_LIGHT[0] - NAVY_BG[0]) * blend)
        g = int(NAVY_BG[1] + (NAVY_BG_LIGHT[1] - NAVY_BG[1]) * blend)
        b = int(NAVY_BG[2] + (NAVY_BG_LIGHT[2] - NAVY_BG[2]) * blend)
        draw.line([(0, i), (size[0], i)], fill=(r, g, b, 255))
    return img


def generate_poster(headline, bullets, output_path, size=(1080, 1080),
                     handle="@muhammad_musa125001", cta_text="💾 Save this for later"):
    _ensure_fonts()

    width, height = size
    img = _background(size)
    draw = ImageDraw.Draw(img)

    margin = int(width * 0.08)
    content_width = width - (margin * 2)

    headline_font_size = int(width * 0.075)
    bullet_font_size = int(width * 0.042)
    cta_font_size = int(width * 0.038)
    handle_font_size = int(width * 0.034)

    headline_font = _load_font(FONT_BOLD_PATH, headline_font_size)
    bullet_font = _load_font(FONT_BOLD_PATH, bullet_font_size)
    cta_font = _load_font(FONT_REGULAR_PATH, cta_font_size)
    handle_font = _load_font(FONT_BOLD_PATH, handle_font_size)

    y_cursor = int(height * 0.07)
    headline_lines = _wrap_text(headline.upper(), headline_font, content_width, draw)
    for i, line in enumerate(headline_lines[:3]):
        color = ORANGE if i == len(headline_lines[:3]) - 1 else WHITE
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        line_h = bbox[3] - bbox[1]
        draw.text((margin, y_cursor), line, font=headline_font, fill=color)
        y_cursor += int(line_h * 1.35)

    y_cursor += int(height * 0.04)

    max_bullets = 4 if size[1] > size[0] else 3
    bullets_to_show = bullets[:max_bullets] if bullets else []

    available_height = height - y_cursor - int(height * 0.18)
    card_gap = int(height * 0.025)
    card_height = (available_height - (card_gap * max(0, len(bullets_to_show) - 1))) // max(1, len(bullets_to_show))
    card_height = min(card_height, int(height * 0.14))

    for bullet in bullets_to_show:
        _draw_glow_card(img, (margin, y_cursor), (content_width, card_height))

        text_lines = _wrap_text(bullet, bullet_font, content_width - int(width * 0.06), draw)
        line_bbox = draw.textbbox((0, 0), "Ag", font=bullet_font)
        line_h = line_bbox[3] - line_bbox[1]
        text_block_h = line_h * 1.3 * len(text_lines)
        text_y = y_cursor + (card_height - text_block_h) / 2

        draw = ImageDraw.Draw(img)
        for line in text_lines[:2]:
            draw.text((margin + int(width * 0.03), text_y), line, font=bullet_font, fill=WHITE)
            text_y += line_h * 1.3

        y_cursor += card_height + card_gap

    cta_y = height - int(height * 0.13)
    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    draw.text(((width - cta_w) / 2, cta_y), cta_text, font=cta_font, fill=ORANGE)

    handle_y = height - int(height * 0.07)
    handle_bbox = draw.textbbox((0, 0), handle, font=handle_font)
    handle_w = handle_bbox[2] - handle_bbox[0]
    draw.text(((width - handle_w) / 2, handle_y), handle, font=handle_font, fill=WHITE)

    final_img = img.convert("RGB")
    final_img.save(output_path, "PNG", quality=95)
    print(f"Poster generated: {output_path} ({size[0]}x{size[1]})")
    return output_path


def generate_square_poster(headline, bullets, output_path="poster_square.png"):
    return generate_poster(headline, bullets, output_path, size=(1080, 1080))


def generate_vertical_poster(headline, bullets, output_path="poster_vertical.png"):
    return generate_poster(headline, bullets, output_path, size=(1080, 1920))
