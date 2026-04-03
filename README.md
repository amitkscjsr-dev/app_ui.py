# ═══════════════════════════════════════════════════════════════════════
# AI CONTENT OS — PHASE 1 SETUP GUIDE
# ═══════════════════════════════════════════════════════════════════════

## What's built in Phase 1

```
ai_productivity_os/
├── app.py                    ← Streamlit main app (6 steps)
├── modules/
│   ├── research.py           ← Tavily + arXiv + trend synthesis
│   ├── post_creator.py       ← Claude + GPT-4o A/B post writer
│   └── image_creator.py      ← DALL·E 3 LinkedIn image generator
├── automation/
│   └── scheduler.py          ← Make.com + LinkedIn API + Telegram
├── .env.example              ← Copy to .env and fill keys
└── requirements.txt          ← All dependencies
```

---

## ⚡ Quick Start (15 minutes)

### 1. Create project folder & virtual environment
```bash
mkdir ai-content-os && cd ai-content-os
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Copy all files into the folder, then install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your .env file
```bash
cp .env.example .env
# Open .env in VS Code and add your API keys
```

**Minimum keys needed to run Phase 1:**
- `ANTHROPIC_API_KEY` — get from console.anthropic.com
- `OPENAI_API_KEY` — get from platform.openai.com
- `TAVILY_API_KEY` — get from tavily.com (free tier = 1000 searches/month)

> ⚠️ If you skip keys, the app runs in **demo mode** with mock data — still fully usable for testing.

### 4. Create the modules folder structure
```bash
mkdir -p modules automation
touch modules/__init__.py automation/__init__.py
```

### 5. Run the app
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser. That's it!

---

## 🔑 API Keys — Where to Get Them

| Key | Where | Cost |
|-----|-------|------|
| ANTHROPIC_API_KEY | console.anthropic.com | ~$0.003/post |
| OPENAI_API_KEY | platform.openai.com | ~$0.005/post + $0.04/image |
| TAVILY_API_KEY | tavily.com | Free: 1000/month |
| LINKEDIN_ACCESS_TOKEN | linkedin.com/developers | Free |
| MAKE_WEBHOOK_URL | make.com | Free: 1000 ops/month |
| TELEGRAM_BOT_TOKEN | @BotFather on Telegram | Free |

**Estimated Phase 1 cost per post:** ~$0.05-0.10 USD (text + image)

---

## 📋 Make.com Scenario Setup (Phase 2)

Create this automation flow in Make.com:

```
1. Webhook (Custom) — receives post data from app
2. Sleep module — wait until scheduled datetime
3. LinkedIn → Create a Post — posts the content
4. Google Sheets → Add Row — logs the post
5. Telegram → Send Message — notifies you
```

Import the webhook URL into your .env as `MAKE_WEBHOOK_URL`.

---

## 🔐 LinkedIn API Setup

1. Go to linkedin.com/developers → Create App
2. Add products: **Share on LinkedIn** + **Sign In with LinkedIn**
3. Request `w_member_social` permission
4. Generate Access Token (valid 60 days — use refresh token for production)
5. Call `/v2/me` to get your Person URN → add to .env

---

## 📅 Best Posting Times (Pre-configured)

The scheduler algorithm targets these slots automatically:

| Day | Best Times (IST) | Why |
|-----|-----------------|-----|
| Tuesday | 7:30 AM, 9:00 AM, 12:00 PM | Highest engagement day globally |
| Wednesday | 8:00 AM, 5:00 PM | Decision-makers most active |
| Thursday | 8:00 AM, 12:00 PM | Strong reach day |
| Friday | 8:00 AM only | Drops off after noon |
| Weekend | Avoid | <40% weekday engagement |

---

## 🗺️ Roadmap

| Phase | Features | Status |
|-------|----------|--------|
| 1 | Post creator + A/B testing + Image + Streamlit UI | ✅ Built |
| 2 | LinkedIn auto-post + Make.com + Scheduler + Telegram | 🔜 Next |
| 3 | Audio (ElevenLabs) + Video (HeyGen) + Carousel + PPT | 📋 Planned |
| 4 | Profile Builder + Astro module + Analytics dashboard | 📋 Planned |

---

## 💡 Pro Tips

- **Run without API keys first** — demo mode shows you the full UI flow
- **A/B test rule of thumb** — Claude tends to be more nuanced; GPT-4o is punchier
- **Best image style for tech/AI niche** → "Bold & Typographic" or "Futuristic & Tech"
- **Character sweet spot** → 1200-1800 chars (the app shows this in real time)
- **Never post on Saturday or Sunday** — the scheduler automatically skips these
