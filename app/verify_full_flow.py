import requests
import time
import os

LOCAL_URL = os.getenv("LOCAL_URL", "http://localhost:8000")
AI_URL = os.getenv("AI_URL", "http://localhost:8001")

# Create a dummy PDF file
with open("test_roadmap.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Machine Learning Basics and Advanced Topics) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000157 00000 n\n0000000305 00000 n\n0000000392 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n486\n%%EOF")

TOPIC = "ML_Test_Topic"
FOCUS = "Neural Networks"

def verify():
    print("--- Starting Verification ---")
    
    # 1. Upload Material
    print("\n1. Uploading material...")
    with open("test_roadmap.pdf", "rb") as f:
        files = {'files': ("test_roadmap.pdf", f, "application/pdf")}
        data = {'topic': TOPIC}
        try:
            r = requests.post(f"{LOCAL_URL}/api/upload-materials", files=files, data=data)
            r.raise_for_status()
            print("Upload success.")
        except Exception as e:
            print(f"Upload failed: {e}")
            return

    # 2. Plan Roadmap (Proxy)
    print("\n2. Requesting Roadmap (via Proxy)...")
    payload = {
        "topic": TOPIC,
        "focus_area": FOCUS,
        "prerequisites_known": ["Math"],
        "prerequisites_unknown": ["Python"]
    }
    try:
        r = requests.post(f"{LOCAL_URL}/api/planning", json=payload, timeout=60)
        r.raise_for_status()
        roadmap_data = r.json()
        print("Roadmap received.")
        # print(roadmap_data)
        
        # Verify RAG usage
        if roadmap_data.get("context_used"):
            print("SUCCESS: RAG context was used.")
        else:
            print("WARNING: RAG context NOT used (maybe indexer was too slow to commit?).")
            
        real_roadmap = roadmap_data["roadmap"]["roadmap"]
        
    except Exception as e:
        print(f"Planning failed: {e}")
        # Use dummy roadmap to continue testing storage
        real_roadmap = {"Chapter 1": {"Lesson 1": " Intro"}}

    # 3. Save Roadmap
    print("\n3. Saving Roadmap...")
    try:
        r = requests.post(f"{LOCAL_URL}/api/roadmaps", json={
            "topic": TOPIC,
            "roadmap": real_roadmap
        })
        r.raise_for_status()
        print("Roadmap saved.")
    except Exception as e:
        print(f"Save failed: {e}")
        return

    # 4. List Topics
    print("\n4. Listing Topics...")
    try:
        r = requests.get(f"{LOCAL_URL}/api/topics")
        topics = r.json()["topics"]
        print(f"Topics: {topics}")
        if TOPIC in topics:
            print("SUCCESS: Topic found in list.")
        else:
            print("FAILURE: Topic not in list.")
    except Exception as e:
         print(f"List failed: {e}")

    # 5. Get Roadmap
    print("\n5. Fetching Roadmap...")
    try:
        r = requests.get(f"{LOCAL_URL}/api/roadmaps/{TOPIC}")
        r.raise_for_status()
        fetched = r.json()["roadmap"]
        if fetched == real_roadmap:
             print("SUCCESS: Roadmap fetched correctly.")
        else:
             print("FAILURE: Roadmap mismatch.")
    except Exception as e:
        print(f"Fetch failed: {e}")

    # 6. Delete Topic
    print("\n6. Deleting Topic...")
    try:
        r = requests.delete(f"{LOCAL_URL}/api/topics/{TOPIC}")
        r.raise_for_status()
        print(r.json())
        print("Delete request successful.")
    except Exception as e:
        print(f"Delete failed: {e}")

    # 7. Verify Deletion
    print("\n7. Verifying Deletion...")
    try:
        r = requests.get(f"{LOCAL_URL}/api/topics")
        topics = r.json()["topics"]
        if TOPIC not in topics:
            print("SUCCESS: Topic gone from list.")
        else:
            print("FAILURE: Topic still in list.")
            
        r = requests.get(f"{LOCAL_URL}/api/roadmaps/{TOPIC}")
        if r.status_code == 404:
            print("SUCCESS: Roadmap 404s.")
        else:
            print(f"FAILURE: Roadmap still exists (status {r.status_code}).")
            
    except Exception as e:
        print(f"Verify delete failed: {e}")

    # Cleanup
    if os.path.exists("test_roadmap.pdf"):
        os.remove("test_roadmap.pdf")

if __name__ == "__main__":
    verify()
