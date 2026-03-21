import streamlit as st
import os
import requests
from dotenv import load_dotenv

# 1. Load your secure API keys
load_dotenv()
canvas_key = os.getenv("CANVAS_API_KEY")
llm_key = os.getenv("LLM_API_KEY")

# 2. Set up the main page and sidebar menu
st.set_page_config(page_title="Creator Studio", page_icon="🚀", layout="wide")

st.sidebar.title("🚀 Creator Studio")
app_mode = st.sidebar.radio("Select a Tool:", 
    ["✍️ LinkedIn Writer", "🎨 Image Generator", "🎬 Audio/Video Creator", "💬 AI Chatbot"]
)
st.sidebar.markdown("---")

# ==========================================
# TOOL 1: LINKEDIN CONTENT WRITER
# ==========================================
if app_mode == "✍️ LinkedIn Writer":
    st.title("✍️ LinkedIn Content Writer")
    st.write("Generate high-impact, professional posts in seconds.")
    
    topic = st.text_area("What is the core message of your post?", placeholder="e.g., How taking risks leads to career growth...")
    tone = st.selectbox("Select the Tone:", ["Professional & Insightful", "Bold & Direct", "Storytelling"])
    
    if st.button("Draft Post"):
        if topic:
            with st.spinner("Drafting your content..."):
                try:
                    api_url = "https://api.openai.com/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    prompt = f"Write a highly engaging LinkedIn post about: {topic}. Make the tone {tone}. Include a hook, body, and a question at the end to drive engagement."
                    data = {
                        "model": "gpt-4o", 
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    
                    # The API call is now active!
                    response = requests.post(api_url, headers=headers, json=data).json()
                    st.write(response['choices'][0]['message']['content'])
                    
                    st.success("Your post is ready!")
                except Exception as e:
                    st.error(f"Error connecting to AI. Please check your LLM_API_KEY in the .env file. Details: {e}")
        else:
            st.warning("Please enter a topic first.")

# ==========================================
# TOOL 2: CANVAS IMAGE GENERATOR
# ==========================================
elif app_mode == "🎨 Image Generator":
    st.title("🎨 Canvas Image Generator")
    st.write("Create custom visuals for your content.")
    
    user_prompt = st.text_input("Describe the image you want:", placeholder="A sleek modern office at golden hour...")
    
    if st.button("Generate Image"):
        if user_prompt:
            with st.spinner("Rendering your image..."):
                try:
                    api_url = "YOUR_CANVAS_API_URL_HERE" # Update with your real Canvas URL
                    headers = {"Authorization": f"Bearer {canvas_key}", "Content-Type": "application/json"}
                    data = {"prompt": user_prompt}
                    
                    # The API call is now active!
                    response = requests.post(api_url, headers=headers, json=data)
                    st.image(response.content)
                    
                    st.success("Image generated successfully!")
                except Exception as e:
                    st.error(f"Error generating image. Please check your CANVAS_API_KEY and URL. Details: {e}")
        else:
            st.warning("Please describe the image first.")

# ==========================================
# TOOL 3: AUDIO & VIDEO CREATOR
# ==========================================
elif app_mode == "🎬 Audio/Video Creator":
    st.title("🎬 Media Creator")
    st.write("Turn your text into dynamic audio or video.")
    
    media_type = st.radio("Select Output Format:", ["Video Clip", "Voiceover Audio"])
    prompt = st.text_area("Enter your script or visual description:")
    
    if st.button(f"Generate {media_type}"):
        if prompt:
            with st.spinner(f"Processing your {media_type.lower()}..."):
                st.info(f"Ready for your video/audio API integration!")
        else:
            st.warning("Please provide a prompt or script.")

# ==========================================
# TOOL 4: AI ASSISTANT CHATBOT
# ==========================================
elif app_mode == "💬 AI Chatbot":
    st.title("💬 Brainstorming Assistant")
    st.write("Your personal AI for brainstorming and strategy.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I help you build your creator studio today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            try:
                # The Chatbot API call is now active!
                api_url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                data = {
                    "model": "gpt-4o",
                    "messages": st.session_state.messages
                }
                response = requests.post(api_url, headers=headers, json=data).json()
                reply = response['choices'][0]['message']['content']
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                error_msg = f"Connection error. Please check your LLM_API_KEY. Details: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})