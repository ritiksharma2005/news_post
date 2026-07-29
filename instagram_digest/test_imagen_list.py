import sys
import os

sys.path.append(os.getcwd())
import config
from google import genai

client = genai.Client(api_key=config.GEMINI_API_KEY)

print("Listing all models on API key:")
try:
    for m in client.models.list():
        # Check if the model name contains "imagen"
        if "imagen" in m.name.lower():
            print(f"Model: {m.name}")
            print(f"  Supported methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")
