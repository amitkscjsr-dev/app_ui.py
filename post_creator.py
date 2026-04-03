"""
Post Creator — Phase 1
Generates LinkedIn posts using Claude (Version A) and GPT-4o (Version B)
for A/B testing with full LinkedIn optimisation.
"""

import os
import re
import concurrent.futures
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")


# ─── Hook Type Library ────────────────────────────────────────────────────────
HOOK_PATTERNS = {
    "Pattern Interrupt":    "Start with a statement that contradicts common belief",
    "Question Hook":        "Open with a thought-provoking question",
    "Number Hook":          "Lead with a specific statistic or number",
    "Story Hook":           "Open mid-scene, in the middle of an action",
    "Bold Claim":           "Make a surprising, bold declarative statement",
    "Confession Hook":      "Start with a personal admission or mistake",
    "Future Vision":        "Paint a picture of what's coming that readers need to know",
}

# ─── Tone Configurations ──────────────────────────────────────────────────────
TONE_CONFIGS = {
    "Insightful & Authoritative":   {"style": "confident expert sharing hard-won knowledge", "cta_style": "ask for their perspective"},
    "Conversational & Relatable":   {"style": "a friend sharing lessons over coffee", "cta_style": "ask a relatable question"},
    "Provocative & Bold":           {"style": "thought leader making a bold contrarian claim", "cta_style": "challenge them to disagree"},
    "Storytelling & Personal":      {"style": "storyteller revealing a pivotal personal moment", "cta_style": "invite them to share their story"},
    "Data-Driven & Analytical":     {"style": "analyst revealing surprising data patterns", "cta_style": "ask what surprised them"},
    "Motivational & Inspiring":     {"style": "mentor who has walked the path and returned", "cta_style": "encourage them to share their journey"},
}


def _build_master_prompt(topic: dict, research: dict, niche: str, tone: str, audience: str, author: str, model_personality: str) -> str:
    """Build the comprehensive LinkedIn post generation prompt."""

    tone_cfg   = TONE_CONFIGS.get(tone, TONE_CONFIGS["Insightful & Authoritative"])
    web_context = research.get("web", {}).get("summary", "")[:500] if research else ""
    paper_refs  = "; ".join(research.get("papers", {}).get("titles", [])[:2]) if research else ""

    return f"""You are an elite LinkedIn ghostwriter who has helped creators build 100K+ followings in {niche}.

Your task: Write a complete, high-performing LinkedIn post.

TOPIC: {topic['title']}
HOOK PREVIEW TO BUILD FROM: {topic['hook_preview']}
FORMAT TO USE: {topic['format']}
NICHE: {niche}
AUDIENCE: {audience}
TONE: {tone} — write as {tone_cfg['style']}
AUTHOR: {author}
MODEL PERSONALITY: {model_personality}

RESEARCH CONTEXT:
{web_context}
{f'Research references: {paper_refs}' if paper_refs else ''}

─────────────────────────────────────────
LINKEDIN POST FORMULA (follow this exactly):

1. HOOK (Lines 1-2, max 200 chars combined)
   - Must create a "stop-scroll" moment
   - No "I'm excited to share" or "Thrilled to announce" — those are dead phrases
   - Use one of: bold claim / surprising stat / open loop / pattern interrupt / mid-story drop-in
   - These two lines appear BEFORE the "see more" fold — they must earn the click

2. BLANK LINE (mandatory — breaks the fold, invites the "see more" tap)

3. BODY (3-7 paragraphs, each 1-3 lines)
   - Short paragraphs — LinkedIn readers scan, not read
   - Every paragraph must earn its place
   - Use the {topic['format']} structure
   - Include 1 specific example, data point, or personal story
   - Build curiosity progressively — never reveal everything at once
   - Use white space generously (line breaks between each paragraph)

4. LESSON / INSIGHT SECTION
   - If using a list format: 3-5 punchy bullet points (use → or ▸ instead of numbers when possible)
   - If story format: the "what I learned" moment
   - If data format: the "what this means for you" section

5. ENGAGING QUESTION (1 line, conversational)
   - {tone_cfg['cta_style']}
   - Must feel natural, not forced
   - Example: "What's been your experience with this?" or "Which of these surprised you most?"

6. CALL TO ACTION (subtle, 1 line)
   - Soft: "Follow for more on {niche}" or "Save this for when you need it"
   - Never beg ("Please like and share!") — that destroys credibility

7. HASHTAGS (line break before, 3-5 max)
   - First hashtag: broad niche (#AI, #Leadership, #Marketing)
   - Second: specific (#AItools, #StartupLife)
   - Third: audience (#Founders, #Professionals)
   - NO more than 5 — algorithm penalises hashtag stuffing

─────────────────────────────────────────
RULES:
✓ Total length: 900–1800 characters (sweet spot for LinkedIn algorithm)
✓ Reading level: 8th grade — simple words, powerful ideas
✓ No corporate jargon, no buzzwords ("synergy", "leverage", "paradigm shift")
✓ Use "you" frequently — make the reader feel seen
✓ Emojis: 2-4 max, only if they add meaning (not decoration)
✓ No em-dashes (—) overuse — LinkedIn renders them oddly on mobile
✓ End every paragraph on a strong beat — no weak trailing sentences
✗ NEVER start with "I" as the first word
✗ NEVER use generic openers: "In today's world...", "As we navigate...", "I'm excited to..."
✗ Do NOT include [Author Name] or any placeholders

Write the complete post now. Output ONLY the post text, nothing else — no "Here is your post:" preamble."""


