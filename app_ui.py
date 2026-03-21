import streamlit as st
import os
import requests
from dotenv import load_dotenv

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

st.sidebar.markdown("---")
st.sidebar.info("Ensure LLM_API_KEY is added to Streamlit Secrets.")

# ===============================
# Helper function: OpenAI Chat API
# ===============================
def generate_text(prompt, model="gpt-4o"):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        response = requests.post(url, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

# ===============================
# TOOL 1: LINKEDIN CONTENT WRITER
# ===============================
if app_mode == "✍️ LinkedIn Writer":
    st.title("✍️ LinkedIn Content Writer")
    topic = st.text_area("What is your post about?", placeholder="e.g., Leadership in banking...")
    tone = st.selectbox("Select Tone:", ["Professional", "Bold", "Storytelling"])
    
    if st.button("Draft Post"):
        if topic:
            with st.spinner("Drafting..."):
                post = generate_text(f"Write a LinkedIn post about '{topic}' in a '{tone}' tone.")
                st.markdown(post)
        else:
            st.warning("Please enter a topic.")

# ===============================
# TOOL 2: IMAGE GENERATOR (DALL-E)
# ===============================
elif app_mode == "🎨 Image Generator":
    st.title("🎨 AI Image Generator")
    user_prompt = st.text_input("Describe the image:", placeholder="A futuristic city skyline...")
    
    if st.button("Generate Image"):
        if user_prompt:
            with st.spinner("Generating image..."):
                try:
                    url = "https://api.openai.com/v1/images/generations"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    data = {"model": "dall-e-3", "prompt": user_prompt, "n": 1, "size": "1024x1024"}
                    response = requests.post(url, headers=headers, json=data).json()
                    image_url = response['data'][0]['url']
                    st.image(image_url, caption=user_prompt)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a description.")

# ===============================
# TOOL 3: AUDIO & VIDEO CREATOR
# ===============================
elif app_mode == "🎬 Audio/Video Creator":
    st.title("🎬 Media Creator")
    st.info("Placeholder for AI video/audio tools (Runway, ElevenLabs, etc.)")

# ===============================
# TOOL 4: AI ASSISTANT CHATBOT
# ===============================
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
            reply = generate_text(user_input)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# ===============================
# TOOL 5: CONTENT CALENDAR
# ===============================
elif app_mode == "📅 Content Calendar":
    st.title("📅 AI Content Calendar")
    st.write("Plan and schedule your LinkedIn posts.")
    
    post_dates = st.date_input("Select dates for posts:", [])
    post_ideas = st.text_area("Add ideas or topics (one per line):", "")
    
    if st.button("Generate Schedule"):
        if post_dates and post_ideas:
            calendar_output = ""
            for i, date in enumerate(post_dates):
                idea = post_ideas.splitlines()[i % len(post_ideas.splitlines())]
                calendar_output += f"- {date}: {idea}\n"
            st.text(calendar_output)
        else:
            st.warning("Select dates and add topics.")

# ===============================
# TOOL 6: DOCUMENT SUMMARIZER
# ===============================
elif app_mode == "📝 Document Summarizer":
    st.title("📝 Document/Meeting Summarizer")
    doc_text = st.text_area("Paste text or meeting notes here:")
    
    if st.button("Summarize"):
        if doc_text:
            summary = generate_text(f"Summarize the following professionally:\n{doc_text}")
            st.markdown(summary)
        else:
            st.warning("Paste some text first.")

# ===============================
# TOOL 7: ANALYTICS DASHBOARD
# ===============================
elif app_mode == "📊 Analytics Dashboard":
    st.title("📊 Post Analytics Dashboard")
    st.info("This is a placeholder for future integrations with LinkedIn/Twitter API.")
    st.write("Metrics: Engagement, Likes, Comments, Shares (mock data)")
    st.table({
        "Post": ["Post 1", "Post 2", "Post 3"],
        "Likes": [120, 80, 150],
        "Comments": [12, 5, 20],
        "Shares": [10, 3, 8]
    })

# ===============================
# TOOL 8: TREND MONITORING
# ===============================
elif app_mode == "📈 Trend Monitoring":
    st.title("📈 Trend Monitoring")
    topic = st.text_input("Enter your industry/topic:", "AI, Tech, Marketing")
    
    if st.button("Check Trends"):
        trends = generate_text(f"List top trending topics for {topic} in a professional context.")
        st.markdown(trends)

# ===============================
# TOOL 9: SLIDE/INFOGRAPHIC GENERATOR
# ===============================
elif app_mode == "🎞️ Slide/Infographic Generator":
    st.title("🎞️ Slide / Infographic Generator")
    content = st.text_area("Enter main points for slides or infographic:")
    
    if st.button("Generate Slides/Infographic"):
        if content:
            slides = generate_text(f"Convert the following points into a professional slide deck format:\n{content}")
            st.markdown(slides)
        else:
            st.warning("Please enter points to convert.")

# ===============================
# TOOL 10: WORKFLOW AUTOMATION
# ===============================
elif app_mode == "🤖 Workflow Automation":
    st.title("🤖 Automation & Workflow Builder")
    st.write("Chain multiple content creation actions into a single workflow.")

    # Step 1: Select actions
    actions = st.multiselect(
        "Select actions in order:",
        [
            "Draft LinkedIn Post",
            "Generate Image",
            "Summarize Document",
            "Generate Slide/Infographic",
            "Check Industry Trends"
        ]
    )

    # Step 2: Inputs for each action
    workflow_inputs = {}
    if "Draft LinkedIn Post" in actions:
        workflow_inputs['post_topic'] = st.text_input("LinkedIn Post Topic:")
        workflow_inputs['post_tone'] = st.selectbox("Post Tone:", ["Professional", "Bold", "Storytelling"])
    
    if "Generate Image" in actions:
        workflow_inputs['image_prompt'] = st.text_input("Image Description:")
    
    if "Summarize Document" in actions:
        workflow_inputs['doc_text'] = st.text_area("Document / Meeting Notes:")
    
    if "Generate Slide/Infographic" in actions:
        workflow_inputs['slide_points'] = st.text_area("Points for Slides/Infographic:")
    
    if "Check Industry Trends" in actions:
        workflow_inputs['trend_topic'] = st.text_input("Industry / Topic for Trends:")

    # Step 3: Execute workflow
    if st.button("Run Workflow"):
        st.info("Running workflow...")
        results = {}

        if "Draft LinkedIn Post" in actions:
            topic = workflow_inputs.get('post_topic', '')
            tone = workflow_inputs.get('post_tone', 'Professional')
            if topic:
                results['LinkedIn Post'] = generate_text(f"Write a LinkedIn post about '{topic}' in a '{tone}' tone.")
            else:
                results['LinkedIn Post'] = "No topic provided."

        if "Generate Image" in actions:
            prompt = workflow_inputs.get('image_prompt', '')
            if prompt:
                try:
                    url = "https://api.openai.com/v1/images/generations"
                    headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
                    data = {"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"}
                    response = requests.post(url, headers=headers, json=data).json()
                    results['Image'] = response['data'][0]['url']
                except Exception as e:
                    results['Image'] = f"Error: {e}"
            else:
                results['Image'] = "No image prompt provided."

        if "Summarize Document" in actions:
            doc = workflow_inputs.get('doc_text', '')
            results['Document Summary'] = generate_text(f"Summarize the following professionally:\n{doc}") if doc else "No document provided."

        if "Generate Slide/Infographic" in actions:
            points = workflow_inputs.get('slide_points', '')
            results['Slides/Infographic'] = generate_text(f"Convert the following points into a professional slide deck format:\n{points}") if points else "No points provided."

        if "Check Industry Trends" in actions:
            topic = workflow_inputs.get('trend_topic', '')
            results['Trends'] = generate_text(f"List top trending topics for {topic} in a professional context.") if topic else "No topic provided."

        # Step 4: Display results
        st.success("Workflow completed! Here are your results:")
        for key, value in results.items():
            if key == "Image" and value.startswith("http"):
                st.image(value, caption="Generated Image")
            else:
                st.markdown(f"### {key}")
                st.markdown(value)