import os
import requests

key = os.getenv("GROQ_API_KEY", "")
model = "llama-3.3-70b-versatile"

print("Sending request to Groq...")
try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.1,
            "max_tokens": 100,
            "stream": False,
        },
        timeout=5,
    )
    print("Status code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", type(e).__name__, e)
