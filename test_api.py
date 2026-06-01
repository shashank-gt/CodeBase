"""
CBQA V5 — end-to-end smoke tests.
Run after server is up: python test_api.py
"""
import sys, requests

BASE = "http://localhost:8000"
OK = "  ✅"; FAIL = "  ❌"

def chk(label, cond, detail=""):
    if cond: print(f"{OK}  {label}")
    else: print(f"{FAIL}  {label}  →  {detail}"); sys.exit(1)

print("\n══ Health ════════════════════════════════════════")
r = requests.get(f"{BASE}/health"); d = r.json()
chk("GET /health → 200", r.status_code == 200)
chk("version == 5.0.0", d.get("version") == "5.0.0")
chk("bm25_ready field present", "bm25_ready" in d)
chk("hyde_enabled field present", "hyde_enabled" in d)
print(f"     {d['llm_provider']} / {d['llm_model']}")
print(f"     BM25: {d['bm25_ready']}  HyDE: {d['hyde_enabled']}  Rerank: {d['rerank_enabled']}")

print("\n══ Analyze repo (this project) ═══════════════════")
r = requests.post(f"{BASE}/analyze-repo", json={"local_path":".", "clear_existing":True})
chk("POST /analyze-repo → 200", r.status_code == 200, r.text[:200])
d = r.json()
chk("files_processed > 0", d["files_processed"] > 0)
chk("chunks_stored > 0", d["chunks_stored"] > 0)
chk("repo_meta present", "repo_meta" in d)
chk("bm25 ready after index", requests.get(f"{BASE}/health").json()["bm25_ready"])
print(f"     {d['files_processed']} files → {d['chunks_stored']} chunks")
print(f"     tech: {d['repo_meta'].get('tech_stack',[][:3])}")

print("\n══ Repo structure endpoint ═══════════════════════")
r = requests.get(f"{BASE}/repo-structure")
chk("GET /repo-structure → 200", r.status_code == 200)
chk("repo_tree in response", "repo_tree" in r.json())

print("\n══ Ask question ══════════════════════════════════")
r = requests.post(f"{BASE}/ask", json={"question":"What does the BM25 index do and which file implements it?"})
chk("POST /ask → 200", r.status_code == 200, r.text[:200])
d = r.json()
chk("answer not empty", len(d["answer"]) > 20)
chk("sources present", len(d["sources"]) > 0)
chk("retrieval_method present", "retrieval_method" in d)
chk("cached == False", d["cached"] == False)
print(f"     chunks={d['chunks_used']}  cached={d['cached']}  method={d['retrieval_method']}")
print(f"     answer[:100]: {d['answer'][:100]}...")

print("\n══ Cache hit ═════════════════════════════════════")
r2 = requests.post(f"{BASE}/ask", json={"question":"What does the BM25 index do and which file implements it?"})
chk("second call cached", r2.json()["cached"] == True)

print("\n══ Multi-turn follow-up ══════════════════════════")
r3 = requests.post(f"{BASE}/ask", json={
    "question": "Which algorithm does BM25 use to score documents?",
    "history": [
        {"role":"user","content":"What does the BM25 index do?"},
        {"role":"assistant","content":d["answer"]},
    ]
})
chk("follow-up → 200", r3.status_code == 200)
chk("follow-up has answer", len(r3.json()["answer"]) > 10)

print("\n══ Summarize ═════════════════════════════════════")
r = requests.post(f"{BASE}/summarize")
chk("POST /summarize → 200", r.status_code == 200)
chk("summary not empty", len(r.json().get("summary","")) > 20)

print("\n══ Input validation ══════════════════════════════")
chk("empty question → 422", requests.post(f"{BASE}/ask", json={"question":""}).status_code == 422)
chk("bad github url → 422", requests.post(f"{BASE}/analyze-repo", json={"github_url":"not-github"}).status_code == 422)
chk("no source → 400", requests.post(f"{BASE}/analyze-repo", json={}).status_code == 400)

print("\n══ Stats & clear ═════════════════════════════════")
r = requests.get(f"{BASE}/stats")
chk("GET /stats → 200", r.status_code == 200)
chk("total_chunks in stats", "total_chunks" in r.json())
r = requests.delete(f"{BASE}/clear")
chk("DELETE /clear → 200", r.status_code == 200)
chk("chunks 0 after clear", requests.get(f"{BASE}/stats").json()["total_chunks"] == 0)

print("\n══ All tests passed ✅ ════════════════════════════\n")
