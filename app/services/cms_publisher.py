import os
import json
import base64
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from app.database import get_connection
from app.services.ftp_deployer import FTPDeployer

class CMSPublisher:
    """
    Automated Multi-CMS Article Publishing Service.
    Supports WordPress REST API and Local / Remote ASP.NET (.aspx/.html) deployments.
    """
    def __init__(self, site_id: int):
        self.site_id = site_id

    def publish_to_wordpress(self, title: str, content_html: str, status: str = "draft") -> Dict[str, Any]:
        conn = get_connection()
        site = conn.execute("SELECT wp_api_url, wp_user, wp_app_pass FROM sites WHERE id = ?", (self.site_id,)).fetchone()
        conn.close()

        if not site or not site["wp_api_url"] or not site["wp_user"] or not site["wp_app_pass"]:
            return {
                "success": False,
                "message": "اطلاعات اتصال به وردپرس (آدرس API، نام کاربری و Application Password) در مشخصات این سایت تنظیم نشده است."
            }

        endpoint = site["wp_api_url"].rstrip("/") + "/wp-json/wp/v2/posts"
        payload = json.dumps({
            "title": title,
            "content": content_html,
            "status": status
        }).encode("utf-8")

        auth_str = f"{site['wp_user']}:{site['wp_app_pass']}"
        b64_auth = base64.b64encode(auth_str.encode()).decode("ascii")

        req = urllib.request.Request(endpoint, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {b64_auth}",
            "User-Agent": "SEO-Command-Center"
        })

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode())
                post_link = res_data.get("link", "")
                return {
                    "success": True,
                    "message": f"مقاله با موفقیت در وردپرس ارسال شد. (وضعیت: {status})",
                    "post_id": res_data.get("id"),
                    "link": post_link
                }
        except Exception as e:
            return {"success": False, "message": f"خطا در ارسال به وردپرس: {str(e)}"}

    def publish_to_local_project(self, title: str, slug: str, content_html: str, faq_schema_json: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates an ASP.NET (.aspx) or HTML article inside the local project source path.
        """
        conn = get_connection()
        site = conn.execute("SELECT project_path, domain, city FROM sites WHERE id = ?", (self.site_id,)).fetchone()
        conn.close()

        if not site or not site["project_path"] or not os.path.exists(site["project_path"]):
            return {
                "success": False,
                "message": "مسیر پوشه سورس محلی این پروژه معتبر یا قابل دسترس نیست."
            }

        articles_dir = os.path.join(site["project_path"], "Articles")
        os.makedirs(articles_dir, exist_ok=True)

        clean_slug = (slug or "seo-article").replace(" ", "-").replace("/", "")
        file_path = os.path.join(articles_dir, f"{clean_slug}.html")

        # Full high-converting SEO HTML template with Schema
        full_html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {site['city']}</title>
    <meta name="robots" content="index, follow">
    {f'<script type="application/ld+json">{faq_schema_json}</script>' if faq_schema_json else ''}
    <style>
        body {{ font-family: Tahoma, 'Segoe UI', sans-serif; line-height: 1.9; color: #2d3748; max-width: 900px; margin: 30px auto; padding: 0 20px; }}
        h1 {{ color: #1a202c; border-bottom: 2px solid #319795; padding-bottom: 12px; }}
        h2 {{ color: #2c5282; margin-top: 30px; }}
        .cta-box {{ background: #ebf8ff; border: 2px dashed #3182ce; padding: 20px; border-radius: 12px; margin: 30px 0; text-align: center; }}
    </style>
</head>
<body>
    <article>
        <h1>{title}</h1>
        {content_html}
    </article>
</body>
</html>"""

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_html)

            return {
                "success": True,
                "message": f"فایل مقاله با موفقیت در پوشه سورس پروژه ایجاد شد.",
                "file_path": file_path
            }
        except Exception as e:
            return {"success": False, "message": f"خطا در ایجاد فایل مقاله: {str(e)}"}
