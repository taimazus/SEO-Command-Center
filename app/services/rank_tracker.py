import time
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from app.database import get_connection

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"
]

def check_keyword_serp(keyword: str, domain: str, max_pages: int = 1) -> int:
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    encoded_kw = urllib.parse.quote_plus(keyword)

    position = 0
    results_per_page = 10

    for page in range(max_pages):
        start = page * results_per_page
        search_url = f"https://www.google.com/search?q={encoded_kw}&num=10&start={start}&hl=fa&gl=ir"
        headers = {
            "User-Agent": USER_AGENTS[page % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fa,en-US;q=0.9,en;q=0.8",
        }

        try:
            resp = requests.get(search_url, headers=headers, timeout=2.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", href=True)

                for link in links:
                    href = link.get("href", "")
                    if href.startswith("/url?q="):
                        href = href.replace("/url?q=", "").split("&")[0]

                    if clean_domain in href.lower():
                        position = (page * results_per_page) + 1
                        return position
            else:
                break
        except Exception:
            break

    return position

def update_keyword_rank(keyword_id: int) -> Dict[str, Any]:
    conn = get_connection()
    kw_row = conn.execute("""
        SELECT k.*, s.domain, s.city
        FROM keywords k
        JOIN sites s ON s.id = k.site_id
        WHERE k.id = ?
    """, (keyword_id,)).fetchone()

    if not kw_row:
        conn.close()
        raise ValueError(f"Keyword ID {keyword_id} not found")

    keyword = kw_row["keyword"]
    domain = kw_row["domain"]
    prev_pos = kw_row["current_position"] or 0
    best_pos = kw_row["best_position"] or 0

    # Live SERP check
    new_pos = check_keyword_serp(keyword, domain)
    if new_pos == 0 and prev_pos > 0:
        # If rate-limited or not found, keep prev_pos or record 0
        new_pos = prev_pos

    new_best = new_pos if (best_pos == 0 or (new_pos > 0 and new_pos < best_pos)) else best_pos
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE keywords
        SET current_position = ?,
            previous_position = ?,
            best_position = ?,
            last_checked_at = ?
        WHERE id = ?
    """, (new_pos, prev_pos, new_best, now_str, keyword_id))

    conn.execute("""
        INSERT INTO rank_history (keyword_id, position, checked_at)
        VALUES (?, ?, ?)
    """, (keyword_id, new_pos, now_str))

    conn.commit()
    conn.close()

    return {
        "keyword_id": keyword_id,
        "keyword": keyword,
        "current_position": new_pos,
        "previous_position": prev_pos,
        "best_position": new_best,
        "change": (prev_pos - new_pos) if (prev_pos > 0 and new_pos > 0) else 0
    }

def update_all_site_ranks(site_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    keywords = conn.execute("SELECT id FROM keywords WHERE site_id = ?", (site_id,)).fetchall()
    conn.close()

    results = []
    for kw in keywords:
        res = update_keyword_rank(kw["id"])
        results.append(res)
    return results
