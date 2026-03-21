import streamlit as st
import os
import requests
from dotenv import load_dotenv

# Load the API key securely
load_dotenv()
api_key = os.getenv("CANVAS_API_KEY")

# Set up the web page title
st.set_page_config(page_title="Image Generator", page_icon="🎨")

# Draw the main interface
st.title("🎨 Canvas Image Generator")
st.write("Welcome to the custom image generation tool!")

# Add a text box for the user
user_prompt = st.text_input("What would you like to create today?", placeholder="A vintage car in a retro setting...")

# Add the button
if st.button("Generate Image"):
    if user_prompt:
        # Show a loading spinner while waiting for the API
        with st.spinner("Generating your image..."):
            
            # --- YOUR CANVAS API CODE GOES HERE ---
            # We will use your api_key and user_prompt variables
            
            st.success("API connection ready!")
    else:
        st.warning("Please type a description into the box first.")