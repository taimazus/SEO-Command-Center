import os
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, get_connection
from app.services.rank_tracker import update_keyword_rank, update_all_site_ranks
from app.services.health_auditor import audit_site_health
from app.services.ai_content import generate_seo_article
from app.services.indexer_service import submit_urls_for_indexing, fetch_sitemap_urls

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="SEO Command Center",
    description="Multi-Tenant SEO Management, SERP Rank Tracking & AI Content Autopilot",
    version="2.0.0",
    lifespan=lifespan
)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ----------------- WEB PAGES -----------------

@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    conn = get_connection()
    sites = conn.execute("""
        SELECT s.*, COUNT(k.id) AS keyword_count
        FROM sites s
        LEFT JOIN keywords k ON k.site_id = s.id
        GROUP BY s.id
        ORDER BY s.id ASC
    """).fetchall()

    keywords = conn.execute("""
        SELECT k.*, s.domain, s.name as site_name
        FROM keywords k
        JOIN sites s ON s.id = k.site_id
        ORDER BY k.current_position ASC, k.id ASC
        LIMIT 10
    """).fetchall()

    total_sites = len(sites)
    total_keywords = conn.execute("SELECT COUNT(*) AS c FROM keywords").fetchone()["c"]
    page_one_keywords = conn.execute("SELECT COUNT(*) AS c FROM keywords WHERE current_position > 0 AND current_position <= 10").fetchone()["c"]

    recent_audit = conn.execute("SELECT AVG(overall_score) as avg_score FROM health_audits").fetchone()
    avg_health_score = int(recent_audit["avg_score"] or 95)

    conn.close()

    stats = {
        "total_sites": total_sites,
        "total_keywords": total_keywords,
        "page_one_keywords": page_one_keywords,
        "avg_health_score": avg_health_score
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "active_page": "dashboard",
            "stats": stats,
            "sites": sites,
            "top_keywords": keywords
        }
    )

@app.get("/sites", response_class=HTMLResponse)
def list_sites_page(request: Request):
    conn = get_connection()
    sites = conn.execute("""
        SELECT s.*, COUNT(k.id) AS keyword_count
        FROM sites s
        LEFT JOIN keywords k ON k.site_id = s.id
        GROUP BY s.id
        ORDER BY s.id ASC
    """).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="sites.html",
        context={
            "active_page": "sites",
            "sites": sites
        }
    )

@app.get("/sites/{site_id}", response_class=HTMLResponse)
def site_detail_page(request: Request, site_id: int):
    conn = get_connection()
    site = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not site:
        conn.close()
        raise HTTPException(status_code=404, detail="Website not found")

    keywords = conn.execute("SELECT * FROM keywords WHERE site_id = ? ORDER BY current_position ASC, id ASC", (site_id,)).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="site_detail.html",
        context={
            "active_page": "sites",
            "site": site,
            "keywords": keywords
        }
    )

@app.get("/rank-tracker", response_class=HTMLResponse)
def rank_tracker_page(request: Request, site_id: Optional[int] = None):
    conn = get_connection()
    sites = conn.execute("SELECT id, name, domain FROM sites ORDER BY id ASC").fetchall()

    if site_id:
        keywords = conn.execute("""
            SELECT k.*, s.domain, s.name as site_name
            FROM keywords k
            JOIN sites s ON s.id = k.site_id
            WHERE k.site_id = ?
            ORDER BY k.current_position ASC, k.id ASC
        """, (site_id,)).fetchall()
    else:
        keywords = conn.execute("""
            SELECT k.*, s.domain, s.name as site_name
            FROM keywords k
            JOIN sites s ON s.id = k.site_id
            ORDER BY k.current_position ASC, k.id ASC
        """).fetchall()

    top_10 = sum(1 for kw in keywords if 0 < (kw["current_position"] or 0) <= 10)
    top_20 = sum(1 for kw in keywords if 10 < (kw["current_position"] or 0) <= 20)
    top_50 = sum(1 for kw in keywords if 20 < (kw["current_position"] or 0) <= 50)
    beyond_50 = sum(1 for kw in keywords if (kw["current_position"] or 0) == 0 or (kw["current_position"] or 0) > 50)

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="rank_tracker.html",
        context={
            "active_page": "ranks",
            "sites": sites,
            "keywords": keywords,
            "selected_site_id": site_id,
            "chart_data": {
                "top_10": top_10,
                "top_20": top_20,
                "top_50": top_50,
                "beyond_50": beyond_50
            }
        }
    )

@app.get("/content-generator", response_class=HTMLResponse)
def content_generator_page(request: Request, site_id: Optional[int] = None):
    conn = get_connection()
    sites = conn.execute("SELECT id, name, domain FROM sites ORDER BY id ASC").fetchall()
    articles = conn.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="content_generator.html",
        context={
            "active_page": "content",
            "sites": sites,
            "articles": articles,
            "selected_site_id": site_id or (sites[0]["id"] if sites else None)
        }
    )

