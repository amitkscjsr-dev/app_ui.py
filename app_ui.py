import streamlit as st
import os
import requests
from dotenv import load_dotenv

# 1. Load your secure API keys
load_dotenv()
# We use llm_key for LinkedIn, Images (DALL-E), and Chatbot
llm_key = os.getenv("LLM_API_KEY")

# 2. Set up the main page and sidebar menu
st.set_page_config(page_title="Creator Studio", page_icon="🚀", layout="wide")

st.sidebar.title("🚀 Creator Studio")
app_mode = st.sidebar.radio("Select a Tool:", 
    ["✍️ LinkedIn Writer", "🎨 Image Generator", "🎬 Audio/Video Creator", "💬 AI Chatbot"]
)
st.sidebar.markdown("---")
st.sidebar.info("Ensure LLM_API_KEY is added to Streamlit Secrets.")

# ==========================================
# TOOL 1: LINKEDIN CONTENT WRITER
# ==========================================
if app_mode == "✍️ LinkedIn Writer":
    st.title("✍️ LinkedIn Content Writer")
    st.write("Generate high-impact, professional posts.")
    
    topic = st.text_area("What is your post about?", placeholder="e.g., Leadership in the banking sector...")
    tone = st.selectbox("Select Tone:", ["Professional", "Bold", "Storytelling"])
    
    if st.button("Draft Post"):
        if topic:
            with st.spinner("Drafting..."):
                try:
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    data = {
                        "model": "gpt-4o", 
                        "messages": [{"role": "user", "content": f"Write a LinkedIn post about {topic} in a {tone} tone."}]
                    }
                    response = requests.post(url, headers=headers, json=data).json()
                    
                    if "choices" in response:
                        st.write(response['choices'][0]['message']['content'])
                        st.success("Post generated!")
                    else:
                        st.error(f"Error: {response.get('error', {}).get('message', 'Check your API key.')}")
                except Exception as e:
                    st.error(f"System Error: {e}")
        else:
            st.warning("Please enter a topic.")

# ==========================================
# TOOL 2: IMAGE GENERATOR (OpenAI DALL-E)
# ==========================================
elif app_mode == "🎨 Image Generator":
    st.title("🎨 AI Image Generator")
    st.write("Create visuals for your LinkedIn posts.")
    
    user_prompt = st.text_input("Describe the image:", placeholder="A vintage car in a futuristic city...")
    
    if st.button("Generate Image"):
        if user_prompt:
            with st.spinner("Generating image..."):
                try:
                    url = "https://api.openai.com/v1/images/generations"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    data = {"model": "dall-e-3", "prompt": user_prompt, "n": 1, "size": "1024x1024"}
                    
                    response = requests.post(url, headers=headers, json=data).json()
                    
                    if "data" in response:
                        image_url = response['data'][0]['url']
                        st.image(image_url, caption=user_prompt)
                        st.success("Image generated successfully!")
                    else:
                        st.error(f"Error: {response.get('error', {}).get('message', 'Check your API key.')}")
                except Exception as e:
                    st.error(f"System Error: {e}")
        else:
            st.warning("Please enter a description.")

# ==========================================
# TOOL 3: AUDIO & VIDEO CREATOR (Placeholder)
# ==========================================
elif app_mode == "🎬 Audio/Video Creator":
    st.title("🎬 Media Creator")
    st.info("This section is ready for future API integrations (like Runway or ElevenLabs).")

# ==========================================
# TOOL 4: AI ASSISTANT CHATBOT
# ==========================================
elif app_mode == "💬 AI Chatbot":
    st.title("💬 Brainstorming Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                data = {"model": "gpt-4o", "messages": st.session_state.messages}
                
                response = requests.post(url, headers=headers, json=data).json()
                reply = response['choices'][0]['message']['content']
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error("Connection error. Check your API key.")