"""
Image Creator — Phase 1
Generates LinkedIn-optimised images using DALL·E 3.
Auto-builds prompts from post context + style settings.
"""

import os
import re
import requests
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# LinkedIn image best practices
# Optimal size: 1200×627px (1.91:1 ratio) for link posts
# Square 1080×1080 also performs well for pure image posts
IMAGE_SPECS = {
    "LinkedIn Banner (1200×627)": {"size": "1792x1024", "ratio": "landscape"},
    "Square Post (1080×1080)":    {"size": "1024x1024", "ratio": "square"},
    "Portrait (1080×1350)":       {"size": "1024x1792", "ratio": "portrait"},
}

STYLE_CONFIGS = {
    "Professional & Clean": {
        "visual_style": "clean minimalist corporate design, white background, professional typography, subtle geometric accents",
        "colours":      "navy blue, white, and gold accents",
        "mood":         "trustworthy, polished, executive",
    },
    "Bold & Typographic": {
        "visual_style": "bold typographic poster design, large impactful text, strong layout, editorial design",
        "colours":      "high contrast black and white with one vivid accent colour",
        "mood":         "impactful, modern, magazine-quality",
    },
    "Abstract & Artistic": {
        "visual_style": "abstract digital art, flowing shapes, conceptual imagery, artistic composition",
        "colours":      "rich jewel tones, deep purples and teals",
        "mood":         "creative, thought-provoking, unique",
    },
    "Data Visualisation": {
        "visual_style": "clean data visualisation style, charts or graphs as design elements, infographic aesthetic",
        "colours":      "cool blues, data-science palette, clean whites",
        "mood":         "analytical, credible, insightful",
    },
    "Photorealistic": {
        "visual_style": "photorealistic scene, professional photography style, natural lighting",
        "colours":      "natural, warm photographic tones",
        "mood":         "authentic, human, cinematic",
    },
    "Minimalist": {
        "visual_style": "extreme minimalism, single focal element, vast white space, refined simplicity",
        "colours":      "monochrome with one accent",
        "mood":         "calm, premium, zen-like clarity",
    },
}

MOOD_CONFIGS = {
    "Inspiring & Uplifting":       "uplifting, hopeful, growth-oriented imagery",
    "Serious & Authoritative":     "serious, authoritative, commanding presence",
    "Playful & Creative":          "playful, creative, energetic, fun",
    "Futuristic & Tech":           "futuristic, technological, digital, innovation",
    "Warm & Human":                "warm, human connection, approachable, empathetic",
}


