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
        time.sleep(0.35)  # 초당 3요청 제한 대응
        return r.json()
    raise SystemExit("429가 반복되어 중단")

S = {}
for o in call("POST", "/search", json={"page_size": 100})["results"]:
    if o["object"] == "data_source":
        S["".join(x["plain_text"] for x in o["title"])] = o["id"]
miss = [n for n in ["캠프", "강사", "팀", "학생", "세션", "자료"] if n not in S]
if miss:
    raise SystemExit(f"없는 DB: {miss}")

title = lambda v: {"title": [{"text": {"content": v}}]}
rel = lambda i: {"relation": [{"id": i}]}
sel = lambda v: {"select": {"name": v}}
dt = lambda d: {"date": {"start": d.isoformat()}}

def add(src, props):
    return call("POST", "/pages", json={
        "parent": {"type": "data_source_id", "data_source_id": S[src]},
        "properties": props})["id"]

if call("POST", f"/data_sources/{S['캠프']}/query", json={"page_size": 1})["results"]:
    raise SystemExit("캠프에 이미 데이터가 있어 중복 방지를 위해 중단합니다")

start = date(2026, 11, 2)
camp = add("캠프", {"이름": title("가상 AI 기획자 과정 1기"), "시작일": dt(start),
                    "종료일": dt(start + timedelta(days=89)), "상태": sel("진행중")})
subjects = ["기획", "AI 도구 활용", "UX 디자인"]
teachers = [add("강사", {"이름": title(f"가상강사{i+1}"),
            "담당 과목": {"rich_text": [{"text": {"content": s}}]}})
            for i, s in enumerate(subjects)]
teams = [add("팀", {"팀명": title(f"팀{i+1}"), "캠프": rel(camp)}) for i in range(6)]
for i in range(30):
    add("학생", {"이름": title(f"가상학생{i+1:02d}"), "캠프": rel(camp),
                "팀": rel(teams[i % 6]), "상태": sel("수강중")})
types = ["강의", "강의", "강의", "발표", "행사"]
for i in range(10):
    s = add("세션", {"이름": title(f"가상 세션 {i+1}"),
                    "날짜": dt(start + timedelta(days=7 * i)), "유형": sel(types[i % 5]),
                    "캠프": rel(camp), "강사": rel(teachers[i % 3])})
    add("자료", {"제목": title(f"가상 자료 {i+1}"), "세션": rel(s),
                "강사": rel(teachers[i % 3]), "링크": {"url": "https://example.com/sample"},
                "공개 여부": {"checkbox": i % 2 == 0}})
print("완료: 캠프1, 강사3, 팀6, 학생30, 세션10, 자료10")