"""
publish_tab.py
───────────────
A self-contained Streamlit publish component.

HOW TO ADD TO YOUR EXISTING app.py
────────────────────────────────────
Option A — Replace your final step with this:
    from publish_tab import render_publish_tab
    render_publish_tab(
        post_content=st.session_state.final_post,
        image_url=st.session_state.get("generated_image_url"),
        topic=st.session_state.selected_topic.get("title", ""),
        niche=st.session_state.niche,
    )

Option B — Add as a sidebar button at any point:
    if st.sidebar.button("Schedule & Publish"):
        st.session_state.show_publish = True
    if st.session_state.get("show_publish"):
        render_publish_tab(...)
"""

import datetime
import streamlit as st
from zoneinfo import ZoneInfo

# Import from make_integration.py (same folder)
from make_integration import (
    schedule_and_dispatch,
    get_next_best_slot,
    get_all_upcoming_slots,
    check_token_expiry,          # from linkedin_auth.py
)

IST = ZoneInfo("Asia/Kolkata")


def _token_status_badge():
    """Show LinkedIn token health at the top of the publish panel."""
    try:
        from linkedin_auth import check_token_expiry
        status = check_token_expiry()
    except Exception:
        status = {"status": "unknown", "days_left": None}

    s = status["status"]
    days = status.get("days_left")

    if s == "ok":
        st.success(f"LinkedIn token valid · {days} days remaining", icon="✅")
    elif s == "expiring_soon":
        st.warning(f"Token expires in {days} days — run `python linkedin_auth.py` to refresh", icon="⚠️")
    elif s == "expired":
        st.error("LinkedIn token expired — run `python linkedin_auth.py` to refresh", icon="🔴")
    else:
        st.info("LinkedIn token status unknown — run `python linkedin_auth.py` if you haven't", icon="ℹ️")


def _scheduling_calendar(niche: str):
    """Show the next 7 days of best posting slots."""
    slots = get_all_upcoming_slots(days=7, niche=niche)[:8]

    st.markdown("**Best slots for your niche (next 7 days)**")
    rows = []
    for s in slots:
        score_bar = "▓" * s["score"] + "░" * (11 - s["score"])
        rows.append({
            "Day & Time":    s["label"],
            "Engagement":    score_bar,
            "Score":         f"{s['score']}/11",
        })

    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)


def render_publish_tab(
    post_content: str,
    image_url:    str | None,
    topic:        str,
    niche:        str,
):
    """
    Renders the complete publish UI.
    Call this wherever you want the scheduling step in your app.
    """
    st.markdown("## Schedule & Publish")
    st.markdown("---")

    # ── Token health ──────────────────────────────────────────────────────
    _token_status_badge()
    st.markdown("")

    # ── Post preview (compact) ────────────────────────────────────────────
    with st.expander("Review post before publishing", expanded=True):
        col_post, col_img = st.columns([2, 1])
        with col_post:
            edited = st.text_area(
                "Post content",
                value=post_content,
                height=260,
                key="publish_final_edit",
            )
            char_count = len(edited)
            colour = "green" if char_count <= 3000 else "red"
            st.markdown(
                f'<span style="color:{colour};font-size:12px">{char_count}/3000 characters</span>',
                unsafe_allow_html=True,
            )
        with col_img:
            if image_url:
                st.image(image_url, caption="Attached image", use_container_width=True)
            else:
                st.info("No image attached")

    # ── Scheduling options ────────────────────────────────────────────────
    st.markdown("### When to publish?")

    mode_choice = st.radio(
        "Publish mode",
        ["Auto (best time)", "Schedule specific time", "Post right now"],
        horizontal=True,
        label_visibility="collapsed",
    )

    publish_at_override = None
    slot_label          = ""
    mode_key            = "auto"

    if mode_choice == "Auto (best time)":
        mode_key = "auto"
        slot     = get_next_best_slot(niche)
        slot_label = slot["human_label"]

        st.markdown(
            f'<div style="background:#f0faf4;border:1px solid #a3d9b1;border-radius:8px;'
            f'padding:12px 18px;margin:8px 0;">'
            f'<span style="font-size:13px;color:#1a7a3c">Next best slot: <b>{slot_label}</b> '
            f'&nbsp;·&nbsp; Engagement score: {slot["score"]}/11</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("See all upcoming slots"):
            _scheduling_calendar(niche)

    elif mode_choice == "Schedule specific time":
        mode_key = "scheduled"
        col_d, col_t = st.columns(2)
        with col_d:
            pub_date = st.date_input(
                "Date",
                min_value=datetime.date.today(),
                value=datetime.date.today() + datetime.timedelta(days=1),
                key="publish_date",
            )
        with col_t:
            pub_time = st.time_input(
                "Time (IST)",
                value=datetime.time(8, 0),
                key="publish_time",
            )
        combined          = datetime.datetime.combine(pub_date, pub_time, tzinfo=IST)
        publish_at_override = combined.isoformat()
        slot_label          = combined.strftime("%A %d %b %Y, %I:%M %p IST")

    else:
        mode_key   = "immediate"
        slot_label = "Right now"
        st.warning("Posting immediately — Make.com scheduler will be bypassed", icon="⚡")

    # ── Notification settings ─────────────────────────────────────────────
    st.markdown("### Notifications")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        notify_telegram = st.checkbox("Telegram notification", value=True)
    with col_n2:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        has_telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
        if not has_telegram:
            st.caption("Add TELEGRAM_BOT_TOKEN to .env to enable")

    # ── Publish button ────────────────────────────────────────────────────
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])

    with col_btn1:
        publish_label = {
            "auto":      f"Schedule for {slot_label}",
            "scheduled": f"Schedule for {slot_label}",
            "immediate": "Post to LinkedIn now",
        }.get(mode_key, "Publish")

        if st.button(f"🚀 {publish_label}", type="primary", use_container_width=True):
            _do_publish(
                post_content=edited,
                image_url=image_url,
                topic=topic,
                niche=niche,
                mode=mode_key,
                scheduled_at=publish_at_override,
                slot_label=slot_label,
            )

    with col_btn2:
        if st.button("Copy post text", use_container_width=True):
            st.code(edited, language=None)

    with col_btn3:
        if st.button("Start over", use_container_width=True):
            # Clear your session state keys as needed
            for key in ["final_post", "post_a", "post_b", "selected_topic",
                        "research_results", "topic_suggestions", "generated_image_url"]:
                st.session_state.pop(key, None)
            st.session_state["step"] = 1
            st.rerun()


