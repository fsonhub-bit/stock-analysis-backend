
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Models to try (Preferred first)
models_to_try = ["gemma-3-27b-it", "gemma-2-27b-it", "gemini-2.0-flash-exp"]

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": 0.2}
        )
        response = model.generate_content("自己紹介をしてください。")
        print(f"✅ Success! Response:\n{response.text}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

for m_name in models_to_try:
    if test_model(m_name):
        print(f"Selected working model: {m_name}")
        break
