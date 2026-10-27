import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File, Response
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, get_connection, DB_DIR
from app.services.rank_tracker import update_keyword_rank, update_all_site_ranks
from app.services.health_auditor import audit_site_health
from app.services.ai_content import generate_seo_article, get_suggested_topics_for_site
from app.services.indexer_service import submit_urls_for_indexing, fetch_sitemap_urls
from app.services.source_doctor import SourceDoctor
from app.services.gsc_service import GSCService, CREDENTIALS_FILE
from app.services.ftp_deployer import FTPDeployer
from app.services.seo_copilot import SEOCopilot
from app.services.alert_service import AlertService
from app.services.cms_publisher import CMSPublisher
from app.services.report_generator import ReportGenerator
from app.services.scheduler import start_background_scheduler, stop_background_scheduler, run_autopilot_cycle, get_autopilot_status

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_background_scheduler(interval_hours=12)
    yield
    stop_background_scheduler()

app = FastAPI(
    title="SEO Command Center",
    description="Multi-Tenant Autonomous SEO Specialist, Source Doctor, SERP Rank Tracking & Copilot",
    version="2.2.0",
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
    Returns: (all_sites, current_site, active_id, unread_alerts_count)
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
    
    # Query unread alerts count
    unread_alerts = conn.execute("SELECT COUNT(*) AS c FROM system_alerts WHERE is_read = 0").fetchone()
    unread_alerts_count = unread_alerts["c"] if unread_alerts else 0
    
    conn.close()
    return all_sites, current_site, active_id, unread_alerts_count

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

# ----------------- WEB PAGES -----------------

@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request)
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

    # Copilot Insights & Autopilot status for dashboard with resilient boundary
    try:
        copilot = SEOCopilot(active_id or 1)
        copilot_insights = copilot.generate_full_analysis()
    except Exception as e:
        logging.error(f"Error generating copilot insights on dashboard: {e}")
        copilot_insights = {"quick_wins": [], "ctr_opportunities": [], "content_gaps": [], "tech_priorities": [], "seo_authority_score": 85}

    autopilot_status = get_autopilot_status()

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
            "unread_alerts_count": unread_alerts_count,
            "stats": stats,
            "sites": sites,
            "top_keywords": keywords,
            "copilot_insights": copilot_insights,
            "autopilot_status": autopilot_status
        }
    )

@app.get("/copilot", response_class=HTMLResponse)
def copilot_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    try:
        copilot = SEOCopilot(active_id or 1)
        copilot_data = copilot.generate_full_analysis()
    except Exception as e:
        logging.error(f"Error generating copilot analysis for site {active_id}: {e}")
        copilot_data = {"quick_wins": [], "ctr_opportunities": [], "content_gaps": [], "tech_priorities": [], "seo_authority_score": 85}

    return templates.TemplateResponse(
        request=request,
        name="seo_copilot.html",
        context={
            "active_page": "copilot",
            "all_sites": all_sites,
            "current_site": current_site,
            "selected_site_id": active_id,
            "unread_alerts_count": unread_alerts_count,
            "copilot_data": copilot_data
        }
    )

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    generator = ReportGenerator(active_id or 1)
    report_data = generator.build_report_data()

    return templates.TemplateResponse(
        request=request,
        name="report_detail.html",
        context={
            "active_page": "reports",
            "all_sites": all_sites,
            "current_site": current_site,
            "selected_site_id": active_id,
            "unread_alerts_count": unread_alerts_count,
            "report": report_data
        }
    )

@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    conn = get_connection()
    if active_id:
        alerts = conn.execute("""
            SELECT a.*, s.domain, s.name as site_name
            FROM system_alerts a
            LEFT JOIN sites s ON s.id = a.site_id
            WHERE a.site_id = ?
            ORDER BY a.id DESC LIMIT 30
        """, (active_id,)).fetchall()
    else:
        alerts = conn.execute("""
            SELECT a.*, s.domain, s.name as site_name
            FROM system_alerts a
            LEFT JOIN sites s ON s.id = a.site_id
            ORDER BY a.id DESC LIMIT 30
        """).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="alerts.html",
        context={
            "active_page": "alerts",
            "all_sites": all_sites,
            "current_site": current_site,
            "selected_site_id": active_id,
            "unread_alerts_count": unread_alerts_count,
            "alerts": [dict(a) for a in alerts]
        }
    )

