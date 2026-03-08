import os
from dotenv import load_dotenv
import requests

load_dotenv()

apis = {
    "ZAI (Zeta Alpha)": os.getenv("ZAI_API_KEY"),
    "OpenRouter": os.getenv("OPENROUTER_API_KEY"),
    "Cerebras": os.getenv("CEREBRAS_API_KEY"),
    "Gemini": os.getenv("GEMINI_API_KEY"),
    "Groq": os.getenv("GROQ_API_KEY"),
    "HuggingFace": os.getenv("HF_TOKEN"),
}

print("🔍 Testing API Keys...\n")

for name, key in apis.items():
    if key and len(key) > 10:
        print(f"✅ {name}: Configured (key: {key[:15]}...)")
    else:
        print(f"❌ {name}: Missing or invalid")

# Test OpenRouter specifically
print("\n🧪 Testing OpenRouter API call...")
try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen/qwen-2.5-coder-32b-instruct",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10
        },
        timeout=10
    )
    if response.status_code == 200:
        print("✅ OpenRouter: Working!")
    elif response.status_code == 429:
        print("⚠️  OpenRouter: Rate limited (free tier)")
    else:
        print(f"❌ OpenRouter: Error {response.status_code}")
except Exception as e:
    print(f"❌ OpenRouter: {str(e)}")

print("\n✨ Your bot will automatically rotate between working APIs!")
