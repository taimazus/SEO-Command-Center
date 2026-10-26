import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "seo_center.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        domain TEXT NOT NULL UNIQUE,
        category TEXT DEFAULT 'خدماتی',
        city TEXT DEFAULT 'تبریز',
        sitemap_url TEXT,
        gsc_site_url TEXT,
        project_path TEXT,
        ftp_host TEXT,
        ftp_port INTEGER DEFAULT 21,
        ftp_user TEXT,
        ftp_pass TEXT,
        ftp_root TEXT DEFAULT '/httpdocs',
        wp_api_url TEXT,
        wp_user TEXT,
        wp_app_pass TEXT,
        telegram_chat_id TEXT,
        telegram_bot_token TEXT,
        autopilot_enabled BOOLEAN DEFAULT 1,
        auto_index BOOLEAN DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_checked_at DATETIME
    );

    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        keyword TEXT NOT NULL,
        target_url TEXT,
        current_position INTEGER DEFAULT 0,
        best_position INTEGER DEFAULT 0,
        previous_position INTEGER DEFAULT 0,
        last_checked_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS rank_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
        position INTEGER NOT NULL,
        checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS indexing_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        url TEXT NOT NULL,
        engine TEXT NOT NULL,
        status TEXT NOT NULL,
        response_code INTEGER,
        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        slug TEXT,
        category TEXT,
        summary TEXT,
        content_html TEXT NOT NULL,
        keywords_used TEXT,
        meta_description TEXT,
        status TEXT DEFAULT 'draft',
        published_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS health_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        status_code INTEGER,
        response_time_ms REAL,
        has_ssl BOOLEAN,
        has_h1 BOOLEAN,
        h1_text TEXT,
        has_canonical BOOLEAN,
        canonical_url TEXT,
        has_sitemap BOOLEAN,
        has_robots BOOLEAN,
        redirect_301_working BOOLEAN,
        overall_score INTEGER,
        issues_json TEXT,
        audited_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS gsc_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        query TEXT NOT NULL,
        clicks INTEGER DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        ctr REAL DEFAULT 0.0,
        position REAL DEFAULT 0.0,
        fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS system_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER REFERENCES sites(id) ON DELETE CASCADE,
        level TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS seo_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
        rec_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        action_plan TEXT NOT NULL,
        impact_level TEXT DEFAULT 'high',
        is_applied BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS autopilot_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_type TEXT NOT NULL,
        summary TEXT NOT NULL,
        items_processed INTEGER DEFAULT 0,
        alerts_generated INTEGER DEFAULT 0,
        ran_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migrations for existing sites table
    existing_cols = [col["name"] for col in cursor.execute("PRAGMA table_info(sites)").fetchall()]
    new_cols = {
        "project_path": "TEXT",
        "ftp_host": "TEXT",
        "ftp_port": "INTEGER DEFAULT 21",
        "ftp_user": "TEXT",
        "ftp_pass": "TEXT",
        "ftp_root": "TEXT DEFAULT '/httpdocs'",
        "wp_api_url": "TEXT",
        "wp_user": "TEXT",
        "wp_app_pass": "TEXT",
        "telegram_chat_id": "TEXT",
        "telegram_bot_token": "TEXT",
        "autopilot_enabled": "BOOLEAN DEFAULT 1"
    }

    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE sites ADD COLUMN {col_name} {col_type};")

    # Seed initial data for Tabriz TV if empty
    cursor.execute("SELECT COUNT(*) AS count FROM sites")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO sites (name, domain, category, city, sitemap_url, gsc_site_url, project_path, auto_index, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
        """, (
            "مرکز تخصصی تعمیر تلویزیون تبریز (تبریز تی‌وی)",
            "tbztvrepair.ir",
            "تعمیرات لوازم خانگی و صوتی تصویری",
            "تبریز",
            "https://tbztvrepair.ir/sitemap.xml",
            "sc-domain:tbztvrepair.ir",
            r"F:\Projects\TabrizTv"
        ))
        site_id = cursor.lastrowid

        default_keywords = [
            ("تعمیرات تلویزیون در تبریز", "https://tbztvrepair.ir/"),
            ("تعمیر تلویزیون در تبریز", "https://tbztvrepair.ir/"),
            ("تعمیر تلویزیون تبریز", "https://tbztvrepair.ir/"),
            ("تعمیر تلویزیون سامسونگ در تبریز", "https://tbztvrepair.ir/Services.aspx?id=11"),
            ("تعمیر تلویزیون ال جی در تبریز", "https://tbztvrepair.ir/Services.aspx?id=12"),
            ("تعمیر تلویزیون سونی در تبریز", "https://tbztvrepair.ir/Services.aspx?id=13"),
            ("تعمیر بک لایت تلویزیون در تبریز", "https://tbztvrepair.ir/"),
            ("تعمیر تلویزیون اسنوا در تبریز", "https://tbztvrepair.ir/Services.aspx?id=14"),
            ("تعمیر تلویزیون دوو در تبریز", "https://tbztvrepair.ir/Services.aspx?id=15"),
            ("تعمیر تلویزیون ایکس ویژن در تبریز", "https://tbztvrepair.ir/Services.aspx?id=16")
        ]

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for kw, url in default_keywords:
            cursor.execute("""
                INSERT INTO keywords (site_id, keyword, target_url, current_position, best_position, previous_position, last_checked_at)
                VALUES (?, ?, ?, 0, 0, 0, ?)
            """, (site_id, kw, url, now_str))
    else:
        # Ensure site 1 has project_path set
        cursor.execute("UPDATE sites SET project_path = ? WHERE id = 1 AND (project_path IS NULL OR project_path = '')", (r"F:\Projects\TabrizTv",))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database updated and initialized successfully.")
