import time
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from app.database import get_connection

def audit_site_health(site_id: int) -> Dict[str, Any]:
    conn = get_connection()
    site = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        raise ValueError(f"Site ID {site_id} not found")

    domain = site["domain"].replace("https://", "").replace("http://", "").strip("/")
    base_url = f"https://{domain}"
    www_url = f"https://www.{domain}"

    issues = []
    score = 100

    start_time = time.time()
    status_code = 0
    response_time_ms = 0.0
    has_ssl = False
    has_h1 = False
    h1_text = ""
    has_canonical = False
    canonical_url = ""
    has_sitemap = False
    has_robots = False
    redirect_301_working = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SEOCommandCenter/1.0"
    }

    # 1. Main Base URL Check
    try:
        resp = requests.get(base_url, headers=headers, timeout=12, verify=True)
        response_time_ms = round((time.time() - start_time) * 1000, 2)
        status_code = resp.status_code
        has_ssl = True

        if status_code != 200:
            score -= 30
            issues.append(f"کد وضعیت صفحه اصلی ناموفق است: {status_code}")

        # Parse HTML
        soup = BeautifulSoup(resp.text, "html.parser")

        # H1 Check
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.get_text(strip=True):
            has_h1 = True
            h1_text = h1_tag.get_text(strip=True)[:150]
        else:
            score -= 15
            issues.append("تگ H1 اصلی در صفحه پیدا نشد یا خالی است.")

        # Canonical Check
        canonical_tag = soup.find("link", rel=lambda val: val and "canonical" in val.lower())
        if canonical_tag and canonical_tag.get("href"):
            has_canonical = True
            canonical_url = canonical_tag.get("href")
        else:
            score -= 15
            issues.append("تگ Canonical برای جلوگیری از محتوای تکراری تعریف نشده است.")

    except requests.exceptions.SSLError:
        score -= 40
        issues.append("گواهی امنیتی SSL نامعتبر است یا منقضی شده است.")
    except Exception as e:
        score -= 50
        issues.append(f"عدم دسترسی به صفحه اصلی: {str(e)[:100]}")

    # 2. Check WWW 301 Redirect
    try:
        www_resp = requests.get(www_url, headers=headers, timeout=10, allow_redirects=False)
        if www_resp.status_code in [301, 302, 308]:
            redirect_301_working = True
        else:
            score -= 15
            issues.append("ریدایرکت ۳۰۱ نسخه www به غیر www به درستی فعال نیست.")
    except Exception:
        # If www fails or has DNS, note it
        score -= 10
        issues.append("بررسی ریدایرکت نسخه www با خطا مواجه شد.")

    # 3. Check Sitemap.xml
    sitemap_target = site["sitemap_url"] or f"{base_url}/sitemap.xml"
    try:
        s_resp = requests.get(sitemap_target, headers=headers, timeout=8)
        if s_resp.status_code == 200 and ("<urlset" in s_resp.text or "<sitemapindex" in s_resp.text):
            has_sitemap = True
        else:
            score -= 10
            issues.append("فایل نقشه سایت (sitemap.xml) در دسترس نیست یا فرمت معتبر ندارد.")
    except Exception:
        score -= 10
        issues.append("عدم امکان دریافت فایل sitemap.xml.")

    # 4. Check Robots.txt
    try:
        r_resp = requests.get(f"{base_url}/robots.txt", headers=headers, timeout=8)
        if r_resp.status_code == 200 and "User-agent:" in r_resp.text:
            has_robots = True
        else:
            score -= 10
            issues.append("فایل robots.txt یافت نشد.")
    except Exception:
        score -= 10
        issues.append("عدم دسترسی به robots.txt.")

    score = max(0, min(100, score))
    issues_json = json.dumps(issues, ensure_ascii=False)

    # Save to database
    conn.execute("""
        INSERT INTO health_audits (
            site_id, status_code, response_time_ms, has_ssl, has_h1, h1_text,
            has_canonical, canonical_url, has_sitemap, has_robots, redirect_301_working,
            overall_score, issues_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site_id, status_code, response_time_ms, has_ssl, has_h1, h1_text,
        has_canonical, canonical_url, has_sitemap, has_robots, redirect_301_working,
        score, issues_json
    ))
    conn.commit()
    conn.close()

    return {
        "site_id": site_id,
        "score": score,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "has_ssl": has_ssl,
        "has_h1": has_h1,
        "h1_text": h1_text,
        "has_canonical": has_canonical,
        "canonical_url": canonical_url,
        "has_sitemap": has_sitemap,
        "has_robots": has_robots,
        "redirect_301_working": redirect_301_working,
        "issues": issues
    }
