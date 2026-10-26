import os
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, get_connection, DB_DIR
from app.services.rank_tracker import update_keyword_rank, update_all_site_ranks
from app.services.health_auditor import audit_site_health
from app.services.ai_content import generate_seo_article
from app.services.indexer_service import submit_urls_for_indexing, fetch_sitemap_urls
from app.services.source_doctor import SourceDoctor
from app.services.gsc_service import GSCService, CREDENTIALS_FILE

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="SEO Command Center",
    description="Multi-Tenant SEO Management, Source Doctor, SERP Rank Tracking & AI Content Autopilot",
    version="2.1.0",
    lifespan=lifespan
)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_site_context(request: Request, explicit_site_id: Optional[int] = None):
    """
    Resolves the global active site from cookie or query param, falling back to the first site.
    Returns: (all_sites, current_site, active_id)
    """
    conn = get_connection()
    all_sites = conn.execute("SELECT * FROM sites ORDER BY id ASC").fetchall()
    
    cookie_site_id = request.cookies.get("active_site_id")
    active_id = None
    if explicit_site_id is not None:
        active_id = explicit_site_id
    elif cookie_site_id and cookie_site_id.isdigit():
        active_id = int(cookie_site_id)
    
    site_map = {s["id"]: s for s in all_sites}
    if active_id not in site_map and all_sites:
        active_id = all_sites[0]["id"]
    
    current_site = site_map.get(active_id) if active_id else None
    conn.close()
    return all_sites, current_site, active_id

# ----------------- WEB PAGES -----------------

@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    all_sites, current_site, active_id = get_site_context(request)
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
            "all_sites": all_sites,
            "current_site": current_site,
            "active_site_id": active_id,
            "stats": stats,
            "sites": sites,
            "top_keywords": keywords
        }
    )

@app.get("/sites", response_class=HTMLResponse)
def list_sites_page(request: Request):
    all_sites, current_site, active_id = get_site_context(request)
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
            "all_sites": all_sites,
            "current_site": current_site,
            "active_site_id": active_id,
            "sites": sites
        }
    )

@app.get("/sites/{site_id}", response_class=HTMLResponse)
def site_detail_page(request: Request, site_id: int):
    all_sites, current_site, active_id = get_site_context(request, site_id)
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
            "all_sites": all_sites,
            "current_site": current_site,
            "active_site_id": active_id,
            "site": site,
            "keywords": keywords
        }
    )

@app.get("/rank-tracker", response_class=HTMLResponse)
def rank_tracker_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id = get_site_context(request, site_id)
    conn = get_connection()

    if active_id:
        keywords = conn.execute("""
            SELECT k.*, s.domain, s.name as site_name
            FROM keywords k
            JOIN sites s ON s.id = k.site_id
            WHERE k.site_id = ?
            ORDER BY k.current_position ASC, k.id ASC
        """, (active_id,)).fetchall()
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
            "all_sites": all_sites,
            "current_site": current_site,
            "sites": all_sites,
            "keywords": keywords,
            "selected_site_id": active_id,
            "chart_data": {
                "top_10": top_10,
                "top_20": top_20,
                "top_50": top_50,
                "beyond_50": beyond_50
            }
        }
    )

@app.get("/source-doctor", response_class=HTMLResponse)
def source_doctor_page(request: Request, site_id: Optional[int] = None, project_path: Optional[str] = None):
    all_sites, current_site, active_id = get_site_context(request, site_id)
    
    target_path = project_path
    if not target_path and current_site:
        target_path = current_site["project_path"] or r"F:\Projects\TabrizTv"
    elif not target_path:
        target_path = r"F:\Projects\TabrizTv"

    scan_result = None
    manifest_data = None
    if target_path and os.path.exists(target_path):
        doctor = SourceDoctor(target_path)
        scan_result = doctor.analyze()
        if scan_result["success"]:
            manifest_data = doctor.generate_publish_manifest(days_modified=14)
    elif target_path:
        scan_result = {
            "success": False,
            "error": f"مسیر '{target_path}' یافت نشد. لطفاً آدرس را بررسی نمایید.",
            "project_path": target_path
        }

    return templates.TemplateResponse(
        request=request,
        name="source_doctor.html",
        context={
            "active_page": "doctor",
            "all_sites": all_sites,
            "current_site": current_site,
            "selected_site_id": active_id,
            "project_path": target_path,
            "scan_result": scan_result,
            "manifest_data": manifest_data
        }
    )

