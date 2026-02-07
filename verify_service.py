
import requests
try:
    resp = requests.get("http://127.0.0.1:8000/api/topics", timeout=2)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json() if resp.status_code == 200 else resp.text}")
except Exception as e:
    print(f"Error: {e}")
