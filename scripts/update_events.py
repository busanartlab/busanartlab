import os
import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

API_KEY = os.environ.get("BUSAN_API_KEY", "").strip()
NEWSBUSAN_RSS_URL = "https://newsbusan.com"
OUTPUT_PATH = "data/events.json"

BUSAN_ENDPOINTS = [
    {
        "category": "미술·전시",
        "url": "https://data.go.kr",
        "root_key": "getBusanCultureExhibit"
    },
    {
        "category": "음악·공연",
        "url": "https://data.go.kr",
        "root_key": "getBusanCultureConcert"
    },
    {
        "category": "음악·공연",
        "url": "https://data.go.kr",
        "root_key": "getBusanCultureMusical"
    }
]

KCISA_AREA_URL = "https://data.go.kr"
TARGET_SIDOS = [
    {"sido": "부산", "rows": 50, "is_busan": True},
    {"sido": "서울", "rows": 25, "is_busan": False},
    {"sido": "울산", "rows": 15, "is_busan": False},
    {"sido": "경남", "rows": 15, "is_busan": False},
    {"sido": "대구", "rows": 15, "is_busan": False},
    {"sido": "광주", "rows": 15, "is_busan": False}
]

BUSAN_16_DISTRICTS = [
    "강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구",
    "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구"
]

VENUE_TO_DISTRICT = {
    "부산현대미술관": "사하구", "낙동강하구에코센터": "사하구", "을숙도": "사하구",
    "부산시립미술관": "해운대구", "영화의전당": "해운대구", "벡스코": "해운대구",
    "부산문화회관": "남구", "부산박물관": "남구",
    "부산시민회관": "동구", "부산항국제전시컨벤션센터": "동구",
    "부산시민공원": "부산진구", "상상마당": "부산진구",
    "F1963": "수영구", "공간 힘": "수영구",
    "부산시청": "연제구", "부산교육역사관": "동래구",
    "금정문화회관": "금정구", "영도문화예술회관": "영도구", "피아크": "영도구"
}

def fetch_newsbusan_articles():
    articles = []
    try:
        req = urllib.request.Request(NEWSBUSAN_RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as res:
            xml_data = res.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is not None and link_el is not None:
                title = (title_el.text or "").strip()
                link = (link_el.text or "").strip()
                if link.startswith("http") and link.rstrip("/") not in ["https://newsbusan.com", "https://newsbusan.com"]:
                    articles.append({"title": title, "link": link})
    except Exception as e:
        print(f"뉴스부산 RSS 수집 알림: {e}")
    return articles

def match_news_article(event_title, articles):
    clean_title = re.sub(r"[《》<>'\"\[\]\(\)·:]", " ", event_title)
    stop_words = {"부산", "서울", "전시", "공연", "기획전", "정기연주회", "초대전", "개인전", "특별전", "제1회", "제2회", "제3회"}
    keywords = [w for w in clean_title.split() if len(w) >= 2 and w not in stop_words]

    for art in articles:
        art_title = art["title"]
        matched = [kw for kw in keywords if kw in art_title]
        if len(matched) >= 2 or any(len(kw) >= 4 for kw in matched):
            return art["link"]
    return ""

def map_region(sido, gugun_or_place):
    text = f"{sido} {gugun_or_place}"
    if sido == "부산":
        for dist in BUSAN_16_DISTRICTS:
            if dist in text:
                return f"부산 {dist}"
        for venue_key, dist in VENUE_TO_DISTRICT.items():
            if venue_key in text:
                return f"부산 {dist}"
        return "부산 전체·일원"
    if sido in ["서울", "경기", "인천"]: return "서울·수도권"
    if sido in ["울산", "경남"]: return "울산·경남"
    if sido in ["대구", "경북"]: return "대구·경북"
    if sido in ["광주", "전남", "전북"]: return "광주·전라"
    return "대전·충청·강원·제주"

def map_category(default_cat, title_text):
    combined = f"{default_cat} {title_text}"
    if any(k in combined for k in ["서예", "문학", "시화", "서화", "문인화"]): return "서예·문학"
    if any(k in combined for k in ["미술", "전시", "갤러리", "회화", "조각", "사진", "비엔날레"]): return "미술·전시"
    if any(k in combined for k in ["음악", "콘서트", "연주", "오페라", "뮤지컬", "연극", "무용", "국악", "공연"]): return "음악·공연"
    return "축제·행사"

def format_date(dt_str):
    s = str(dt_str).strip().replace("-", ".")
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}.{s[4:6]}.{s[6:8]}"
    return s

def normalize_key(title, start_dt):
    clean = re.sub(r"[^가-힣a-zA-Z0-9]", "", title).lower()
    return f"{clean}_{start_dt}"

