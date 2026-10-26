import os
import ftplib
import logging
from typing import Dict, Any, List, Optional
import io

class FTPDeployer:
    """
    Plesk & cPanel Direct FTP/FTPS Deployment Service.
    Deploys updated code, Web.config fixes, or full packages directly to remote server.
    """
    def __init__(self, host: str, port: int = 21, user: str = "", password: str = "", remote_root: str = "/httpdocs"):
        self.host = host.strip()
        self.port = int(port or 21)
        self.user = user.strip()
        self.password = password.strip()
        self.remote_root = remote_root.strip() or "/httpdocs"

    def _connect(self) -> ftplib.FTP:
        ftp = ftplib.FTP()
        ftp.connect(self.host, self.port, timeout=12)
        ftp.login(self.user, self.password)
        ftp.encoding = "utf-8"
        return ftp

    def test_connection(self) -> Dict[str, Any]:
        if not self.host or not self.user:
            return {"success": False, "message": "اطلاعات هاست و نام کاربری FTP وارد نشده است."}
        try:
            ftp = self._connect()
            welcome = ftp.getwelcome()
            
            # Check if remote root exists
            try:
                ftp.cwd(self.remote_root)
                files = ftp.nlst()[:10]
            except Exception:
                files = []

            ftp.quit()
            return {
                "success": True,
                "message": f"اتصال به هاست پلسک ({self.host}) با موفقیت برقرار شد.",
                "remote_root": self.remote_root,
                "files_sample": files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"خطا در اتصال FTP: {str(e)}"
            }

    def deploy_single_file(self, local_path: str, remote_rel_path: str, make_backup: bool = True) -> Dict[str, Any]:
        """
        Uploads a single file (like Web.config) to remote path with backup (.bak) support.
        """
        if not os.path.exists(local_path):
            return {"success": False, "message": f"فایل محلی '{local_path}' یافت نشد."}

        try:
            ftp = self._connect()
            ftp.cwd(self.remote_root)

            # Navigate or create directories
            dirs = remote_rel_path.replace("\\", "/").strip("/").split("/")
            filename = dirs.pop()
            
            for d in dirs:
                try:
                    ftp.cwd(d)
                except Exception:
                    ftp.mkd(d)
                    ftp.cwd(d)

            # Backup existing file if requested
            backup_created = False
            if make_backup:
                try:
                    existing_files = ftp.nlst()
                    if filename in existing_files:
                        backup_name = f"{filename}.bak"
                        try:
                            ftp.delete(backup_name)
                        except Exception as del_err:
                            logging.debug(f"Previous backup file {backup_name} not present or could not be removed: {del_err}")
                        ftp.rename(filename, backup_name)
                        backup_created = True
                except Exception as bak_err:
                    logging.warning(f"Could not create remote backup file for {filename}: {bak_err}")

            # Upload local file
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)

            ftp.quit()
            return {
                "success": True,
                "message": f"فایل '{filename}' با موفقیت روی هاست مستقر شد." + (" (نسخه پشتیبان .bak ایجاد شد)" if backup_created else ""),
                "backup_created": backup_created
            }
        except Exception as e:
            return {"success": False, "message": f"خطا در استقرار فایل روی هاست: {str(e)}"}

    def deploy_manifest_files(self, project_path: str, manifest_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Uploads all modified files listed in the deployment manifest.
        """
        if not manifest_items:
            return {"success": False, "message": "هیچ فایلی برای استقرار وجود ندارد."}

        success_count = 0
        errors = []

        try:
            ftp = self._connect()
            for item in manifest_items:
                local_file = os.path.join(project_path, item["rel_path"])
                if not os.path.exists(local_file):
                    continue

                # Reset to remote root
                ftp.cwd(self.remote_root)
                target_dir = item.get("target_dir", "").replace("\\", "/").strip("/")
                if target_dir:
                    for d in target_dir.split("/"):
                        try:
                            ftp.cwd(d)
                        except Exception:
                            ftp.mkd(d)
                            ftp.cwd(d)

                filename = item["file_name"]
                try:
                    with open(local_file, "rb") as f:
                        ftp.storbinary(f"STOR {filename}", f)
                    success_count += 1
                except Exception as err:
                    errors.append(f"{filename}: {str(err)}")

            ftp.quit()
            return {
                "success": len(errors) == 0,
                "uploaded_count": success_count,
                "errors": errors,
                "message": f"{success_count} فایل با موفقیت روی هاست پلسک جایگزین شدند."
            }
        except Exception as e:
            return {"success": False, "message": f"خطا در فرآیند استقرار FTP: {str(e)}"}
