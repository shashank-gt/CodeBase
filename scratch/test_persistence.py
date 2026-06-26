import sys, time, requests, subprocess

BASE = "http://localhost:8000"

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_server():
    return subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def wait_for_server():
    for _ in range(20):
        try:
            r = requests.get(f"{BASE}/health")
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

print("1. Starting server...")
srv1 = run_server()
try:
    if not wait_for_server():
        print("❌ Server failed to start")
        sys.exit(1)
    
    print("2. Indexing codebase...")
    r = requests.post(f"{BASE}/analyze-repo", json={"local_path":".", "clear_existing":True})
    if r.status_code != 200:
        print(f"❌ Failed to index: {r.text}")
        sys.exit(1)
    
    initial_data = r.json()
    initial_chunks = initial_data["chunks_stored"]
    print(f"✅ Indexed {initial_chunks} chunks.")
    
    # Verify health status
    h = requests.get(f"{BASE}/health").json()
    print(f"Health info: BM25 ready={h['bm25_ready']}, Vector DB chunks={h['vector_db_chunks']}")
    
finally:
    print("3. Stopping server...")
    srv1.terminate()
    srv1.wait()

print("\n4. Restarting server to test recovery...")
srv2 = run_server()
try:
    if not wait_for_server():
        print("❌ Restarter failed to start")
        sys.exit(1)
        
    print("5. Checking health and persistence...")
    h2 = requests.get(f"{BASE}/health").json()
    
    print(f"Restored info: BM25 ready={h2['bm25_ready']}, Vector DB chunks={h2['vector_db_chunks']}")
    
    # Assert
    assert h2['bm25_ready'] is True, "BM25 was not rebuilt on startup"
    assert h2['vector_db_chunks'] == initial_chunks, "Vector store chunks mismatch after restart"
    
    # Check repo structure
    r_struct = requests.get(f"{BASE}/repo-structure")
    assert r_struct.status_code == 200, "Failed to fetch repo structure after restart"
    assert r_struct.json().get("name") == "CBQA3", "Repo structure name mismatch after restart"
    
    print("✅ Persistence and recovery across server restarts test PASSED successfully!")
    
finally:
    print("6. Stopping Restarter...")
    srv2.terminate()
    srv2.wait()
