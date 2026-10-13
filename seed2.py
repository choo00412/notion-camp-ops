import os, time, random, requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()
H = {"Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
     "Content-Type": "application/json", "Notion-Version": "2026-03-11"}
BASE = "https://api.notion.com/v1"

def call(method, path, **kw):
    for _ in range(5):
        r = requests.request(method, BASE + path, headers=H, timeout=15, **kw)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 1)))
            continue
        if not r.ok:
            raise SystemExit(f"{r.status_code} {r.text[:300]}")
        time.sleep(0.35)
        return r.json()
    raise SystemExit("429 반복으로 중단")

S = {}
for o in call("POST", "/search", json={"page_size": 100})["results"]:
    if o["object"] == "data_source":
        S["".join(x["plain_text"] for x in o["title"])] = o["id"]
miss = [n for n in ["캠프", "학생", "세션", "출결", "과제", "제출"] if n not in S]
if miss:
    raise SystemExit(f"없는 DB: {miss}")

def has_title(p):
    for v in p["properties"].values():
        if v["type"] == "title":
            return len(v["title"]) > 0
    return True

def rows(name):
    out, cur = [], None
    while True:
        body = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        d = call("POST", f"/data_sources/{S[name]}/query", json=body)
        out += [x for x in d["results"] if has_title(x)]
        if not d.get("has_more"):
            return out
        cur = d["next_cursor"]

if rows("출결") or rows("과제") or rows("제출"):
    raise SystemExit("출결/과제/제출에 이미 데이터가 있어 중단합니다")

title = lambda v: {"title": [{"text": {"content": v}}]}
rel = lambda i: {"relation": [{"id": i}]}
sel = lambda v: {"select": {"name": v}}
dt = lambda d: {"date": {"start": d.isoformat()}}
nm = lambda p: p["properties"]["이름"]["title"][0]["plain_text"]

def add(src, props):
    return call("POST", "/pages", json={
        "parent": {"type": "data_source_id", "data_source_id": S[src]},
        "properties": props})["id"]

random.seed(42)
camp = rows("캠프")[0]
camp_id = camp["id"]
start = date.fromisoformat(camp["properties"]["시작일"]["date"]["start"])
students = [(s["id"], nm(s)) for s in rows("학생")]
sessions = sorted(rows("세션"), key=lambda s: s["properties"]["날짜"]["date"]["start"])

for s in sessions:
    for sid, sname in students:
        st = random.choices(["출석", "지각", "결석"], [85, 8, 7])[0]
        add("출결", {"이름": title(f"{nm(s)}-{sname}"), "세션": rel(s["id"]),
                    "학생": rel(sid), "상태": sel(st)})

for name, offset in [("가상 과제 1: 서비스 기획안", 14),
                     ("가상 과제 2: 중간 프로젝트", 42),
                     ("가상 과제 3: 최종 발표 자료", 70)]:
    due = start + timedelta(days=offset)
    a = add("과제", {"과제명": title(name), "캠프": rel(camp_id),
                    "마감일": dt(due), "대상": sel("개인")})
    for sid, sname in students:
        if random.random() < 0.88:
            d = due + timedelta(days=random.randint(-4, 2))
            add("제출", {"이름": title(f"{name[:5]}-{sname}"), "과제": rel(a),
                        "학생": rel(sid), "제출일": dt(d),
                        "링크": {"url": "https://example.com/submission"}})
print("완료")