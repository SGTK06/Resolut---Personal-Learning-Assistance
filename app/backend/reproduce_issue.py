import requests
import json

url = "http://127.0.0.1:8001/api/ai/teaching"
payload = {
    "topic": "Test Topic",
    "chapter_title": "Chapter 1",
    "lesson_title": "Lesson 1"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
