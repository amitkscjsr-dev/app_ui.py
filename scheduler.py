"""
Automation Module — Phase 1
Handles: Make.com webhook dispatch, LinkedIn API posting, best-time scheduling
"""

import os
import json
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

MAKE_WEBHOOK_URL      = os.getenv("MAKE_WEBHOOK_URL", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN   = os.getenv("LINKEDIN_PERSON_URN", "")   # urn:li:person:XXXXXX
TELEGRAM_BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID", "")


# ─── Best Time Algorithm ─────────────────────────────────────────────────────
# Based on LinkedIn algorithm research for Indian + Global audiences
BEST_TIMES_IST = {
    "Monday":    ["08:00", "12:00"],
    "Tuesday":   ["07:30", "09:00", "12:00"],  # Best day
    "Wednesday": ["08:00", "09:00", "17:00"],  # Best day
    "Thursday":  ["08:00", "12:00", "17:30"],  # Best day
    "Friday":    ["08:00", "11:00"],
    "Saturday":  [],                            # Avoid
    "Sunday":    [],                            # Avoid
}

NICHE_BOOST_TIMES = {
    "AI & Technology":       ["08:00", "09:00"],
    "Entrepreneurship":      ["07:30", "08:30"],
    "Marketing & Growth":    ["09:00", "12:00"],
    "Finance & Investing":   ["08:00", "17:00"],
    "Leadership":            ["07:00", "12:00"],
}


def get_next_best_slot(niche: str = "AI & Technology") -> dict:
    """Calculate the next optimal LinkedIn posting slot."""
    now  = datetime.datetime.now()
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    # Look ahead up to 7 days
    for days_ahead in range(0, 8):
        candidate = now + datetime.timedelta(days=days_ahead)
        day_name  = days[candidate.weekday()]
        slots     = BEST_TIMES_IST.get(day_name, [])

        if not slots:
            continue

        for slot_time in slots:
            h, m = map(int, slot_time.split(":"))
            slot_dt = candidate.replace(hour=h, minute=m, second=0, microsecond=0)

            # Must be at least 30 minutes in the future
            if slot_dt > now + datetime.timedelta(minutes=30):
                return {
                    "datetime":     slot_dt.isoformat(),
                    "day":          day_name,
                    "time":         slot_time,
                    "days_from_now": days_ahead,
                    "human_label":  f"{day_name} at {slot_time} IST" + (" (tomorrow)" if days_ahead == 1 else f" (+{days_ahead}d)" if days_ahead > 1 else " (today)"),
                }

    # Fallback: next Tuesday 8am
    days_until_tuesday = (1 - now.weekday()) % 7 or 7
    next_tue = now + datetime.timedelta(days=days_until_tuesday)
    next_tue = next_tue.replace(hour=8, minute=0, second=0, microsecond=0)
    return {
        "datetime":     next_tue.isoformat(),
        "day":          "Tuesday",
        "time":         "08:00",
        "days_from_now": days_until_tuesday,
        "human_label":  f"Tuesday at 08:00 IST (+{days_until_tuesday}d)",
    }


# ─── LinkedIn API ─────────────────────────────────────────────────────────────
class LinkedInPublisher:

    def post_text_only(self, content: str) -> dict:
        """Post a text-only LinkedIn post."""
        if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
            return {"success": False, "error": "LinkedIn credentials not configured", "demo": True}

        url     = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization":  f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type":   "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        payload = {
            "author":          LINKEDIN_PERSON_URN,
            "lifecycleState":  "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            if resp.status_code in [200, 201]:
                post_id = resp.headers.get("x-restli-id", "unknown")
                return {"success": True, "post_id": post_id, "url": f"https://www.linkedin.com/feed/update/{post_id}/"}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post_with_image(self, content: str, image_url: str) -> dict:
        """
        Post to LinkedIn with an image.
        Requires: register upload → upload image → create post.
        """
        if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
            return {"success": False, "error": "LinkedIn credentials not configured", "demo": True}

        headers = {
            "Authorization":  f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type":   "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # Step 1: Register upload
        try:
            reg_payload = {
                "registerUploadRequest": {
                    "recipes":           ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner":             LINKEDIN_PERSON_URN,
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier":       "urn:li:userGeneratedContent",
                    }],
                }
            }
            reg_resp = requests.post(
                "https://api.linkedin.com/v2/assets?action=registerUpload",
                headers=headers, json=reg_payload, timeout=15,
            )
            reg_data    = reg_resp.json()
            upload_url  = reg_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_urn   = reg_data["value"]["asset"]

            # Step 2: Download image and upload
            img_bytes = requests.get(image_url, timeout=20).content
            upload_headers = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type":  "application/octet-stream",
            }
            requests.put(upload_url, headers=upload_headers, data=img_bytes, timeout=30)

            # Step 3: Create post with image
            post_payload = {
                "author":          LINKEDIN_PERSON_URN,
                "lifecycleState":  "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary":   {"text": content},
                        "shareMediaCategory": "IMAGE",
                        "media": [{
                            "status":      "READY",
                            "description": {"text": "Post image"},
                            "media":       asset_urn,
                            "title":       {"text": ""},
                        }],
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                },
            }
            post_resp = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers, json=post_payload, timeout=15,
            )
            if post_resp.status_code in [200, 201]:
                post_id = post_resp.headers.get("x-restli-id", "unknown")
                return {"success": True, "post_id": post_id, "url": f"https://www.linkedin.com/feed/update/{post_id}/"}
            return {"success": False, "error": post_resp.text}

        except Exception as e:
            return {"success": False, "error": str(e)}


# ─── Make.com Webhook ─────────────────────────────────────────────────────────
def trigger_make_webhook(payload: dict) -> dict:
    """
    Send post data to Make.com webhook for scheduled publishing.
    Make.com scenario handles: wait for best time → post → log → notify.
    """
    if not MAKE_WEBHOOK_URL:
        print("Make.com webhook URL not set — simulating trigger")
        return {"success": True, "demo": True, "message": "Demo mode — set MAKE_WEBHOOK_URL in .env"}

    try:
        resp = requests.post(
            MAKE_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return {"success": resp.status_code == 200, "status_code": resp.status_code, "response": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def schedule_post(
    post_content: str,
    image_url: str | None,
    topic_title: str,
    niche: str,
    publish_mode: str = "auto",
    scheduled_datetime: str | None = None,
) -> dict:
    """
    Main scheduling function.
    Determines best time (or uses specified) and sends to Make.com.
    """
    if publish_mode == "auto":
        slot = get_next_best_slot(niche)
        publish_at = slot["datetime"]
        slot_label = slot["human_label"]
    elif publish_mode == "immediate":
        publish_at = datetime.datetime.now().isoformat()
        slot_label = "Immediately"
    else:
        publish_at = scheduled_datetime or datetime.datetime.now().isoformat()
        slot_label = f"Scheduled: {publish_at}"

    webhook_payload = {
        "post_content":  post_content,
        "image_url":     image_url,
        "topic_title":   topic_title,
        "niche":         niche,
        "publish_at":    publish_at,
        "slot_label":    slot_label,
        "notify":        True,
        "log_to_sheets": True,
        "timestamp":     datetime.datetime.now().isoformat(),
    }

    result = trigger_make_webhook(webhook_payload)
    result["slot_label"]  = slot_label
    result["publish_at"]  = publish_at
    return result


# ─── Telegram Notifications ───────────────────────────────────────────────────
def send_telegram_notification(message: str) -> bool:
    """Send a Telegram message to notify about post status."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"Telegram not configured — would send: {message}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       message,
            "parse_mode": "HTML",
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False
