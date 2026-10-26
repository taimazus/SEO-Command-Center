import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.database import get_connection

class AlertService:
    """
    Real-time Smart Alerting System for SERP Drops, Technical Failures, and SEO Copilot Insights.
    Supports Telegram Bot, SMS Webhooks, and Internal UI Notification Center.
    """
    @staticmethod
    def notify(site_id: Optional[int], level: str, category: str, title: str, message: str) -> Dict[str, Any]:
        """
        Records an alert and dispatches to Telegram/SMS if credentials exist for the site.
        Levels: 'critical', 'warning', 'info', 'success'
        Categories: 'rank_drop', 'health', 'ssl', 'copilot', 'indexer'
        """
        conn = get_connection()
        conn.execute("""
            INSERT INTO system_alerts (site_id, level, category, title, message)
            VALUES (?, ?, ?, ?, ?)
        """, (site_id, level, category, title, message))
        conn.commit()

        # Check if site has Telegram configured
        telegram_sent = False
        if site_id:
            site = conn.execute("SELECT name, domain, telegram_chat_id, telegram_bot_token FROM sites WHERE id = ?", (site_id,)).fetchone()
            if site and site["telegram_bot_token"] and site["telegram_chat_id"]:
                formatted_msg = f"🚨 *هشدار سئو مرکز فرماندهی*\n\n" \
                                f"🌐 *سایت:* {site['name']} ({site['domain']})\n" \
                                f"📌 *موضوع:* {title}\n" \
                                f"📝 *جزئیات:* {message}\n" \
                                f"⏰ *زمان:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                telegram_sent = AlertService.send_telegram(site["telegram_bot_token"], site["telegram_chat_id"], formatted_msg)

        conn.close()
        return {"recorded": True, "telegram_sent": telegram_sent}

    @staticmethod
    def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
        if not bot_token or not chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "SEO-Command-Center"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def get_unread_alerts(limit: int = 10) -> List[Dict[str, Any]]:
        conn = get_connection()
        alerts = conn.execute("""
            SELECT a.*, s.domain, s.name as site_name
            FROM system_alerts a
            LEFT JOIN sites s ON s.id = a.site_id
            WHERE a.is_read = 0
            ORDER BY a.id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(a) for a in alerts]

    @staticmethod
    def mark_all_as_read(site_id: Optional[int] = None):
        conn = get_connection()
        if site_id:
            conn.execute("UPDATE system_alerts SET is_read = 1 WHERE site_id = ?", (site_id,))
        else:
            conn.execute("UPDATE system_alerts SET is_read = 1")
        conn.commit()
        conn.close()
