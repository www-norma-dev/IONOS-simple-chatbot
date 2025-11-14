# backend/studio_client.py
"""
IONOS AI Model Studio client for fine-tuned models.
Uses cookie auth (factory_session) or API key when available.
"""
import os, time, httpx

BASE = os.getenv("STUDIO_BASE", "https://studio.ionos.de/api/v1")
ORG = os.getenv("STUDIO_ORG_ID")
KEY = os.getenv("STUDIO_API_KEY")

def studio_call(model_id: str, messages: list) -> str:
    """Single function: convert messages, create job, poll result."""
    # Convert to Studio format inline
    msgs = [{"role": "user" if m["type"] in ("human", "user") else "assistant", 
             "content": m["content"]} 
            for m in messages if m["type"] in ("human", "user", "ai", "assistant")]
    
    payload = {"model_id": model_id, "messages": [msgs], "temperature": 0.2, "max_tokens": 768}
    print(f"[DEBUG] Studio payload: {payload}")
    
    with httpx.Client(timeout=60) as c:
        # Create job
        r = c.post(f"{BASE}/organizations/{ORG}/generate", 
                   headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                   json=payload)
        if r.status_code != 200:
            print(f"[ERROR] Studio API error: {r.status_code} - {r.text}")
        r.raise_for_status()
        job_id = r.json()["job_id"]
        
        # Poll result
        for _ in range(60):
            g = c.get(f"{BASE}/organizations/{ORG}/generate/{job_id}",
                     headers={"Authorization": f"Bearer {KEY}"})
            g.raise_for_status()
            status = g.json()
            if status.get("job_status") == "FINISHED":
                return status["results"][0]["result"]
            if status.get("job_status") in ("FAILED", "CANCELED"):
                raise RuntimeError(f"Job failed: {status}")
            time.sleep(1)
        raise TimeoutError("Job timeout")