@app.get("/gsc-integration", response_class=HTMLResponse)
def gsc_integration_page(request: Request, site_id: Optional[int] = None, imported: Optional[int] = None):
    all_sites, current_site, active_id = get_site_context(request, site_id)
    gsc_service = GSCService()
    gsc_data = gsc_service.get_performance_summary(site_id=active_id or 1)

    return templates.TemplateResponse(
        request=request,
        name="gsc_integration.html",
        context={
            "active_page": "gsc",
            "all_sites": all_sites,
            "current_site": current_site,
            "selected_site_id": active_id,
            "gsc_data": gsc_data,
            "just_imported": bool(imported)
        }
    )

@app.get("/content-generator", response_class=HTMLResponse)
def content_generator_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id = get_site_context(request, site_id)
    conn = get_connection()
    articles = conn.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="content_generator.html",
        context={
            "active_page": "content",
            "all_sites": all_sites,
            "current_site": current_site,
            "sites": all_sites,
            "articles": articles,
            "selected_site_id": active_id
        }
    )

@app.get("/indexer", response_class=HTMLResponse)
def indexer_page(request: Request):
    all_sites, current_site, active_id = get_site_context(request)
    conn = get_connection()
    logs = conn.execute("SELECT * FROM indexing_logs ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="indexer.html",
        context={
            "active_page": "indexer",
            "all_sites": all_sites,
            "current_site": current_site,
            "sites": all_sites,
            "selected_site_id": active_id,
            "logs": logs
        }
    )

@app.get("/health-audit", response_class=HTMLResponse)
def health_audit_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id = get_site_context(request, site_id)
    conn = get_connection()

    audit = None
    if active_id:
        audit_row = conn.execute("""
            SELECT * FROM health_audits
            WHERE site_id = ?
            ORDER BY id DESC LIMIT 1
        """, (active_id,)).fetchone()
        if audit_row:
            import json
            audit = dict(audit_row)
            audit["score"] = audit_row["overall_score"]
            audit["issues"] = json.loads(audit_row["issues_json"] or "[]")
        else:
            try:
                audit = audit_site_health(active_id)
            except Exception:
                pass
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="technical_audit.html",
        context={
            "active_page": "audit",
            "all_sites": all_sites,
            "current_site": current_site,
            "sites": all_sites,
            "audit": audit,
            "selected_site_id": active_id
        }
    )

# ----------------- FORM ACTIONS & API -----------------

@app.post("/api/sites/{site_id}/update-path")
def update_site_path_action(site_id: int, project_path: str = Form(...)):
    clean_path = project_path.strip()
    conn = get_connection()
    conn.execute("UPDATE sites SET project_path = ? WHERE id = ?", (clean_path, site_id))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/source-doctor?site_id={site_id}&project_path={clean_path}", status_code=303)

@app.post("/api/gsc/import-csv")
async def import_gsc_csv_action(file: UploadFile = File(...), site_id: int = Form(...)):
    file_bytes = await file.read()
    gsc_service = GSCService()
    gsc_service.import_gsc_csv(site_id, file_bytes, file.filename)
    return RedirectResponse(f"/gsc-integration?site_id={site_id}&imported=1", status_code=303)

@app.post("/api/gsc/upload-credentials")
async def upload_gsc_credentials_action(credentials_file: UploadFile = File(...), site_id: int = Form(...)):
    content = await credentials_file.read()
    with open(CREDENTIALS_FILE, "wb") as f:
        f.write(content)
    return RedirectResponse(f"/gsc-integration?site_id={site_id}&connected=1", status_code=303)

@app.post("/api/source-doctor/auto-fix")
def source_doctor_autofix_action(project_path: str = Form(...)):
    doctor = SourceDoctor(project_path)
    doctor.auto_fix()
    return RedirectResponse(f"/source-doctor?project_path={project_path}", status_code=303)

@app.post("/api/source-doctor/export-zip")
def source_doctor_export_zip_action(project_path: str = Form(...)):
    doctor = SourceDoctor(project_path)
    zip_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")
    os.makedirs(zip_dir, exist_ok=True)
    zip_path = os.path.join(zip_dir, "TabrizTv_Publish_Package.zip")
    doctor.create_publish_zip(zip_path, days_modified=14)
    if os.path.exists(zip_path):
        return FileResponse(zip_path, filename="Publish_Package.zip", media_type="application/zip")
    return RedirectResponse(f"/source-doctor?project_path={project_path}", status_code=303)

@app.post("/api/sites")
def create_site_action(
    name: str = Form(...),
    domain: str = Form(...),
    city: str = Form("تبریز"),
    category: str = Form("خدماتی"),
    sitemap_url: Optional[str] = Form(None),
    project_path: Optional[str] = Form(None)
):
    clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sites (name, domain, city, category, sitemap_url, project_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, clean_domain, city, category, sitemap_url, project_path))
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
