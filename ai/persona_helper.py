import json

def load_persona():
    try:
        with open("persona.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "system_prompt": "Generate an engaging Instagram post about modern AI tools.",
            "topics": ["AI Tools & Automation"],
            "image_style_prefix": "3D dark-mode tech graphic: "
  }
