import requests
import os

LOCAL_URL = "http://localhost:8010"
TOPIC = "IssueReproTopic"

def reproduce():
    print(f"Testing against {LOCAL_URL}")
    
    # 1. Create Topic (Upload) (Ensure it exists)
    print("1. Creating dummy topic...")
    with open("dummy.txt", "w") as f:
        f.write("Some dummy content for RAG indexing.")
        
    try:
        with open("dummy.txt", "rb") as f:
            files = {'files': ("dummy.txt", f, "text/plain")}
            data = {'topic': TOPIC}
            r = requests.post(f"{LOCAL_URL}/api/upload-materials", files=files, data=data)
            r.raise_for_status()
            print("Upload success.")
    except Exception as e:
        print(f"Upload failed: {e}")

    # 2. Check if roadmap exists (Expect 404 since we didn't generate it)
    print("2. Checking roadmap (Expect 404)...")
    r = requests.get(f"{LOCAL_URL}/api/roadmaps/{TOPIC}")
    print(f"Roadmap status: {r.status_code}")
    if r.status_code == 404:
        print("Confirmed: Roadmap not found as expected (user scenario).")
    
    # 3. Test Save Roadmap (Simulate frontend save)
    print("3. Testing Save Roadmap...")
    dummy_roadmap = {
        "Chapter 1: Basics": {
            "Lesson 1.1": "Intro to the topic",
            "Lesson 1.2": "Core concepts"
        }
    }
    try:
        r = requests.post(f"{LOCAL_URL}/api/roadmaps", json={
            "topic": TOPIC,
            "roadmap": dummy_roadmap
        })
        r.raise_for_status()
        print("Save success.")
    except Exception as e:
        print(f"Save failed: {e}")

    # 4. Test Get Roadmap (Simulate UI view)
    print("4. Testing Get Roadmap...")
    try:
        r = requests.get(f"{LOCAL_URL}/api/roadmaps/{TOPIC}")
        r.raise_for_status()
        data = r.json()
        print(f"Retrieved roadmap: {data}")
        if data["roadmap"] == dummy_roadmap:
            print("FULL FLOW SUCCESS: Roadmap saved and retrieved correctly!")
        else:
            print(f"DATA MISMATCH! Expected {dummy_roadmap}, got {data['roadmap']}")
    except Exception as e:
        print(f"Get failed: {e}")

    # 5. Try to delete topic
    print("5. Deleting topic...")
    try:
        r = requests.delete(f"{LOCAL_URL}/api/topics/{TOPIC}")
        print(f"Delete Status: {r.status_code}")
        print(f"Delete Content: {r.text}")
        r.raise_for_status()
        print("Delete success.")
    except Exception as e:
        print(f"Delete failed: {e}")

    if os.path.exists("dummy.txt"):
        os.remove("dummy.txt")

if __name__ == "__main__":
    reproduce()