@app.get("/indexer", response_class=HTMLResponse)
def indexer_page(request: Request):
    conn = get_connection()
    sites = conn.execute("SELECT id, name, domain, sitemap_url FROM sites ORDER BY id ASC").fetchall()
    logs = conn.execute("SELECT * FROM indexing_logs ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="indexer.html",
        context={
            "active_page": "indexer",
            "sites": sites,
            "logs": logs
        }
    )

@app.get("/health-audit", response_class=HTMLResponse)
def health_audit_page(request: Request, site_id: Optional[int] = None):
    conn = get_connection()
    sites = conn.execute("SELECT id, name, domain FROM sites ORDER BY id ASC").fetchall()
    selected_id = site_id or (sites[0]["id"] if sites else None)

    audit = None
    if selected_id:
        audit_row = conn.execute("""
            SELECT * FROM health_audits
            WHERE site_id = ?
            ORDER BY id DESC LIMIT 1
        """, (selected_id,)).fetchone()
        if audit_row:
            import json
            audit = dict(audit_row)
            audit["score"] = audit_row["overall_score"]
            audit["issues"] = json.loads(audit_row["issues_json"] or "[]")
        else:
            try:
                audit = audit_site_health(selected_id)
            except Exception:
                pass
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="technical_audit.html",
        context={
            "active_page": "audit",
            "sites": sites,
            "audit": audit,
            "selected_site_id": selected_id
        }
    )

# ----------------- FORM ACTIONS & API -----------------

@app.post("/api/sites")
def create_site_action(
    name: str = Form(...),
    domain: str = Form(...),
    city: str = Form("تبریز"),
    category: str = Form("خدماتی"),
    sitemap_url: Optional[str] = Form(None)
):
    clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sites (name, domain, city, category, sitemap_url)
            VALUES (?, ?, ?, ?, ?)
        """, (name, clean_domain, city, category, sitemap_url))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"خطا در ثبت دامنه: {str(e)}")
    conn.close()
    return RedirectResponse("/sites", status_code=303)

@app.post("/api/sites/{site_id}/delete")
def delete_site_action(site_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/sites", status_code=303)

@app.post("/api/sites/{site_id}/keywords")
def add_keyword_action(site_id: int, keyword: str = Form(...), target_url: Optional[str] = Form(None)):
    conn = get_connection()
    conn.execute("""
        INSERT INTO keywords (site_id, keyword, target_url, current_position, best_position, previous_position)
        VALUES (?, ?, ?, 0, 0, 0)
    """, (site_id, keyword, target_url))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/sites/{site_id}", status_code=303)

@app.post("/api/keywords/{keyword_id}/delete")
def delete_keyword_action(keyword_id: int):
    conn = get_connection()
    row = conn.execute("SELECT site_id FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
    site_id = row["site_id"] if row else None
    conn.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
    conn.commit()
    conn.close()
    if site_id:
        return RedirectResponse(f"/sites/{site_id}", status_code=303)
    return RedirectResponse("/rank-tracker", status_code=303)

@app.post("/api/keywords/{keyword_id}/check-rank")
def check_single_rank_action(keyword_id: int):
    update_keyword_rank(keyword_id)
    return RedirectResponse("/rank-tracker", status_code=303)

@app.post("/api/sites/{site_id}/check-ranks")
def check_site_ranks_action(site_id: int):
    update_all_site_ranks(site_id)
    return RedirectResponse(f"/sites/{site_id}", status_code=303)

@app.post("/api/check-all-ranks")
def check_all_ranks_action(site_id: Optional[int] = Form(None)):
    conn = get_connection()
    if site_id:
        update_all_site_ranks(site_id)
    else:
        all_sites = conn.execute("SELECT id FROM sites").fetchall()
        for s in all_sites:
            update_all_site_ranks(s["id"])
    conn.close()
    target = f"/rank-tracker?site_id={site_id}" if site_id else "/rank-tracker"
    return RedirectResponse(target, status_code=303)

@app.post("/api/generate-content")
def generate_content_action(
    site_id: int = Form(...),
    topic: str = Form(...),
    brand: str = Form("سامسونگ"),
    city: str = Form("تبریز")
):
    generate_seo_article(site_id, topic, brand, city)
    return RedirectResponse(f"/content-generator?site_id={site_id}", status_code=303)

@app.post("/api/submit-indexing")
def submit_indexing_action(site_id: int = Form(...), urls: str = Form(...)):
    url_list = [u.strip() for u in urls.strip().split("\n") if u.strip()]
    if url_list:
        submit_urls_for_indexing(site_id, url_list)
    return RedirectResponse("/indexer", status_code=303)

@app.post("/api/index-sitemap")
def index_sitemap_action(site_id: int = Form(...)):
    conn = get_connection()
    site = conn.execute("SELECT domain, sitemap_url FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    if site:
        target = site["sitemap_url"] or f"https://{site['domain']}/sitemap.xml"
        urls = fetch_sitemap_urls(target, max_urls=30)
        if urls:
            submit_urls_for_indexing(site_id, urls)
    return RedirectResponse("/indexer", status_code=303)

@app.post("/api/run-audit")
def run_audit_action(site_id: int = Form(...)):
    audit_site_health(site_id)
    return RedirectResponse(f"/health-audit?site_id={site_id}", status_code=303)
