import os
import google.generativeai as genai

key = os.getenv("GEMINI_API_KEY", "")
model = "gemini-2.5-flash"

print("Sending request to Gemini...")
try:
    genai.configure(api_key=key)
    m = genai.GenerativeModel(model_name=model)
    response = m.generate_content("Hello")
    print("Gemini response text:", response.text)
except Exception as e:
    print("Error:", type(e).__name__, e)
