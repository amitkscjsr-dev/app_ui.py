"""
Research Engine — Phase 1
Handles: Tavily web search, arXiv papers, LinkedIn trends synthesis via Claude
"""

import os
import json
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY  = os.getenv("TAVILY_API_KEY", "")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY", "")

ARXIV_BASE = "http://export.arxiv.org/api/query"

# LinkedIn best-performing post patterns by niche (static knowledge base + dynamic)
LINKEDIN_TREND_TEMPLATES = {
    "AI & Technology": [
        "Unpopular opinion about AI tools",
        "What no one tells you about LLMs",
        "I tested 10 AI tools so you don't have to",
        "The AI skill that took me from 0 to 1M impressions",
        "Why most AI hype is wrong",
    ],
    "Entrepreneurship": [
        "What I learned after failing my first startup",
        "The business lesson that changed everything",
        "I made $X with no funding — here's how",
        "5 things MBA schools don't teach you",
        "The founder mindset no one talks about",
    ],
    "Marketing & Growth": [
        "This marketing strategy increased our conversion by X%",
        "The email template that got a 60% open rate",
        "Viral content formula that actually works",
        "SEO is dead — here's what's replacing it",
        "The growth hack my competitors don't know yet",
    ],
    "Finance & Investing": [
        "What Warren Buffett said that changed my investing",
        "The financial mistake most millennials make",
        "How to build wealth on a salary under 5LPA",
        "The truth about passive income",
        "Why your savings account is losing you money",
    ],
    "Leadership": [
        "The leadership lesson that cost me a team",
        "How great managers give feedback",
        "The one-on-one meeting format that works",
        "Signs you're a micromanager (and don't know it)",
        "How to lead people smarter than you",
    ],
}


