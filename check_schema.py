import os, requests
from dotenv import load_dotenv

load_dotenv()
headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}

r = requests.post(
    "https://api.notion.com/v1/search",
    headers=headers, json={"page_size": 100}, timeout=10,
)
print(r.status_code)
for o in r.json().get("results", []):
    t = o.get("title") or o.get("name") or ""
    if isinstance(t, list):
        t = "".join(x.get("plain_text", "") for x in t)
    if o["object"] in ("database", "data_source"):
        print(o["object"], "|", t, "|", o["id"])
        print("  ", list(o.get("properties", {}).keys()))