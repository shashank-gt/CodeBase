import sys
import requests

# Force stdout to output UTF-8 safely on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("Sending /ask request to server...")
try:
    r = requests.post(
        "http://localhost:8000/ask",
        json={"question": "What is the overall architecture of this project?"}
    )
    print(f"Server Status Code: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("\n=== SUCCESSFUL GROQ RESPONSE ===\n")
        print(data["answer"][:1000] + "\n...")
    else:
        print("Error Response:", r.json())
except Exception as e:
    print("Request failed:", e)
