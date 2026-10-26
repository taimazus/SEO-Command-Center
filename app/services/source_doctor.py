import os
import re
import shutil
import zipfile
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class SourceDoctor:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.issues = []
        self.fixes = []
        self.score = 100

    def analyze(self) -> Dict[str, Any]:
        self.issues = []
        self.score = 100

        if not os.path.exists(self.project_path):
            return {
                "success": False,
                "error": f"مسیر پروژه یافت نشد: {self.project_path}",
                "score": 0,
                "issues": [f"پوشه پروژه در آدرس {self.project_path} وجود ندارد."]
            }

        # 1. Detect Framework
        framework = self._detect_framework()

        # 2. Check Web.config for 301 Redirects (if ASP.NET / IIS)
        self._check_web_config()

        # 3. Check App_Code for misplaced code-behind files (Crucial Server Error Prevention)
        self._check_app_code_conflicts()

        # 4. Check Master pages and main HTML/ASPX files for SEO Tags
        self._check_markup_files()

        self.score = max(0, min(100, self.score))

        return {
            "success": True,
            "project_path": self.project_path,
            "framework": framework,
            "score": self.score,
            "issues": self.issues,
            "total_issues": len(self.issues)
        }

    def _detect_framework(self) -> str:
        files = os.listdir(self.project_path)
        if any(f.endswith(".aspx") or f.endswith(".master") or f.lower() == "web.config" for f in files):
            return "ASP.NET Web Forms / IIS"
        elif any(f.endswith(".csproj") for f in files):
            return "ASP.NET Core / .NET"
        elif any(f.endswith(".php") for f in files):
            return "PHP / Laravel / WordPress"
        elif "package.json" in files:
            return "Node.js / React / Next.js"
        return "وب‌سایت استاتیک / سفارشی"

    def _check_web_config(self):
        web_config_path = os.path.join(self.project_path, "Web.config")
        if not os.path.exists(web_config_path):
            web_config_path = os.path.join(self.project_path, "web.config")

        if os.path.exists(web_config_path):
            try:
                with open(web_config_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check 301 rewrite rule
                if "Redirect WWW to Non-WWW" not in content and "redirectType=\"Permanent\"" not in content:
                    self.score -= 20
                    self.issues.append({
                        "severity": "high",
                        "category": "ریدایرکت و وب‌کانفیگ",
                        "title": "عدم وجود قانون ریدایرکت ۳۰۱ ساب‌دامین www در Web.config",
                        "description": "قانون URL Rewrite دائمی ۳۰۱ برای انتقال خودکار www به نسخه بدون www در Web.config یافت نشد.",
                        "fixable": True,
                        "file": "Web.config"
                    })

                # Check customErrors mode
                if "mode=\"Off\"" in content:
                    self.score -= 10
                    self.issues.append({
                        "severity": "medium",
                        "category": "امنیت و پیکربندی",
                        "title": "حالت CustomErrors روی Off تنظیم شده است",
                        "description": "بهتر است جهت جلوگیری از افشای اطلاعات فنی به موتورهای جستجو روی RemoteOnly تنظیم شود.",
                        "fixable": False,
                        "file": "Web.config"
                    })
            except Exception as e:
                self.issues.append({
                    "severity": "medium",
                    "category": "خواندن فایل",
                    "title": f"خطا در بررسی Web.config: {str(e)}",
                    "fixable": False,
                    "file": "Web.config"
                })

    def _check_app_code_conflicts(self):
        app_code_dir = os.path.join(self.project_path, "App_Code")
        if os.path.exists(app_code_dir) and os.path.isdir(app_code_dir):
            for root, _, files in os.walk(app_code_dir):
                for f in files:
                    if f.endswith(".aspx.cs") or f.endswith(".master.cs"):
                        self.score -= 30
                        rel_path = os.path.relpath(os.path.join(root, f), self.project_path)
                        self.issues.append({
                            "severity": "critical",
                            "category": "ساختار هاست و سرور",
                            "title": f"فایل Code-Behind در پوشه App_Code قرار گرفته است: {f}",
                            "description": f"فایل {rel_path} نباید داخل App_Code باشد؛ این موضوع باعث خطای بحرانی سرور ۵۰۰ (CS0103) می‌شود.",
                            "fixable": True,
                            "file": rel_path
                        })

    def _check_markup_files(self):
        # Scan Master and Default pages
        target_files = []
        for root, _, files in os.walk(self.project_path):
            # Skip hidden, bin, obj, vendor, .git
            if any(part.startswith(".") or part in ["bin", "obj", "vendor", "node_modules", "App_Data"] for part in root.split(os.sep)):
                continue
            for f in files:
                if f.endswith(".master") or f.lower() in ["default.aspx", "index.html", "index.php"]:
                    target_files.append(os.path.join(root, f))

        for file_path in target_files[:10]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_name = os.path.relpath(file_path, self.project_path)

                # Check Title
                if "<title" not in content.lower():
                    self.score -= 10
                    self.issues.append({
                        "severity": "high",
                        "category": "محتوا و متادیتا",
                        "title": f"تگ Title در فایل {rel_name} یافت نشد",
                        "description": "صفحه فاقد عنوان اصلی در تگ <head> است.",
                        "fixable": False,
                        "file": rel_name
                    })

                # Check H1 in default/index pages
                if "default" in rel_name.lower() or "index" in rel_name.lower():
                    if "<h1" not in content.lower():
                        self.score -= 15
                        self.issues.append({
                            "severity": "high",
                            "category": "هدینگ‌ها",
                            "title": f"تگ H1 در صفحه اصلی ({rel_name}) یافت نشد",
                            "description": "صفحه اصلی باید حداقل یک تگ H1 شفاف و غنی از کلمات کلیدی داشته باشد.",
                            "fixable": False,
                            "file": rel_name
                        })

                # Check Canonical
                if "canonical" not in content.lower() and rel_name.endswith(".master"):
                    self.score -= 10
                    self.issues.append({
                        "severity": "medium",
                        "category": "متادیتا و سئو فنی",
                        "title": f"تگ Canonical در مسترپیج ({rel_name}) یافت نشد",
                        "description": "تگ کنونیکال برای پیشگیری از جریمه محتوای تکراری ضروری است.",
                        "fixable": False,
                        "file": rel_name
                    })

            except Exception as e:
                logging.debug(f"Could not read master page {full_path}: {e}")

    def auto_fix(self) -> Dict[str, Any]:
        self.fixes = []
        # 1. Fix Web.config 301 rule if missing
        web_config_path = os.path.join(self.project_path, "Web.config")
        if os.path.exists(web_config_path):
            with open(web_config_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "Redirect WWW to Non-WWW" not in content:
                # Backup first
                bak_path = web_config_path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(web_config_path, bak_path)

                rule_snippet = """\t\t<rewrite>
\t\t\t<rules>
\t\t\t\t<rule name="Redirect WWW to Non-WWW" stopProcessing="true">
\t\t\t\t\t<match url="(.*)" />
\t\t\t\t\t<conditions logicalGrouping="MatchAll" trackAllCaptures="false">
\t\t\t\t\t\t<add input="{HTTP_HOST}" pattern="^www\\.(.+)$" />
\t\t\t\t\t</conditions>
\t\t\t\t\t<action type="Redirect" url="https://{C:1}/{R:1}" redirectType="Permanent" />
\t\t\t\t</rule>
\t\t\t</rules>
\t\t</rewrite>\n"""

                if "<system.webServer>" in content:
                    new_content = content.replace("<system.webServer>", f"<system.webServer>\n{rule_snippet}", 1)
                    with open(web_config_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    self.fixes.append(f"قانون ریدایرکت ۳۰۱ در Web.config درج شد (پشتیبان: {os.path.basename(bak_path)})")

        return {
            "success": True,
            "fixes_applied": self.fixes
        }

    def generate_publish_manifest(self, days_modified: int = 7) -> Dict[str, Any]:
        manifest = []
        total_size = 0
        now = datetime.now().timestamp()
        time_limit = now - (days_modified * 86400)

        for root, _, files in os.walk(self.project_path):
            rel_dir = os.path.relpath(root, self.project_path)
            # Skip non-publishable dirs
            if any(part.startswith(".") or part in ["bin", "obj", "packages", ".git"] for part in rel_dir.split(os.sep)):
                continue

            for f in files:
                full_path = os.path.join(root, f)
                rel_file = os.path.relpath(full_path, self.project_path)
                mtime = os.path.getmtime(full_path)

                if mtime >= time_limit or f in ["Web.config", "Global.asax", "Default.aspx"]:
                    size = os.path.getsize(full_path)
                    total_size += size

                    # Map to hosting target
                    if rel_dir == ".":
                        target_dir = "httpdocs/"
                    else:
                        target_dir = f"httpdocs/{rel_dir.replace(os.sep, '/')}/"

                    warning = ""
                    if "App_Code" in rel_dir and (f.endswith(".aspx.cs") or f.endswith(".master.cs")):
                        warning = "⚠️ خطر: این فایل نباید در App_Code هاست آپلود شود!"

                    manifest.append({
                        "file_name": f,
                        "rel_path": rel_file.replace(os.sep, "/"),
                        "target_dir": target_dir,
                        "size_kb": round(size / 1024, 2),
                        "modified_at": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                        "warning": warning
                    })

        return {
            "project_path": self.project_path,
            "total_files": len(manifest),
            "total_size_kb": round(total_size / 1024, 2),
            "manifest": manifest
        }

    def create_publish_zip(self, output_zip_path: str, days_modified: int = 7) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
        manifest_data = self.generate_publish_manifest(days_modified=days_modified)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for item in manifest_data["manifest"]:
                local_path = os.path.join(self.project_path, item["rel_path"].replace("/", os.sep))
                if os.path.exists(local_path):
                    z.write(local_path, arcname=item["rel_path"])

        return output_zip_path
