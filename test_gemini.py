import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Using GEMINI_API_KEY: {api_key[:10]}...{api_key[-5:] if api_key else ''}")

# 1. Try listing models to see what this key has access to
print("\n--- Trying to list models ---")
list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    r = httpx.get(list_url)
    print("List models status code:", r.status_code)
    if r.status_code == 200:
        models = r.json().get("models", [])
        print("Available models:")
        for m in models:
            print(" -", m.get("name"))
    else:
        print("List models error response:", r.text)
except Exception as e:
    print("Error listing models:", str(e))

# 2. Try v1 endpoint
print("\n--- Trying v1 endpoint ---")
v1_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": "Hello"}]}]
}
try:
    r = httpx.post(v1_url, json=payload, headers={"Content-Type": "application/json"})
    print("v1 status code:", r.status_code)
    print("v1 response:", r.text[:300])
except Exception as e:
    print("Error trying v1:", str(e))

# 3. Try v1beta endpoint
print("\n--- Trying v1beta endpoint ---")
v1beta_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
try:
    r = httpx.post(v1beta_url, json=payload, headers={"Content-Type": "application/json"})
    print("v1beta status code:", r.status_code)
    print("v1beta response:", r.text[:300])
except Exception as e:
    print("Error trying v1beta:", str(e))
