import streamlit as st
import os
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ===============================
# 1. Load API keys
# ===============================
load_dotenv()
llm_key = os.getenv("LLM_API_KEY")

# ===============================
# 2. Streamlit setup
# ===============================
st.set_page_config(page_title="Creator Studio", page_icon="🚀", layout="wide")
st.sidebar.title("🚀 Creator Studio")

# ===============================
# 3. Sidebar Menu
# ===============================
app_mode = st.sidebar.radio("Select a Tool:", [
    "✍️ LinkedIn Writer",
    "🎨 Image Generator",
    "🎬 Audio/Video Creator",
    "💬 AI Chatbot",
    "📅 Content Calendar",
    "📝 Document Summarizer",
    "📊 Analytics Dashboard",
    "📈 Trend Monitoring",
    "🎞️ Slide/Infographic Generator",
    "🤖 Workflow Automation"
])

# ===============================
# Helper: GPT Text
# ===============================
def generate_text(prompt, model="gpt-4o"):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=data).json()
    return response['choices'][0]['message']['content']

# ===============================
# Helper: Image Generation (NO TEXT)
# ===============================
def generate_image(prompt):
    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
    
    data = {
        "model": "dall-e-3",
        "prompt": f"{prompt}. No text, no words, no typography.",
        "n": 1,
        "size": "1024x1024"
    }
    
    response = requests.post(url, headers=headers, json=data).json()
    return response['data'][0]['url']

# ===============================
# Helper: Add Text Overlay
# ===============================
def add_text_to_image(image_url, title, subtitle=""):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content)).convert("RGB")

    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_sub = ImageFont.truetype("arial.ttf", 30)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Title
    draw.text((50, 50), title, fill="white", font=font_title)

    # Subtitle
    if subtitle:
        draw.text((50, 130), subtitle, fill="white", font=font_sub)

    return img

# ===============================
# TOOL 1: LINKEDIN WRITER
# ===============================
if app_mode == "✍️ LinkedIn Writer":
    st.title("✍️ LinkedIn Content Writer")

    topic = st.text_area("Topic")
    tone = st.selectbox("Tone", ["Professional", "Bold", "Storytelling"])

    if st.button("Generate"):
        post = generate_text(f"Write a LinkedIn post about {topic} in {tone} tone")
        st.markdown(post)

# ===============================
# TOOL 2: IMAGE GENERATOR (FIXED)
# ===============================
elif app_mode == "🎨 Image Generator":
    st.title("🎨 AI Image Generator (Fixed Text Issue)")

    prompt = st.text_input("Image description")
    add_text = st.checkbox("Add text overlay")

    if add_text:
        title = st.text_input("Title text")
        subtitle = st.text_input("Subtitle (optional)")

    if st.button("Generate Image"):
        if prompt:
            with st.spinner("Generating..."):
                image_url = generate_image(prompt)

                if add_text and title:
                    final_img = add_text_to_image(image_url, title, subtitle)
                    st.image(final_img)
                else:
                    st.image(image_url)

# ===============================
# TOOL 3: CHATBOT
# ===============================
elif app_mode == "💬 AI Chatbot":
    st.title("💬 Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    if prompt := st.chat_input("Ask something"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        reply = generate_text(prompt)
        st.chat_message("assistant").markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ===============================
# TOOL 4: CONTENT CALENDAR
# ===============================
elif app_mode == "📅 Content Calendar":
    st.title("📅 Content Calendar")

    dates = st.date_input("Select dates", [])
    ideas = st.text_area("Ideas (one per line)")

    if st.button("Generate"):
        ideas_list = ideas.splitlines()
        for i, d in enumerate(dates):
            st.write(f"{d} → {ideas_list[i % len(ideas_list)]}")

# ===============================
# TOOL 5: SUMMARIZER
# ===============================
elif app_mode == "📝 Document Summarizer":
    st.title("📝 Summarizer")

    text = st.text_area("Paste text")

    if st.button("Summarize"):
        st.markdown(generate_text(f"Summarize:\n{text}"))

# ===============================
# TOOL 6: ANALYTICS
# ===============================
elif app_mode == "📊 Analytics Dashboard":
    st.title("📊 Analytics")

    st.table({
        "Post": ["Post1", "Post2"],
        "Likes": [100, 200],
        "Comments": [10, 20]
    })

# ===============================
# TOOL 7: TRENDS
# ===============================
elif app_mode == "📈 Trend Monitoring":
    st.title("📈 Trends")

    topic = st.text_input("Topic")

    if st.button("Check"):
        st.markdown(generate_text(f"Trending topics in {topic}"))

# ===============================
# TOOL 8: SLIDES
# ===============================
elif app_mode == "🎞️ Slide Generator":
    st.title("🎞️ Slides")

    content = st.text_area("Content")

    if st.button("Generate"):
        st.markdown(generate_text(f"Convert into slides:\n{content}"))

# ===============================
# TOOL 9: WORKFLOW
# ===============================
elif app_mode == "🤖 Workflow Automation":
    st.title("🤖 Workflow")

    actions = st.multiselect("Actions", [
        "Post", "Image", "Summary"
    ])

    if st.button("Run"):
        if "Post" in actions:
            st.markdown(generate_text("Write LinkedIn post about AI"))

        if "Image" in actions:
            img = generate_image("AI future city")
            st.image(img)

        if "Summary" in actions:
            st.markdown(generate_text("Summarize AI trends"))