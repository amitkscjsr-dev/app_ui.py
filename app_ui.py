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
                    # Example API setup for OpenAI/Standard LLM
                    api_url = "https://api.openai.com/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    prompt = f"Write a highly engaging LinkedIn post about: {topic}. Make the tone {tone}. Include a hook, body, and a question at the end to drive engagement."
                    data = {
                        "model": "gpt-4o", # Or whichever model you use
                        "messages": [{"role": "user", "content": prompt}]
                    }
                    
                    # UNCOMMENT THE NEXT TWO LINES WHEN YOU HAVE YOUR LLM KEY
                    # response = requests.post(api_url, headers=headers, json=data).json()
                    # st.write(response['choices'][0]['message']['content'])
                    
                    st.success("Your post is ready! (API call commented out until key is added)")
                except Exception as e:
                    st.error(f"Error connecting to AI: {e}")
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
                    api_url = "YOUR_CANVAS_API_URL_HERE" 
                    headers = {"Authorization": f"Bearer {canvas_key}", "Content-Type": "application/json"}
                    data = {"prompt": user_prompt}
                    
                    # UNCOMMENT THE NEXT TWO LINES WHEN YOUR CANVAS URL IS READY
                    # response = requests.post(api_url, headers=headers, json=data)
                    # st.image(response.content)
                    
                    st.success(f"Image prompt sent: '{user_prompt}' (API call commented out until URL is added)")
                except Exception as e:
                    st.error(f"Error generating image: {e}")
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
                st.info(f"To activate this, you will plug in an API key for a tool like Runway (Video) or ElevenLabs (Audio) right here!")
        else:
            st.warning("Please provide a prompt or script.")

# ==========================================
# TOOL 4: AI ASSISTANT CHATBOT
# ==========================================
elif app_mode == "💬 AI Chatbot":
    st.title("💬 Brainstorming Assistant")
    st.write("Your personal AI for brainstorming and strategy.")
    
    # Initialize the chat history in Streamlit's memory
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I help you build your creator studio today?"}]

    # Draw the previous messages on the screen
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Wait for the user to type something new
    if user_input := st.chat_input("Type your message here..."):
        
        # 1. Show the user's message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # 2. Get the AI's response
        with st.chat_message("assistant"):
            # This is where your actual LLM API call will go. 
            # For now, it echoes back a placeholder response.
            reply = f"I am ready to help you with: '{user_input}'. Once your LLM API key is plugged in, I'll provide real answers!"
            st.markdown(reply)
            
        # 3. Save the AI's response to history
        st.session_state.messages.append({"role": "assistant", "content": reply})