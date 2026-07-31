def parse_post_sections(generated_text):
    sections = {"headline": "", "caption": "", "hashtags": "", "image_prompt": ""}
    current_key = None
    label_map = {
        "HEADLINE:": "headline",
        "CAPTION:": "caption",
        "HASHTAGS:": "hashtags",
        "IMAGE_PROMPT:": "image_prompt"
    }

    for line in generated_text.splitlines():
        stripped = line.strip()
        matched = False
        for label, key in label_map.items():
            if stripped.startswith(label):
                current_key = key
                sections[key] = stripped[len(label):].strip()
                matched = True
                break
        if not matched and current_key and stripped:
            sections[current_key] += " " + stripped
    return sections
