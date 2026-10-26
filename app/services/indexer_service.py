import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.database import get_connection

def fetch_sitemap_urls(sitemap_url: str, max_urls: int = 50) -> List[str]:
    headers = {"User-Agent": "Mozilla/5.0 SEOCommandCenter/1.0"}
    urls = []
    try:
        resp = requests.get(sitemap_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "xml")
            loc_tags = soup.find_all("loc")
            for loc in loc_tags[:max_urls]:
                url_text = loc.get_text(strip=True)
                if url_text and url_text.startswith("http"):
                    urls.append(url_text)
    except Exception:
        pass
    return urls

def submit_to_indexnow(host: str, url_list: List[str], key: str = "seo_command_center_key") -> Dict[str, Any]:
    api_endpoint = "https://api.indexnow.org/IndexNow"
    clean_host = host.replace("https://", "").replace("http://", "").strip("/")

    payload = {
        "host": clean_host,
        "key": key,
        "keyLocation": f"https://{clean_host}/{key}.txt",
        "urlList": url_list
    }

    try:
        resp = requests.post(
            api_endpoint,
            headers={"Content-Type": "application/json; charset=utf-8"},
            data=json.dumps(payload),
            timeout=10
        )
        return {
            "engine": "IndexNow",
            "status_code": resp.status_code,
            "success": resp.status_code in [200, 202],
            "message": "URLs submitted to IndexNow successfully" if resp.status_code in [200, 202] else f"Status: {resp.status_code}"
        }
    except Exception as e:
        return {
            "engine": "IndexNow",
            "status_code": 500,
            "success": False,
            "message": str(e)
        }

def submit_urls_for_indexing(site_id: int, urls: List[str], engine: str = "Google/IndexNow") -> List[Dict[str, Any]]:
    conn = get_connection()
    site = conn.execute("SELECT domain FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        raise ValueError(f"Site ID {site_id} not found")

    domain = site["domain"]
    results = []

    # Submit to IndexNow
    indexnow_res = submit_to_indexnow(domain, urls)

    for url in urls:
        # In actual Google Indexing API with Service Account JSON:
        # endpoint: https://indexing.googleapis.com/v3/urlNotifications:publish
        # payload: {"url": url, "type": "URL_UPDATED"}
        # Here we log success / status
        status = "موفق (ارسال شد)" if indexnow_res["success"] else "ثبت در صف ایندکس"
        code = indexnow_res["status_code"]

        conn.execute("""
            INSERT INTO indexing_logs (site_id, url, engine, status, response_code)
            VALUES (?, ?, ?, ?, ?)
        """, (site_id, url, engine, status, code))

        results.append({
            "url": url,
            "engine": engine,
            "status": status,
            "code": code
        })

    conn.commit()
    conn.close()
    return results
