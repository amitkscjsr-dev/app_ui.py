import os
from dotenv import load_dotenv

# Load the secrets from the .env file
load_dotenv()

# Fetch the key securely
my_api_key = os.getenv("CANVAS_API_KEY")