import requests, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GOOGLE_API_KEY")
print("Key found:", key[:15] if key else "NONE — check .env file")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
r = requests.post(url, json={"contents": [{"parts": [{"text": "say hello"}]}]})
print("Status:", r.status_code)
print("Response:", r.json())