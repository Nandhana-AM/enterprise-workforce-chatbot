import requests
import json

base_url = "http://localhost:8000"

# 1. Reset session first
requests.post(f"{base_url}/reset-session", json={"session_id": "debug_session"})

# 2. Query 1: find people skilled in waterproofing
r1 = requests.post(
    f"{base_url}/chat",
    json={"session_id": "debug_session", "message": "find people skilled in waterproofing"}
)
print("Query 1 status:", r1.status_code)
if r1.status_code == 200:
    data = r1.json()
    print("Query 1 Active Filters:", data.get("active_filters"))
    print("Query 1 Results Count:", len(data.get("results", [])))
    if data.get("results"):
        print("First employee total_exp:", data["results"][0].get("total_exp"))
else:
    print(r1.text)

# 3. Query 2: find people skilled in waterproofing with atleast 5 years experience
r2 = requests.post(
    f"{base_url}/chat",
    json={"session_id": "debug_session", "message": "find people skilled in waterproofing with atleast 5 years experience"}
)
print("Query 2 status:", r2.status_code)
if r2.status_code == 200:
    data = r2.json()
    print("Query 2 Active Filters:", data.get("active_filters"))
    print("Query 2 Results Count:", len(data.get("results", [])))
    print("Query 2 Message:", data.get("message"))
else:
    print(r2.text)