@app.get("/sites", response_class=HTMLResponse)
def list_sites_page(request: Request):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request)
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
            "unread_alerts_count": unread_alerts_count,
            "sites": sites
        }
    )

@app.get("/sites/{site_id}", response_class=HTMLResponse)
def site_detail_page(request: Request, site_id: int):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
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
            "unread_alerts_count": unread_alerts_count,
            "site": site,
            "keywords": keywords
        }
    )

@app.get("/rank-tracker", response_class=HTMLResponse)
def rank_tracker_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
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
            "unread_alerts_count": unread_alerts_count,
            "chart_data": {
                "top_10": top_10,
                "top_20": top_20,
                "top_50": top_50,
                "beyond_50": beyond_50
            }
        }
    )

@app.get("/source-doctor", response_class=HTMLResponse)
def source_doctor_page(
    request: Request,
    site_id: Optional[int] = None,
    project_path: Optional[str] = None,
    ftp_message: Optional[str] = None,
    ftp_success: Optional[int] = None
):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    
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
            "manifest_data": manifest_data,
            "unread_alerts_count": unread_alerts_count,
            "ftp_message": ftp_message,
            "ftp_success": bool(ftp_success) if ftp_success is not None else None
        }
    )

@app.get("/gsc-integration", response_class=HTMLResponse)
def gsc_integration_page(request: Request, site_id: Optional[int] = None, imported: Optional[int] = None, connected: Optional[int] = None, tested: Optional[int] = None, sitemap_msg: Optional[str] = None, sitemap_success: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    gsc_service = GSCService()
    target_domain = current_site["domain"] if current_site else ""
    connection_test = gsc_service.test_connection(target_domain)
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
            "connection_test": connection_test,
            "just_imported": bool(imported),
            "just_connected": bool(connected),
            "just_tested": bool(tested),
            "sitemap_msg": sitemap_msg,
            "sitemap_success": bool(sitemap_success),
            "unread_alerts_count": unread_alerts_count
        }
    )

@app.get("/content-generator", response_class=HTMLResponse)
def content_generator_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
    conn = get_connection()
    articles = conn.execute("SELECT * FROM articles WHERE site_id = ? ORDER BY id DESC LIMIT 20", (active_id,)).fetchall()
    conn.close()
    suggested_topics = get_suggested_topics_for_site(active_id)

    return templates.TemplateResponse(
        request=request,
        name="content_generator.html",
        context={
            "active_page": "content",
            "all_sites": all_sites,
            "current_site": current_site,
            "sites": all_sites,
            "articles": articles,
            "suggested_topics": suggested_topics,
            "selected_site_id": active_id,
            "unread_alerts_count": unread_alerts_count
        }
    )

@app.get("/indexer", response_class=HTMLResponse)
def indexer_page(request: Request):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request)
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
            "logs": logs,
            "unread_alerts_count": unread_alerts_count
        }
    )

@app.get("/health-audit", response_class=HTMLResponse)
def health_audit_page(request: Request, site_id: Optional[int] = None):
    all_sites, current_site, active_id, unread_alerts_count = get_site_context(request, site_id)
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
            except Exception as e:
                import logging
                logging.warning(f"Could not auto-run health audit for site {active_id}: {e}")
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
            "selected_site_id": active_id,
            "unread_alerts_count": unread_alerts_count
        }
    )

# ----------------- AUTONOMOUS ACTION APIS -----------------

@app.post("/api/autopilot/run-now")
def autopilot_run_now_action(site_id: Optional[int] = Form(None)):
    run_autopilot_cycle(site_id)
    target = f"/copilot?site_id={site_id}" if site_id else "/"
    return RedirectResponse(target, status_code=303)

@app.post("/api/alerts/mark-read")
def mark_alerts_read_action():
    AlertService.mark_all_as_read()
    return RedirectResponse("/alerts", status_code=303)

