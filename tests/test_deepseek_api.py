import os, requests, json, time
API_KEY = os.environ["DEEPSEEK_API_KEY"]
payload = {
  "model": "deepseek-chat",
  "messages": [
    {"role":"system","content":"You are terse."},
    {"role":"user","content":"Say OK"}
  ],
  "stream": False
}
t0 = time.time()
r = requests.post(
  "https://api.deepseek.com/chat/completions",
  headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
  json=payload,
  timeout=40,
)
print("status:", r.status_code, "elapsed:", round(time.time()-t0,2), "s")
print(r.text[:400])