def _do_publish(
    post_content: str,
    image_url:    str | None,
    topic:        str,
    niche:        str,
    mode:         str,
    scheduled_at: str | None,
    slot_label:   str,
):
    """Execute the publish and show result."""
    with st.spinner("Dispatching to Make.com..." if mode != "immediate" else "Posting to LinkedIn..."):
        result = schedule_and_dispatch(
            post_content=post_content,
            image_url=image_url,
            topic=topic,
            niche=niche,
            mode=mode,
            scheduled_at=scheduled_at,
        )

    if result["success"]:
        st.balloons()

        if mode == "immediate":
            post_url = result.get("raw", {}).get("url", "")
            st.success("Your post is live on LinkedIn!", icon="🎉")
            if post_url:
                st.markdown(f"[View your post →]({post_url})")
        else:
            st.success(
                f"Scheduled! Make.com will post on **{slot_label}**",
                icon="✅",
            )

        # What happens next
        method = result.get("method", "")
        if "make" in method:
            st.markdown("""
**What happens next:**
1. Make.com scenario received your post + image
2. Sleep module waits until the optimal time
3. LinkedIn module publishes the post automatically
4. Google Sheets logs the post URL + timestamp
5. Telegram sends you a "post is live" notification
            """)

        if result.get("telegram_sent"):
            st.info("Telegram notification sent", icon="📱")
        elif result.get("raw", {}).get("demo"):
            st.warning(
                "Demo mode — add MAKE_WEBHOOK_URL to .env to enable real scheduling",
                icon="⚠️",
            )

        # Log to session state for analytics
        if "post_history" not in st.session_state:
            st.session_state.post_history = []
        st.session_state.post_history.append({
            "topic":      topic,
            "scheduled":  slot_label,
            "method":     method,
            "timestamp":  datetime.datetime.now(tz=IST).isoformat(),
            "post_url":   result.get("raw", {}).get("url", ""),
        })

    else:
        error = result.get("raw", {}).get("error", "Unknown error")
        st.error(f"Publishing failed: {error}", icon="❌")

        # Helpful error hints
        if "MAKE_WEBHOOK_URL" in error:
            st.info("Set MAKE_WEBHOOK_URL in .env — see the Make.com setup guide below")
        elif "access_token" in error.lower() or "401" in str(error):
            st.info("Run `python linkedin_auth.py` to refresh your LinkedIn token")
        elif "403" in str(error):
            st.info("Check that your LinkedIn app has the `w_member_social` permission")