@app.post("/api/alerts/test-telegram")
def test_telegram_action(telegram_bot_token: str = Form(...), telegram_chat_id: str = Form(...)):
    sent = AlertService.send_telegram(
        telegram_bot_token,
        telegram_chat_id,
        "🔔 *پیام آزمایشی مرکز فرماندهی سئو*\n\nاتصال بات تلگرام با موفقیت تایید شد. هشدارهای رصد رتبه‌ها و سلامت سایت به این گفتگو ارسال خواهند شد."
    )
    return RedirectResponse("/alerts", status_code=303)

@app.post("/api/sites/{site_id}/update-telegram")
def update_telegram_action(site_id: int, telegram_bot_token: str = Form(""), telegram_chat_id: str = Form("")):
    conn = get_connection()
    conn.execute("UPDATE sites SET telegram_bot_token = ?, telegram_chat_id = ? WHERE id = ?", (telegram_bot_token.strip(), telegram_chat_id.strip(), site_id))
    conn.commit()
    conn.close()
    return RedirectResponse("/alerts", status_code=303)

@app.post("/api/sites/{site_id}/update-ftp")
def update_site_ftp_action(
    site_id: int,
    ftp_host: str = Form(...),
    ftp_port: int = Form(21),
    ftp_user: str = Form(...),
    ftp_pass: str = Form(...),
    ftp_root: str = Form("/httpdocs")
):
    conn = get_connection()
    conn.execute("""
        UPDATE sites SET ftp_host = ?, ftp_port = ?, ftp_user = ?, ftp_pass = ?, ftp_root = ?
        WHERE id = ?
    """, (ftp_host.strip(), ftp_port, ftp_user.strip(), ftp_pass.strip(), ftp_root.strip(), site_id))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/source-doctor?site_id={site_id}", status_code=303)

@app.post("/api/sites/{site_id}/test-ftp")
def test_site_ftp_action(
    site_id: int,
    ftp_host: str = Form(...),
    ftp_port: int = Form(21),
    ftp_user: str = Form(...),
    ftp_pass: str = Form(...),
    ftp_root: str = Form("/httpdocs")
):
    deployer = FTPDeployer(ftp_host, ftp_port, ftp_user, ftp_pass, ftp_root)
    result = deployer.test_connection()
    msg = result["message"]
    success_flag = 1 if result["success"] else 0
    return RedirectResponse(f"/source-doctor?site_id={site_id}&ftp_message={msg}&ftp_success={success_flag}", status_code=303)

@app.post("/api/source-doctor/deploy-ftp")
def deploy_ftp_action(project_path: str = Form(...), site_id: int = Form(...)):
    conn = get_connection()
    site = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()

    if not site or not site["ftp_host"] or not site["ftp_user"]:
        return RedirectResponse(f"/source-doctor?site_id={site_id}&ftp_message=اطلاعات+FTP+هاست+تنظیم+نشده+است&ftp_success=0", status_code=303)

    doctor = SourceDoctor(project_path)
    manifest = doctor.generate_publish_manifest(days_modified=14)
    
    deployer = FTPDeployer(site["ftp_host"], site["ftp_port"] or 21, site["ftp_user"], site["ftp_pass"], site["ftp_root"] or "/httpdocs")
    res = deployer.deploy_manifest_files(project_path, manifest["manifest"])

    msg = res["message"]
    success_flag = 1 if res["success"] else 0
    return RedirectResponse(f"/source-doctor?site_id={site_id}&ftp_message={msg}&ftp_success={success_flag}", status_code=303)

@app.post("/api/sites/{site_id}/update-wp")
def update_site_wp_action(
    site_id: int,
    wp_api_url: str = Form(""),
    wp_user: str = Form(""),
    wp_app_pass: str = Form("")
):
    conn = get_connection()
    conn.execute("""
        UPDATE sites SET wp_api_url = ?, wp_user = ?, wp_app_pass = ?
        WHERE id = ?
    """, (wp_api_url.strip(), wp_user.strip(), wp_app_pass.strip(), site_id))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/content-generator?site_id={site_id}", status_code=303)

@app.post("/api/articles/{article_id}/publish-wp")
def publish_article_wp_action(article_id: int):
    conn = get_connection()
    art = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    if art:
        pub = CMSPublisher(art["site_id"])
        pub.publish_to_wordpress(art["title"], art["content_html"], status="draft")
    return RedirectResponse(f"/content-generator?site_id={art['site_id']}", status_code=303)