def fetch_busan_api(articles, seen_keys):
    results = []
    today_dot = datetime.now().strftime("%Y.%m.%d")

    for ep in BUSAN_ENDPOINTS:
        req_url = f"{ep['url']}?serviceKey={API_KEY}&pageNo=1&numOfRows=40&resultType=json"
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as res:
                raw = json.loads(res.read().decode("utf-8"))

            items = raw.get(ep["root_key"], {}).get("item", [])
            if isinstance(items, dict):
                items = [items]

            for item in items:
                title = (item.get("title") or "").strip()
                start_dt = format_date(item.get("op_st_dt") or "")
                end_dt = format_date(item.get("op_ed_dt") or "")
                venue = (item.get("place_nm") or "").strip()
                fee = (item.get("pay_at") or "주최 측 문의").strip()
                dabom_url = (item.get("dabom_url") or item.get("homepage") or "https://busandabom.net").strip()

                if not title or not end_dt or not venue or end_dt < today_dot:
                    continue

                dedup_key = normalize_key(title, start_dt or end_dt)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                status = "예정" if start_dt > today_dot else "진행중"
                period = f"{start_dt} - {end_dt}" if start_dt and start_dt != end_dt else (start_dt or end_dt)

                results.append({
                    "isBusan": True,
                    "status": status,
                    "category": map_category(ep["category"], title),
                    "region": map_region("부산", venue),
                    "title": title,
                    "period": period,
                    "endDate": end_dt,
                    "venue": venue,
                    "artist": (item.get("supervise") or "부산문화포털 다봄 공식 등록").strip(),
                    "fee": fee,
                    "newsUrl": match_news_article(title, articles),
                    "officialUrl": dabom_url
                })
        except Exception as e:
            print(f"[{ep['root_key']}] 호출 알림: {e}")
    return results

def fetch_kcisa_api(articles, seen_keys):
    results = []
    today_num = datetime.now().strftime("%Y%m%d")
    today_dot = datetime.now().strftime("%Y.%m.%d")

    for reg in TARGET_SIDOS:
        sido = reg["sido"]
        sido_enc = urllib.parse.quote(sido)
        req_url = f"{KCISA_AREA_URL}?serviceKey={API_KEY}&sido={sido_enc}&from={today_num}&PageNo=1&numOfrows={reg['rows']}"

        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as res:
                xml_data = res.read()

            root = ET.fromstring(xml_data)
            items = root.findall(".//item") or root.findall(".//perforList")
            for item in items:
                title = (item.findtext("title") or "").strip()
                start_dt = format_date(item.findtext("startDate") or "")
                end_dt = format_date(item.findtext("endDate") or "")
                place = (item.findtext("place") or "").strip()
                gugun = (item.findtext("gugun") or "").strip()
                realm = (item.findtext("realmName") or "").strip()
                seq = (item.findtext("seq") or "").strip()

                if not title or not end_dt or not place or end_dt < today_dot:
                    continue

                dedup_key = normalize_key(title, start_dt or end_dt)
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)

                status = "예정" if start_dt > today_dot else "진행중"
                period = f"{start_dt} - {end_dt}" if start_dt and start_dt != end_dt else end_dt
                official_url = f"https://culture.go.kr{seq}" if seq else "https://culture.go.kr"
                venue_label = f"[{sido}] {place}" if not reg["is_busan"] else (f"{place} ({gugun})" if gugun and gugun not in place else place)

                results.append({
                    "isBusan": reg["is_busan"],
                    "status": status,
                    "category": map_category(realm, title),
                    "region": map_region(sido, f"{gugun} {place}"),
                    "title": title,
                    "period": period,
                    "endDate": end_dt,
                    "venue": venue_label,
                    "artist": realm if realm else "문화포털 공식 등록",
                    "fee": "공식 안내 페이지 확인",
                    "newsUrl": match_news_article(title, articles),
                    "officialUrl": official_url
                })
        except Exception as e:
            print(f"[KCISA-{sido}] 호출 알림: {e}")
    return results

def main():
    if not API_KEY:
        print("BUSAN_API_KEY가 설정되지 않았습니다.")
        return

    os.makedirs("data", exist_ok=True)
    articles = fetch_newsbusan_articles()
    seen_keys = set()

    busan_events = fetch_busan_api(articles, seen_keys)
    kcisa_events = fetch_kcisa_api(articles, seen_keys)
    all_events = busan_events + kcisa_events

    all_events.sort(key=lambda x: (not x["isBusan"], not bool(x["newsUrl"]), x["period"]))

    if all_events:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_events, f, ensure_ascii=False, indent=2)

        print(f"총 {len(all_events)}건(부산 {len(busan_events)}건 + 통합 {len(kcisa_events)}건) 업데이트 완료.")
    else:
        print("수집된 신규 데이터가 없습니다.")

if __name__ == "__main__":
    main()
