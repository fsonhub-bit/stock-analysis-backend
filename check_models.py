
import google.generativeai as genai
import os
from app.config import config

def list_models():
    api_key = config.GEMINI_API_KEY
    if not api_key:
        print("API Key not found")
        return

    genai.configure(api_key=api_key)
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

if __name__ == "__main__":
    list_models()
