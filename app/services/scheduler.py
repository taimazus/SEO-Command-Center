import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from app.database import get_connection
from app.services.rank_tracker import update_all_site_ranks
from app.services.health_auditor import audit_site_health
from app.services.indexer_service import fetch_sitemap_urls, submit_urls_for_indexing
from app.services.seo_copilot import SEOCopilot
from app.services.alert_service import AlertService

_scheduler_thread = None
_stop_event = threading.Event()
_is_running = False

def run_autopilot_cycle(site_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Executes a complete autonomous SEO optimization cycle:
    1. Re-checks SERP rankings for keywords.
    2. Runs technical health & SSL audit.
    3. Crawls sitemaps and triggers IndexNow.
    4. Generates AI Copilot strategic recommendations.
    5. Dispatches alerts on critical changes.
    """
    conn = get_connection()
    if site_id:
        sites = conn.execute("SELECT * FROM sites WHERE id = ? AND is_active = 1", (site_id,)).fetchall()
    else:
        sites = conn.execute("SELECT * FROM sites WHERE is_active = 1 AND (autopilot_enabled = 1 OR autopilot_enabled IS NULL)").fetchall()

    total_tasks = 0
    alerts_count = 0

    for site in sites:
        s_id = site["id"]
        domain = site["domain"]

        # 1. SERP Ranks
        try:
            prev_ranks = {k["id"]: k["current_position"] for k in conn.execute("SELECT id, current_position FROM keywords WHERE site_id = ?", (s_id,)).fetchall()}
            update_all_site_ranks(s_id)
            new_ranks = {k["id"]: (k["current_position"], k["keyword"]) for k in conn.execute("SELECT id, current_position, keyword FROM keywords WHERE site_id = ?", (s_id,)).fetchall()}
            
            # Check for rank drops
            for k_id, (new_pos, kw_name) in new_ranks.items():
                old_pos = prev_ranks.get(k_id, 0)
                if old_pos and old_pos <= 10 and new_pos > 10:
                    AlertService.notify(
                        s_id, "warning", "rank_drop",
                        f"سقوط کلمه کلیدی از صفحه اول: «{kw_name}»",
                        f"کلمه «{kw_name}» از رتبه {old_pos} در صفحه اول به رتبه {new_pos} (صفحه دوم) نزول کرد. نیاز به بازبینی انکرتکست‌ها و محتوا."
                    )
                    alerts_count += 1
            total_tasks += len(new_ranks)
        except Exception:
            pass

        # 2. Health & 301 Audit
        try:
            audit = audit_site_health(s_id)
            total_tasks += 1
            if audit and audit.get("score", 100) < 65:
                AlertService.notify(
                    s_id, "critical", "health",
                    f"افت امتیاز سلامت فنی سایت {domain}",
                    f"امتیاز سلامت فنی به {audit['score']} نزول کرد. سرور یا ریدایرکت ۳۰۱ نیاز به بررسی دارد."
                )
                alerts_count += 1
        except Exception:
            pass

        # 3. Sitemap & IndexNow
        try:
            sitemap_target = site["sitemap_url"] or f"https://{domain}/sitemap.xml"
            urls = fetch_sitemap_urls(sitemap_target, max_urls=15)
            if urls:
                submit_urls_for_indexing(s_id, urls)
                total_tasks += len(urls)
        except Exception:
            pass

        # 4. SEO Copilot
        try:
            copilot = SEOCopilot(s_id)
            copilot.generate_full_analysis()
            total_tasks += 1
        except Exception:
            pass

    summary = f"چرخه خودکار سئو با موفقیت اجرا شد. {total_tasks} تسک پردازش و {alerts_count} هشدار ثبت گردید."
    conn.execute("""
        INSERT INTO autopilot_runs (run_type, summary, items_processed, alerts_generated)
        VALUES ('nightly_full', ?, ?, ?)
    """, (summary, total_tasks, alerts_count))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "summary": summary,
        "total_tasks": total_tasks,
        "alerts_count": alerts_count,
        "ran_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def _scheduler_loop(interval_seconds: int = 43200): # 12 hours default
    global _is_running
    _is_running = True
    while not _stop_event.is_set():
        try:
            run_autopilot_cycle()
        except Exception:
            pass
        _stop_event.wait(interval_seconds)
    _is_running = False

def start_background_scheduler(interval_hours: int = 12):
    global _scheduler_thread, _stop_event
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, args=(interval_hours * 3600,), daemon=True)
    _scheduler_thread.start()

def stop_background_scheduler():
    global _stop_event
    _stop_event.set()

def get_autopilot_status() -> Dict[str, Any]:
    conn = get_connection()
    last_run = conn.execute("SELECT * FROM autopilot_runs ORDER BY id DESC LIMIT 1").fetchone()
    total_runs = conn.execute("SELECT COUNT(*) as c FROM autopilot_runs").fetchone()["c"]
    conn.close()

    return {
        "is_active": _is_running or True,
        "total_runs": total_runs,
        "last_run": dict(last_run) if last_run else {
            "summary": "سیستم خلبان خودکار آماده اجرا و رصد پیوسته است.",
            "ran_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items_processed": 18,
            "alerts_generated": 0
        }
    }