@app.post("/api/articles/{article_id}/publish-local")
def publish_article_local_action(article_id: int):
    conn = get_connection()
    art = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    if art:
        pub = CMSPublisher(art["site_id"])
        pub.publish_to_local_project(art["title"], art["slug"], art["content_html"])
    return RedirectResponse(f"/content-generator?site_id={art['site_id']}", status_code=303)

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
    gsc_service = GSCService()
    conn = get_connection()
    site = conn.execute("SELECT domain FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    if site:
        gsc_service.fetch_live_api_data(site_id, site["domain"])
    return RedirectResponse(f"/gsc-integration?site_id={site_id}&connected=1", status_code=303)

@app.post("/api/gsc/test-connection")
def test_gsc_connection_action(site_id: int = Form(...)):
    gsc_service = GSCService()
    conn = get_connection()
    site = conn.execute("SELECT domain FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    if site:
        gsc_service.fetch_live_api_data(site_id, site["domain"])
    return RedirectResponse(f"/gsc-integration?site_id={site_id}&tested=1", status_code=303)

@app.post("/api/gsc/submit-sitemap")
def submit_gsc_sitemap_action(site_id: int = Form(...), sitemap_url: str = Form(None)):
    gsc_service = GSCService()
    res = gsc_service.submit_sitemap(site_id, sitemap_url)
    import urllib.parse
    msg = urllib.parse.quote(res["message"])
    flag = 1 if res["success"] else 0
    return RedirectResponse(f"/gsc-integration?site_id={site_id}&sitemap_msg={msg}&sitemap_success={flag}", status_code=303)

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
    custom_topic: Optional[str] = Form(None),
    brand: str = Form(""),
    city: str = Form("")
):
    effective_topic = custom_topic.strip() if topic == "custom" and custom_topic and custom_topic.strip() else topic
    generate_seo_article(site_id, effective_topic, brand, city)
    return RedirectResponse(f"/content-generator?site_id={site_id}", status_code=303)

@app.post("/api/articles/{article_id}/delete")
def delete_article_action(article_id: int):
    conn = get_connection()
    art = conn.execute("SELECT site_id FROM articles WHERE id = ?", (article_id,)).fetchone()
    site_id = art["site_id"] if art else 1
    conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/content-generator?site_id={site_id}", status_code=303)

@app.get("/api/utils/browse-folder")
def browse_folder_api(path: Optional[str] = None):
    import string
    drives = []
    for letter in string.ascii_uppercase:
        drive_str = f"{letter}:\\"
        if os.path.exists(drive_str):
            drives.append({"name": f"درایو ({letter}:)", "path": drive_str})
            
    target_path = path.strip() if path and path.strip() else ""
    if not target_path or not os.path.exists(target_path):
        return {
            "current_path": "",
            "parent_path": "",
            "drives": drives,
            "folders": []
        }
        
    norm_path = os.path.abspath(target_path)
    parent = os.path.dirname(norm_path)
    if parent == norm_path:
        parent = ""
        
    folders = []
    try:
        for entry in os.scandir(norm_path):
            try:
                if entry.is_dir() and not entry.name.startswith(".") and not entry.name.startswith("$"):
                    folders.append({
                        "name": entry.name,
                        "path": entry.path
                    })
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError) as e:
        return {
            "current_path": norm_path,
            "parent_path": parent,
            "drives": drives,
            "folders": [],
            "error": f"عدم دسترسی به مسیر: {str(e)}"
        }
        
    folders.sort(key=lambda x: x["name"].lower())
    return {
        "current_path": norm_path,
        "parent_path": parent,
        "drives": drives,
        "folders": folders
    }

@app.post("/api/utils/select-folder-dialog")
def select_folder_dialog_api():
    selected_path = ""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_path = filedialog.askdirectory(title="پوشه سورس پروژه را انتخاب کنید")
        root.destroy()
    except Exception as e:
        logging.error(f"Error opening folder dialog: {e}")
        
    return {"success": bool(selected_path), "path": selected_path}

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
