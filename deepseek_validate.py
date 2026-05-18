import json, os, dotenv

# Load the .env file
dotenv_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

api_key = os.environ.get("DEEPSEEK_API_KEY", "")
api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
print("API Key found:", bool(api_key))
if api_key:
    print("Key prefix:", api_key[:8] + "...")

import urllib.request
req = urllib.request.Request(
    "https://api.deepseek.com/models",
    headers={"Authorization": f"Bearer {api_key}"},
    method="GET"
)
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    models = [m["id"] for m in data.get("data", [])]
    print(f"Total models from API: {len(models)}")
    for m in sorted(models):
        print(f"  - {m}")
except Exception as e:
    print(f"Error: {e}")