class ImageCreator:
    def __init__(self):
        self.openai   = OpenAI(api_key=OPENAI_KEY)     if OPENAI_KEY    else None
        self.anthropic = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

    def _build_image_prompt(
        self,
        post_content: str,
        topic: dict,
        style: str,
        mood: str,
        custom_details: str,
    ) -> str:
        """Use Claude to craft an optimised DALL·E 3 image prompt."""

        style_cfg = STYLE_CONFIGS.get(style, STYLE_CONFIGS["Professional & Clean"])
        mood_desc = MOOD_CONFIGS.get(mood, "professional and inspiring")

        # Extract key theme from post
        post_snippet = post_content[:500].replace("\n", " ")
        topic_title  = topic.get("title", "professional content")

        if self.anthropic:
            try:
                resp = self.anthropic.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=300,
                    messages=[{
                        "role": "user",
                        "content": f"""Create a concise, specific DALL·E 3 image prompt for a LinkedIn post.

Post topic: {topic_title}
Post excerpt: {post_snippet[:300]}
Visual style: {style_cfg['visual_style']}
Colour palette: {style_cfg['colours']}
Mood: {style_cfg['mood']}, {mood_desc}
Custom details: {custom_details if custom_details else 'none'}

Rules:
- Must be LinkedIn-appropriate, professional
- No people's faces (avoid face recognition issues)
- No text in the image (LinkedIn renders post text separately)
- Focus on concept/metaphor that represents the topic
- Mention the aspect ratio: optimised for LinkedIn 1.91:1 format
- Keep it under 200 words

Output ONLY the image prompt, nothing else.""",
                    }],
                )
                base_prompt = resp.content[0].text.strip()
            except Exception:
                base_prompt = self._fallback_prompt(topic_title, style_cfg, mood_desc, custom_details)
        else:
            base_prompt = self._fallback_prompt(topic_title, style_cfg, mood_desc, custom_details)

        # Append quality and safety suffixes
        final_prompt = (
            f"{base_prompt}, "
            f"professional LinkedIn image, high quality, "
            f"no text overlays, no human faces shown, "
            f"suitable for business social media, 1200x627 format."
        )
        return final_prompt

    def _fallback_prompt(self, topic_title: str, style_cfg: dict, mood_desc: str, custom: str) -> str:
        custom_part = f", {custom}" if custom else ""
        return (
            f"A {style_cfg['visual_style']} image representing {topic_title}. "
            f"Colours: {style_cfg['colours']}. "
            f"Mood: {mood_desc}{custom_part}. "
            f"Abstract conceptual art, no text, no faces, professional business context."
        )

    def generate(
        self,
        post_content: str,
        topic: dict,
        style: str = "Professional & Clean",
        mood: str = "Inspiring & Uplifting",
        custom_details: str = "",
        size_preset: str = "LinkedIn Banner (1200×627)",
    ) -> dict:
        """
        Generate a LinkedIn image using DALL·E 3.
        Returns dict with: url, prompt_used, size, revised_prompt
        """
        prompt  = self._build_image_prompt(post_content, topic, style, mood, custom_details)
        size    = IMAGE_SPECS.get(size_preset, IMAGE_SPECS["LinkedIn Banner (1200×627)"])["size"]

        if not self.openai:
            # Return a placeholder if no API key
            return {
                "url":            "https://via.placeholder.com/1200x627/5b6bff/ffffff?text=LinkedIn+Image+Preview",
                "prompt_used":    prompt,
                "size":           size,
                "revised_prompt": prompt,
                "note":           "Demo mode — set OPENAI_API_KEY to generate real images",
            }

        try:
            response = self.openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="hd",
                n=1,
            )
            image_data = response.data[0]
            return {
                "url":            image_data.url,
                "prompt_used":    prompt,
                "size":           size,
                "revised_prompt": getattr(image_data, "revised_prompt", prompt),
            }
        except Exception as e:
            print(f"DALL·E 3 error: {e}")
            # Try standard quality as fallback
            try:
                response = self.openai.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1792x1024",
                    quality="standard",
                    n=1,
                )
                image_data = response.data[0]
                return {
                    "url":            image_data.url,
                    "prompt_used":    prompt,
                    "size":           "1792x1024",
                    "revised_prompt": getattr(image_data, "revised_prompt", prompt),
                }
            except Exception as e2:
                print(f"DALL·E 3 fallback error: {e2}")
                return {
                    "url":            "https://via.placeholder.com/1200x627/5b6bff/ffffff?text=Image+Generation+Failed",
                    "prompt_used":    prompt,
                    "size":           size,
                    "revised_prompt": prompt,
                    "error":          str(e2),
                }

    def regenerate_with_variation(
        self,
        original_prompt: str,
        variation_instruction: str,
    ) -> dict:
        """Regenerate with a specific variation instruction."""
        varied_prompt = f"{original_prompt} BUT: {variation_instruction}"
        if not self.openai:
            return {"url": "https://via.placeholder.com/1200x627/b44fff/ffffff?text=Variation", "prompt_used": varied_prompt}

        try:
            response = self.openai.images.generate(
                model="dall-e-3",
                prompt=varied_prompt,
                size="1792x1024",
                quality="hd",
                n=1,
            )
            return {
                "url":         response.data[0].url,
                "prompt_used": varied_prompt,
            }
        except Exception as e:
            return {"url": None, "error": str(e), "prompt_used": varied_prompt}
