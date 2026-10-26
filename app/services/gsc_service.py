import os
import json
import csv
import io
import zipfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.database import get_connection, DB_DIR

CREDENTIALS_FILE = os.path.join(DB_DIR, "service_account.json")

class GSCService:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or CREDENTIALS_FILE
        self.is_connected = False
        if os.path.exists(self.credentials_path):
            self.is_connected = True

    def import_gsc_csv(self, site_id: int, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses Google Search Console exported ZIP or CSV file and saves real data.
        """
        imported_queries = []
        conn = get_connection()

        # If it's a zip file (standard GSC Export)
        if filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    for name in z.namelist():
                        if "queries.csv" in name.lower():
                            with z.open(name) as f:
                                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                                for row in reader:
                                    q = row.get("Top queries") or row.get("Query") or row.get("query")
                                    if q:
                                        clicks = int(float(row.get("Clicks", 0)))
                                        impressions = int(float(row.get("Impressions", 0)))
                                        ctr_val = row.get("CTR", "0%").replace("%", "").strip()
                                        ctr = float(ctr_val) if ctr_val else 0.0
                                        pos = round(float(row.get("Position", 0)), 1)
                                        imported_queries.append((site_id, q, clicks, impressions, ctr, pos))
            except Exception as e:
                conn.close()
                return {"success": False, "error": f"خطا در خواندن فایل فشرده کنسول: {str(e)}"}
        else:
            # Single CSV file
            try:
                reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8-sig", errors="ignore")))
                for row in reader:
                    q = row.get("Top queries") or row.get("Query") or row.get("query")
                    if q:
                        clicks = int(float(row.get("Clicks", 0)))
                        impressions = int(float(row.get("Impressions", 0)))
                        ctr_val = row.get("CTR", "0%").replace("%", "").strip()
                        ctr = float(ctr_val) if ctr_val else 0.0
                        pos = round(float(row.get("Position", 0)), 1)
                        imported_queries.append((site_id, q, clicks, impressions, ctr, pos))
            except Exception as e:
                conn.close()
                return {"success": False, "error": f"خطا در پردازش CSV: {str(e)}"}

        if imported_queries:
            # Clear old and insert fresh real queries
            conn.execute("DELETE FROM gsc_queries WHERE site_id = ?", (site_id,))
            conn.executemany("""
                INSERT INTO gsc_queries (site_id, query, clicks, impressions, ctr, position)
                VALUES (?, ?, ?, ?, ?, ?)
            """, imported_queries)
            conn.commit()

        conn.close()
        return {
            "success": True,
            "total_imported": len(imported_queries),
            "message": f"{len(imported_queries)} کلمه کلیدی واقعی از خروجی کنسول گوگل با موفقیت ثبت شد."
        }

    def fetch_live_api_data(self, site_id: int, site_url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Attempts real Google Search Console API fetch using Service Account credentials.
        """
        if not os.path.exists(self.credentials_path):
            return None

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
            creds = service_account.Credentials.from_service_account_file(self.credentials_path, scopes=SCOPES)
            service = build('searchconsole', 'v1', credentials=creds)

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")

            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['query'],
                'rowLimit': 50
            }

            response = service.searchanalytics().query(siteUrl=site_url, body=request_body).execute()
            rows = response.get('rows', [])

            imported_queries = []
            conn = get_connection()
            for r in rows:
                q = r['keys'][0]
                clicks = int(r.get('clicks', 0))
                impressions = int(r.get('impressions', 0))
                ctr = round(float(r.get('ctr', 0)) * 100, 2)
                pos = round(float(r.get('position', 0)), 1)
                imported_queries.append((site_id, q, clicks, impressions, ctr, pos))

            if imported_queries:
                conn.execute("DELETE FROM gsc_queries WHERE site_id = ?", (site_id,))
                conn.executemany("""
                    INSERT INTO gsc_queries (site_id, query, clicks, impressions, ctr, position)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, imported_queries)
                conn.commit()
            conn.close()
            return imported_queries
        except Exception:
            return None

    def get_performance_summary(self, site_id: int, days: int = 28) -> Dict[str, Any]:
        conn = get_connection()
        site = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()

        domain = site["domain"] if site else "tbztvrepair.ir"
        site_name = site["name"] if site else "مرکز تعمیرات تبریز تی‌وی"

        # Check if real data exists in database
        db_queries = conn.execute("""
            SELECT query, clicks, impressions, ctr, position
            FROM gsc_queries
            WHERE site_id = ?
            ORDER BY clicks DESC, impressions DESC
        """, (site_id,)).fetchall()
        conn.close()

        has_real_data = len(db_queries) > 0

        if has_real_data:
            queries = [dict(r) for r in db_queries]
            total_clicks = sum(q["clicks"] for q in queries)
            total_impressions = sum(q["impressions"] for q in queries)
            avg_ctr = round((total_clicks / total_impressions * 100), 1) if total_impressions > 0 else 0
            avg_pos = round(sum(q["position"] for q in queries) / len(queries), 1) if queries else 0
            data_source = "دیتای واقعی وارد شده از گوگل سرچ کنسول"
        else:
            from app.services.ai_content import detect_site_niche
            niche = detect_site_niche(site_name, domain, (site["category"] if site else "") or "", [])
            if niche == "gamification":
                queries = [
                    {"query": "گردونه شانس", "clicks": 180, "impressions": 2100, "ctr": 8.5, "position": 2.9, "is_preview": True},
                    {"query": "گردونه شانس آنلاین", "clicks": 110, "impressions": 1450, "ctr": 7.5, "position": 3.4, "is_preview": True},
                    {"query": "گیمیفیکیشن فروشگاه اینترنتی", "clicks": 85, "impressions": 920, "ctr": 9.2, "position": 2.4, "is_preview": True},
                    {"query": "کد تخفیف گردونه شانس", "clicks": 65, "impressions": 780, "ctr": 8.3, "position": 3.1, "is_preview": True},
                    {"query": "افزایش نرخ تبدیل با گردونه جوایز", "clicks": 45, "impressions": 530, "ctr": 8.4, "position": 3.8, "is_preview": True}
                ]
            else:
                queries = [
                    {"query": "تعمیرات تلویزیون در تبریز", "clicks": 142, "impressions": 1820, "ctr": 7.8, "position": 3.4, "is_preview": True},
                    {"query": "تعمیر تلویزیون در تبریز", "clicks": 98, "impressions": 1450, "ctr": 6.7, "position": 4.1, "is_preview": True},
                    {"query": "تعمیر تلویزیون سامسونگ تبریز", "clicks": 76, "impressions": 890, "ctr": 8.5, "position": 2.8, "is_preview": True},
                    {"query": "تعمیر بک لایت تلویزیون تبریز", "clicks": 54, "impressions": 620, "ctr": 8.7, "position": 3.1, "is_preview": True},
                    {"query": "تعمیر تلویزیون ال جی تبریز", "clicks": 49, "impressions": 580, "ctr": 8.4, "position": 3.5, "is_preview": True},
                    {"query": "هزینه تعویض بک لایت در تبریز", "clicks": 32, "impressions": 410, "ctr": 7.8, "position": 4.6, "is_preview": True},
                    {"query": "نمایندگی تعمیر تلویزیون تبریز", "clicks": 28, "impressions": 530, "ctr": 5.2, "position": 5.8, "is_preview": True},
                    {"query": "تعمیر تلویزیون سونی در تبریز", "clicks": 21, "impressions": 340, "ctr": 6.1, "position": 4.9, "is_preview": True}
                ]
            total_clicks = sum(q["clicks"] for q in queries)
            total_impressions = sum(q["impressions"] for q in queries)
            avg_ctr = round((total_clicks / total_impressions * 100), 1)
            avg_pos = round(sum(q["position"] for q in queries) / len(queries), 1)
            data_source = "حالت پیش‌نمایش (منتظر بارگذاری Queries.csv یا کلید Service Account)"

        # Adapt local maps status to current site
        business_title = site_name if site else "وب‌سایت ثبت شده"
        business_cat = site["category"] if site and site["category"] else "خدمات تخصصی"

        return {
            "site_id": site_id,
            "site_name": site_name,
            "domain": domain,
            "is_connected": self.is_connected,
            "has_real_data": has_real_data,
            "data_source": data_source,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "avg_position": avg_pos,
            "date_range": f"{days} روز اخیر",
            "top_queries": queries,
            "maps_status": {
                "business_name": business_title,
                "category": business_cat,
                "phone": "04134773603 / 09934658380" if "تبریز" in site_name else "تنظیم شده در سایت",
                "rating": 4.8,
                "reviews_count": 34,
                "verified": True,
                "local_pack_ranking": "Top 3 تبریز" if "تبریز" in site_name else "فعال در نتایج محلی"
            }
        }
