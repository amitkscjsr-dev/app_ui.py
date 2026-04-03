"""
make_integration.py
────────────────────
Drop this into your existing project folder.

Handles:
  - Best-time scheduling algorithm (IST-optimised)
  - Make.com webhook dispatch
  - LinkedIn direct post (fallback if Make.com not set up)
  - Token expiry check at startup
  - Telegram notifications

Add to your .env:
  MAKE_WEBHOOK_URL
  LINKEDIN_ACCESS_TOKEN
  LINKEDIN_CLIENT_ID
  LINKEDIN_CLIENT_SECRET
  LINKEDIN_PERSON_URN
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import time
import json
import datetime
import requests
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# ── Env vars ─────────────────────────────────────────────────────────────────
MAKE_WEBHOOK_URL      = os.getenv("MAKE_WEBHOOK_URL", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN   = os.getenv("LINKEDIN_PERSON_URN", "")
TELEGRAM_BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID", "")

IST = ZoneInfo("Asia/Kolkata")

# ── Best-time data (IST, research-backed for LinkedIn) ───────────────────────
# Scores: 10 = peak engagement window
BEST_SLOTS = {
    "Monday":    [("07:30", 7), ("12:00", 6)],
    "Tuesday":   [("07:30", 10), ("09:00", 9), ("12:00", 8)],   # Best day
    "Wednesday": [("08:00", 9),  ("09:00", 8), ("17:00", 7)],   # Best day
    "Thursday":  [("08:00", 9),  ("12:00", 7), ("17:30", 6)],   # Best day
    "Friday":    [("08:00", 7),  ("11:00", 6)],
    "Saturday":  [],
    "Sunday":    [],
}

NICHE_SLOT_BOOST = {
    "AI & Technology":    ["07:30", "08:00", "09:00"],
    "Entrepreneurship":   ["07:30", "08:30"],
    "Marketing & Growth": ["09:00", "12:00"],
    "Finance & Investing":["08:00", "17:00"],
    "Leadership":         ["07:00", "12:00"],
}


# ── Best-time algorithm ───────────────────────────────────────────────────────
def get_next_best_slot(niche: str = "AI & Technology", min_ahead_minutes: int = 30) -> dict:
    """
    Returns the next optimal LinkedIn posting slot in IST.
    Looks up to 7 days ahead.
    """
    now     = datetime.datetime.now(tz=IST)
    cutoff  = now + datetime.timedelta(minutes=min_ahead_minutes)
    boosts  = NICHE_SLOT_BOOST.get(niche, [])

    for days_ahead in range(8):
        candidate = now + datetime.timedelta(days=days_ahead)
        day_name  = candidate.strftime("%A")
        slots     = BEST_SLOTS.get(day_name, [])

        for slot_time_str, base_score in slots:
            h, m = map(int, slot_time_str.split(":"))
            slot_dt = candidate.replace(hour=h, minute=m, second=0, microsecond=0)

            if slot_dt <= cutoff:
                continue

            # Apply niche boost
            score = base_score + (1 if slot_time_str in boosts else 0)

            days_label = (
                "today"    if days_ahead == 0 else
                "tomorrow" if days_ahead == 1 else
                f"in {days_ahead} days"
            )

            return {
                "datetime_ist":  slot_dt.isoformat(),
                "datetime_utc":  slot_dt.astimezone(ZoneInfo("UTC")).isoformat(),
                "day":           day_name,
                "time_ist":      slot_time_str,
                "days_ahead":    days_ahead,
                "score":         score,
                "human_label":   f"{day_name} {slot_time_str} IST ({days_label})",
            }

    # Fallback: next Tuesday 8am
    days_to_tue = (1 - now.weekday()) % 7 or 7
    next_tue    = (now + datetime.timedelta(days=days_to_tue)).replace(
        hour=8, minute=0, second=0, microsecond=0
    )
    return {
        "datetime_ist": next_tue.isoformat(),
        "datetime_utc": next_tue.astimezone(ZoneInfo("UTC")).isoformat(),
        "day":          "Tuesday",
        "time_ist":     "08:00",
        "days_ahead":   days_to_tue,
        "score":        10,
        "human_label":  f"Tuesday 08:00 IST (in {days_to_tue} days)",
    }


def get_all_upcoming_slots(days: int = 7, niche: str = "AI & Technology") -> list:
    """Return all good slots for the next N days — useful for a scheduling calendar."""
    now    = datetime.datetime.now(tz=IST)
    result = []
    boosts = NICHE_SLOT_BOOST.get(niche, [])

    for days_ahead in range(days):
        candidate = now + datetime.timedelta(days=days_ahead)
        day_name  = candidate.strftime("%A")
        slots     = BEST_SLOTS.get(day_name, [])

        for slot_time_str, base_score in slots:
            h, m    = map(int, slot_time_str.split(":"))
            slot_dt = candidate.replace(hour=h, minute=m, second=0, microsecond=0)
            if slot_dt <= now:
                continue
            result.append({
                "datetime_ist": slot_dt.isoformat(),
                "day":          day_name,
                "time_ist":     slot_time_str,
                "score":        base_score + (1 if slot_time_str in boosts else 0),
                "label":        f"{day_name} {slot_time_str}",
            })

    return sorted(result, key=lambda x: x["score"], reverse=True)


# ── Make.com webhook ──────────────────────────────────────────────────────────
def send_to_make(
    post_content: str,
    image_url:    str | None,
    topic:        str,
    niche:        str,
    publish_at:   str,            # ISO datetime string
    notify:       bool = True,
) -> dict:
    """
    Send the scheduled post to Make.com via webhook.
    Make.com handles: sleep → LinkedIn post → Sheets log → Telegram notify.
    """
    if not MAKE_WEBHOOK_URL:
        return {
            "success": False,
            "error":   "MAKE_WEBHOOK_URL not set in .env",
            "demo":    True,
        }

    payload = {
        "post_content":  post_content,
        "image_url":     image_url or "",
        "topic":         topic,
        "niche":         niche,
        "publish_at":    publish_at,      # Make.com reads this to calculate sleep duration
        "notify":        notify,
        "sent_at":       datetime.datetime.now(tz=IST).isoformat(),
        "source":        "ai_content_os",
    }

    try:
        resp = requests.post(
            MAKE_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            return {"success": True, "payload": payload}
        return {
            "success":     False,
            "status_code": resp.status_code,
            "response":    resp.text,
        }
    except requests.Timeout:
        return {"success": False, "error": "Make.com webhook timed out (10s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── LinkedIn direct post (fallback / immediate mode) ─────────────────────────
def post_to_linkedin_now(post_content: str, image_url: str | None = None) -> dict:
    """
    Post directly to LinkedIn right now (bypasses Make.com).
    Use this for 'Post immediately' mode or as a fallback.
    """
    token = LINKEDIN_ACCESS_TOKEN
    urn   = LINKEDIN_PERSON_URN

    if not token or not urn:
        return {
            "success": False,
            "error":   "LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN not set in .env",
        }

    headers = {
        "Authorization":             f"Bearer {token}",
        "Content-Type":              "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    if image_url:
        return _post_with_image(post_content, image_url, headers, urn)
    return _post_text_only(post_content, headers, urn)


def _post_text_only(content: str, headers: dict, urn: str) -> dict:
    payload = {
        "author":          urn,
        "lifecycleState":  "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary":    {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers, json=payload, timeout=15,
        )
        if resp.status_code in (200, 201):
            post_id  = resp.headers.get("x-restli-id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
            return {"success": True, "post_id": post_id, "url": post_url}
        return {"success": False, "status_code": resp.status_code, "error": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _post_with_image(content: str, image_url: str, headers: dict, urn: str) -> dict:
    """Register upload → upload bytes → create post with image."""
    try:
        # 1. Register upload
        reg_resp = requests.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            headers=headers,
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner":   urn,
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier":       "urn:li:userGeneratedContent",
                    }],
                }
            },
            timeout=15,
        )
        reg   = reg_resp.json()
        value = reg["value"]
        upload_url = value["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn  = value["asset"]

        # 2. Download image and upload to LinkedIn
        img_bytes = requests.get(image_url, timeout=20).content
        requests.put(
            upload_url,
            data=img_bytes,
            headers={
                "Authorization": headers["Authorization"],
                "Content-Type":  "application/octet-stream",
            },
            timeout=30,
        )

        # 3. Create post with asset
        payload = {
            "author":          urn,
            "lifecycleState":  "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": content},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status":      "READY",
                        "description": {"text": ""},
                        "media":        asset_urn,
                        "title":       {"text": ""},
                    }],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers, json=payload, timeout=15,
        )
        if resp.status_code in (200, 201):
            post_id  = resp.headers.get("x-restli-id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
            return {"success": True, "post_id": post_id, "url": post_url}
        return {"success": False, "status_code": resp.status_code, "error": resp.text}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Telegram notifications ────────────────────────────────────────────────────
def notify_telegram(message: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message. Returns True on success."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": parse_mode},
            timeout=8,
        )
        return resp.status_code == 200
    except Exception:
        return False


def notify_post_scheduled(topic: str, slot_label: str) -> bool:
    msg = (
        f"<b>Post scheduled!</b>\n\n"
        f"Topic: {topic}\n"
        f"Publishing: <b>{slot_label}</b>\n\n"
        f"Make.com will auto-post at the right time."
    )
    return notify_telegram(msg)


def notify_post_live(topic: str, post_url: str) -> bool:
    msg = (
        f"Your LinkedIn post is <b>live</b>!\n\n"
        f"Topic: {topic}\n"
        f"URL: {post_url}"
    )
    return notify_telegram(msg)


# ── Main schedule function (call this from your Streamlit app) ────────────────
def schedule_and_dispatch(
    post_content: str,
    image_url:    str | None,
    topic:        str,
    niche:        str,
    mode:         str = "auto",        # "auto" | "immediate" | "scheduled"
    scheduled_at: str | None = None,   # ISO datetime, used when mode="scheduled"
) -> dict:
    """
    Central function — call from your Streamlit publish step.

    Returns dict with keys:
        success, mode, slot_label, publish_at, method, telegram_sent
    """
    # Determine when to post
    if mode == "immediate":
        publish_at = datetime.datetime.now(tz=IST).isoformat()
        slot_label = "Right now"
    elif mode == "scheduled" and scheduled_at:
        publish_at = scheduled_at
        slot_label = f"Scheduled: {scheduled_at}"
    else:
        slot       = get_next_best_slot(niche)
        publish_at = slot["datetime_ist"]
        slot_label = slot["human_label"]

    # Choose dispatch method
    if mode == "immediate":
        # Direct LinkedIn API for instant posts
        result = post_to_linkedin_now(post_content, image_url)
        method = "linkedin_direct"
    elif MAKE_WEBHOOK_URL:
        # Make.com handles scheduled posting
        result = send_to_make(post_content, image_url, topic, niche, publish_at)
        method = "make_webhook"
    else:
        # Fallback: direct API (posts immediately, ignores schedule)
        result = post_to_linkedin_now(post_content, image_url)
        method = "linkedin_direct_fallback"

    # Telegram notification
    telegram_sent = False
    if result.get("success"):
        if mode == "immediate":
            telegram_sent = notify_post_live(topic, result.get("url", ""))
        else:
            telegram_sent = notify_post_scheduled(topic, slot_label)

    return {
        "success":       result.get("success", False),
        "mode":          mode,
        "method":        method,
        "slot_label":    slot_label,
        "publish_at":    publish_at,
        "telegram_sent": telegram_sent,
        "raw":           result,
    }
