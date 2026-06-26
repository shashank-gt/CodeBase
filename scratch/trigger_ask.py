import time
import requests

print("Waiting for server to fully initialize...")
time.sleep(3)

print("Checking /health endpoint...")
try:
    r = requests.get("http://localhost:8000/health")
    print("Health response:", r.status_code)
    print(r.json())
except Exception as e:
    print("Health check failed:", e)

print("\nSending /ask request to server...")
try:
    r = requests.post(
        "http://localhost:8000/ask",
        json={"question": "What is the overall architecture of this project?"}
    )
    print("Ask response status code:", r.status_code)
    print("Ask response JSON:", r.json())
except Exception as e:
    print("Ask request failed:", e)