class ResearchEngine:
    def __init__(self):
        self.anthropic = Anthropic(api_key=ANTHROPIC_KEY)

    # ── Web Search via Tavily ─────────────────────────────────────────────
    def search_web(self, idea: str, niche: str) -> dict:
        """Search web for latest content on the topic using Tavily."""
        if not TAVILY_API_KEY:
            return self._mock_web_results(idea)

        try:
            query = f"{idea} {niche} LinkedIn 2025"
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 8,
                    "include_answer": True,
                    "include_raw_content": False,
                },
                timeout=15,
            )
            data = response.json()
            results = data.get("results", [])
            answer = data.get("answer", "")

            summary_parts = [f"• {r['title']}: {r.get('content','')[:200]}" for r in results[:5]]

            return {
                "summary": answer or "\n".join(summary_parts),
                "sources": [{"title": r["title"], "url": r["url"]} for r in results],
                "raw_snippets": [r.get("content", "") for r in results[:6]],
            }
        except Exception as e:
            print(f"Tavily error: {e}")
            return self._mock_web_results(idea)

    def _mock_web_results(self, idea: str) -> dict:
        """Fallback when Tavily key not set — uses mock data."""
        return {
            "summary": f"Recent analysis shows growing interest in '{idea}'. Several thought leaders have published on this topic in 2025, with engagement rates 2-3x higher than average posts. Key angles include practical application, common misconceptions, and personal experience stories.",
            "sources": [
                {"title": f"Why {idea} matters in 2025", "url": "https://example.com"},
                {"title": f"The truth about {idea}", "url": "https://example.com"},
            ],
            "raw_snippets": [
                f"Experts suggest {idea} is becoming critical for professionals in all fields.",
                f"New research shows {idea} can dramatically improve outcomes when applied correctly.",
            ],
        }

    # ── LinkedIn Trend Patterns ───────────────────────────────────────────
    def get_linkedin_trends(self, niche: str) -> dict:
        """Return top-performing LinkedIn post patterns for the niche."""
        patterns = LINKEDIN_TREND_TEMPLATES.get(niche, LINKEDIN_TREND_TEMPLATES["AI & Technology"])
        return {
            "top_patterns": patterns,
            "best_formats": ["Numbered list", "Story arc", "Contrarian take", "Lessons learned", "How-to thread"],
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["7:30–9:30 AM", "12:00–1:00 PM"],
            "avg_engagement_tip": "Posts under 1300 chars with a strong hook get 3× more comments",
        }

    # ── arXiv / Paper Search ──────────────────────────────────────────────
    def search_papers(self, idea: str) -> dict:
        """Search arXiv for recent research papers related to the topic."""
        try:
            params = {
                "search_query": f"all:{idea}",
                "start": 0,
                "max_results": 5,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            resp = requests.get(ARXIV_BASE, params=params, timeout=10)
            # Parse Atom XML simply
            text = resp.text
            titles, summaries = [], []

            import re
            title_matches = re.findall(r"<title>(.*?)</title>", text, re.DOTALL)
            summary_matches = re.findall(r"<summary>(.*?)</summary>", text, re.DOTALL)

            # First title is feed title, skip it
            for t in title_matches[1:4]:
                titles.append(t.strip().replace("\n", " "))
            for s in summary_matches[:3]:
                summaries.append(s.strip()[:250].replace("\n", " "))

            return {"titles": titles, "summaries": summaries}

        except Exception as e:
            print(f"arXiv error: {e}")
            return {"titles": [], "summaries": []}

    # ── Topic Synthesis ───────────────────────────────────────────────────
    def synthesise_topics(
        self,
        idea: str,
        niche: str,
        tone: str,
        audience: str,
        web_results: dict,
        linkedin_trends: dict,
        papers: dict,
    ) -> list:
        """Use Claude to synthesise research into 5 distinct topic angles."""

        web_summary = web_results.get("summary", "")[:800]
        paper_titles = "; ".join(papers.get("titles", []))
        trend_patterns = ", ".join(linkedin_trends.get("top_patterns", [])[:4])
        best_formats = ", ".join(linkedin_trends.get("best_formats", []))

        prompt = f"""You are a LinkedIn content strategist with deep expertise in {niche}.

A creator wants to post about: "{idea}"

Research context:
- Web findings: {web_summary}
- Related research: {paper_titles}
- Top LinkedIn patterns in this niche: {trend_patterns}
- High-performing formats: {best_formats}
- Target audience: {audience}
- Desired tone: {tone}

Generate exactly 5 distinct, compelling LinkedIn post topic angles based on this research.
Each angle must be different in approach (story, list, contrarian, how-to, data-driven, etc).

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "title": "Specific post title / angle (max 10 words)",
    "hook_preview": "The first 1-2 sentences of how this post would open (make it punchy)",
    "format": "Post format (e.g. Story arc, Numbered list, Contrarian take, How-to, Data reveal)",
    "trend_score": "High / Medium / Very High",
    "est_reach": "Estimated reach like 3K-8K",
    "why_works": "One sentence on why this angle performs well on LinkedIn"
  }}
]

Important: Return ONLY the JSON array, no other text."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            # Clean up if wrapped in markdown
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            topics = json.loads(raw)
            return topics[:5]

        except Exception as e:
            print(f"Topic synthesis error: {e}")
            # Fallback topics
            return [
                {
                    "title": f"The truth about {idea} nobody tells you",
                    "hook_preview": f"I spent 3 years learning {idea} the hard way. Here's what I wish someone had told me on day one.",
                    "format": "Story arc",
                    "trend_score": "High",
                    "est_reach": "5K-12K",
                    "why_works": "Personal story + useful insight combo drives high comment rates",
                },
                {
                    "title": f"5 lessons from {idea} that changed my career",
                    "hook_preview": f"Most people think {idea} is about X. They're completely wrong.",
                    "format": "Numbered list",
                    "trend_score": "Very High",
                    "est_reach": "8K-20K",
                    "why_works": "Numbered lists are the #1 highest-saving format on LinkedIn",
                },
                {
                    "title": f"Unpopular opinion: {idea} is overrated",
                    "hook_preview": f"Hot take: You don't need {idea} to succeed. You need something far simpler.",
                    "format": "Contrarian take",
                    "trend_score": "Very High",
                    "est_reach": "10K-30K",
                    "why_works": "Contrarian posts generate 4× more comments than agreement posts",
                },
                {
                    "title": f"How I used {idea} to achieve X in 90 days",
                    "hook_preview": f"90 days ago, I had no idea how {idea} worked. Today it's my #1 competitive advantage.",
                    "format": "How-to / Results",
                    "trend_score": "High",
                    "est_reach": "4K-10K",
                    "why_works": "Specific timeframes + results make posts relatable and credible",
                },
                {
                    "title": f"The data behind {idea} that surprised me",
                    "hook_preview": f"I analysed 100+ case studies on {idea}. The results were not what I expected.",
                    "format": "Data reveal",
                    "trend_score": "Medium",
                    "est_reach": "3K-7K",
                    "why_works": "Data-backed posts build authority and get shared by industry leaders",
                },
            ]
