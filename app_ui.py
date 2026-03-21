import streamlit as st
import os
from dotenv import load_dotenv

# Load the API key securely
load_dotenv()
api_key = os.getenv("CANVAS_API_KEY")

# Set up the web page title
st.set_page_config(page_title="Image Generator", page_icon="🎨")

# Draw the main interface
st.title("🎨 Canvas Image Generator")
st.write("Welcome to the custom image generation tool!")

# Add a text box for the user to type what they want to see
user_prompt = st.text_input("What would you like to create today?", placeholder="A vintage car driving through a neon city...")

# Add a button to trigger the generation
if st.button("Generate Image"):
    if user_prompt:
        st.success(f"System is ready to generate: '{user_prompt}'")
    else:
        st.warning("Please type a description into the box first.")