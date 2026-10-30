import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Danh sach cac model ho tro generateContent voi API Key cua ban:")
try:
    for model in client.models.list():
        if "generateContent" in (model.supported_actions or []):
            print(f"- {model.name}")
except Exception as e:
    print(f"Loi khi lay danh sach model: {e}")