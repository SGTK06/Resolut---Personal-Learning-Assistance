import requests
import json
import time

LOCAL_SERVICE = "http://127.0.0.1:8000"
AI_SERVICE = "http://127.0.0.1:8001"

def print_result(step, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {step}")
    if details:
        print(f"   {details}")

def verify_rag():
    print("Starting RAG Verification...")
    
    # 1. Check Index Stats (Local Service)
    try:
        resp = requests.get(f"{LOCAL_SERVICE}/api/tools/index_stats")
        if resp.status_code == 200:
            stats = resp.json()
            print_result("Check Index Stats", True, f"Total Vectors: {stats.get('total_vectors')}")
        else:
            print_result("Check Index Stats", False, f"Status: {resp.status_code}")
            return
    except Exception as e:
        print_result("Check Index Stats", False, str(e))
        return

    # 2. Upload and Index File (Local Service)
    test_content = """
    Resolut Learning Assistant is a cool project.
    It uses a local RAG architecture.
    The embeddings are generated on the device using sentence-transformers.
    This ensures user privacy.
    """
    files = {'files': ('test_doc.txt', test_content, 'text/plain')}
    data = {'topic': 'resolut-architecture'}
    
    try:
        resp = requests.post(f"{LOCAL_SERVICE}/api/upload-materials", files=files, data=data)
        if resp.status_code == 200:
            result = resp.json()
            print_result("Upload & Index", True, f"Indexed: {result.get('message')}")
        else:
            print_result("Upload & Index", False, resp.text)
            return
    except Exception as e:
        print_result("Upload & Index", False, str(e))
        return

    # 3. Verify Search Tool (Local Service direct call)
    search_payload = {"query": "local RAG architecture", "top_k": 2}
    try:
        resp = requests.post(f"{LOCAL_SERVICE}/api/tools/search_knowledge_base", json=search_payload)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            found = any("local RAG architecture" in r['content'] for r in results)
            print_result("Direct Search Tool", found, f"Found {len(results)} chunks")
        else:
            print_result("Direct Search Tool", False, resp.text)
    except Exception as e:
        print_result("Direct Search Tool", False, str(e))

    # 4. Verify AI Service Tool Use (AI Service -> Local Tool)
    # The AI service should call back to the local service using the provided URL
    ai_payload = {
        "topic": "resolut-architecture",
        "focus_area": "privacy",
        "device_callback_url": LOCAL_SERVICE 
    }
    
    try:
        print("   Calling AI Service (this might take a moment if it runs inference)...")
        resp = requests.post(f"{AI_SERVICE}/api/ai/prerequisites", json=ai_payload)
        
        if resp.status_code == 200:
            data = resp.json()
            context_used = data.get("context_used", False)
            print_result("AI Agent RAG", context_used, "AI successfully used local context")
            if not context_used:
                print(f"   AI Response: {json.dumps(data, indent=2)}")
        else:
            print_result("AI Agent RAG", False, resp.text)
            
    except Exception as e:
        print_result("AI Agent RAG", False, str(e))

if __name__ == "__main__":
    verify_rag()