def _analyse_post(content: str) -> dict:
    """Extract metadata from a generated post."""
    char_count    = len(content)
    hashtags      = re.findall(r"#\w+", content)
    words         = content.split()
    word_count    = len(words)
    read_time     = f"{max(1, round(word_count / 238))} min"

    # Detect hook type
    first_line = content.split("\n")[0].lower()
    hook_type  = "Bold Claim"
    if "?" in first_line:
        hook_type = "Question Hook"
    elif any(c.isdigit() for c in first_line[:20]):
        hook_type = "Number Hook"
    elif any(w in first_line for w in ["i ", "my ", "i'", "me "]):
        hook_type = "Story / Confession"
    elif any(w in first_line for w in ["most ", "everyone", "nobody", "stop"]):
        hook_type = "Pattern Interrupt"

    return {
        "char_count":    char_count,
        "word_count":    word_count,
        "hashtag_count": len(hashtags),
        "hashtags":      hashtags,
        "read_time":     read_time,
        "hook_type":     hook_type,
    }


class PostCreator:
    def __init__(self, niche: str, tone: str, audience: str, author: str):
        self.niche    = niche
        self.tone     = tone
        self.audience = audience
        self.author   = author
        self.claude   = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
        self.openai   = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

    # ── Generate single post (Claude) ────────────────────────────────────
    def _generate_claude(self, topic: dict, research: dict) -> dict:
        prompt = _build_master_prompt(
            topic, research, self.niche, self.tone, self.audience, self.author,
            model_personality="Claude: precise, nuanced, with a literary quality. Favours elegant sentence construction.",
        )
        if not self.claude:
            return self._mock_post("Claude 3.5 Sonnet", topic)

        try:
            resp = self.claude.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text.strip()
            meta    = _analyse_post(content)
            return {"content": content, "model": "Claude 3.5 Sonnet", **meta}
        except Exception as e:
            print(f"Claude generation error: {e}")
            return self._mock_post("Claude 3.5 Sonnet", topic)

    # ── Generate single post (GPT-4o) ───────────────────────────────────
    def _generate_gpt4o(self, topic: dict, research: dict) -> dict:
        prompt = _build_master_prompt(
            topic, research, self.niche, self.tone, self.audience, self.author,
            model_personality="GPT-4o: punchy, conversational, direct. Favours short sentences and high energy.",
        )
        if not self.openai:
            return self._mock_post("GPT-4o", topic)

        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                max_tokens=1200,
                messages=[
                    {"role": "system", "content": f"You are an elite LinkedIn ghostwriter specialising in {self.niche}."},
                    {"role": "user",   "content": prompt},
                ],
            )
            content = resp.choices[0].message.content.strip()
            meta    = _analyse_post(content)
            return {"content": content, "model": "GPT-4o", **meta}
        except Exception as e:
            print(f"GPT-4o generation error: {e}")
            return self._mock_post("GPT-4o", topic)

    # ── A/B Generation (parallel) ────────────────────────────────────────
    def generate_ab(self, topic: dict, research: dict) -> tuple:
        """Generate both versions in parallel using threads."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(self._generate_claude, topic, research)
            future_b = executor.submit(self._generate_gpt4o,  topic, research)
            post_a   = future_a.result()
            post_b   = future_b.result()
        return post_a, post_b

    # ── Single regeneration ──────────────────────────────────────────────
    def generate_single(self, topic: dict, model: str, research: dict) -> dict:
        if model == "claude":
            return self._generate_claude(topic, research)
        return self._generate_gpt4o(topic, research)

    # ── Mock post (when API keys not set) ───────────────────────────────
    def _mock_post(self, model_name: str, topic: dict) -> dict:
        content = f"""{topic['hook_preview']}

Here's what I discovered after going deep on this topic:

Most people think they understand it. They don't.

The real insight? It's not about what you know — it's about what you're willing to unlearn.

→ Lesson 1: The conventional wisdom is wrong in one specific way
→ Lesson 2: The people succeeding are doing the opposite of what's taught
→ Lesson 3: One small shift changes everything

I've seen this pattern across dozens of cases in {self.niche}. The ones who thrive aren't smarter — they're just asking different questions.

What's the one belief about {self.niche} you've had to unlearn?

Follow for more unfiltered insights on {self.niche}.

#{self.niche.replace(' ','').replace('&','And')} #LinkedIn #ProfessionalGrowth"""

        meta = _analyse_post(content)
        return {"content": content, "model": f"{model_name} (demo)", **meta}
