import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_connection

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

client = TestClient(app)

def test_dashboard_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "SEO Command" in response.text
    assert "داشبورد اجرایی" in response.text

def test_sites_page():
    response = client.get("/sites")
    assert response.status_code == 200
    assert "مدیریت وب‌سایت‌ها" in response.text
    assert "tbztvrepair.ir" in response.text

def test_rank_tracker_page():
    response = client.get("/rank-tracker")
    assert response.status_code == 200
    assert "رصد زنده کلمات" in response.text
    assert "صفحه ۲ گوگل" in response.text

def test_source_doctor_page():
    response = client.get("/source-doctor?project_path=F:\\Projects\\TabrizTv")
    assert response.status_code == 200
    assert "پزشک سورس‌کد" in response.text

def test_update_site_path_api():
    conn = get_connection()
    site = conn.execute("SELECT id FROM sites LIMIT 1").fetchone()
    conn.close()
    assert site is not None
    site_id = site["id"]

    custom_path = r"F:\Projects\TabrizTv_Custom"
    response = client.post(f"/api/sites/{site_id}/update-path", data={
        "project_path": custom_path
    }, follow_redirects=True)
    assert response.status_code == 200

    conn = get_connection()
    updated = conn.execute("SELECT project_path FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    assert updated["project_path"] == custom_path

def test_gsc_integration_page():
    response = client.get("/gsc-integration")
    assert response.status_code == 200
    assert "Google Search Console" in response.text
    assert "نقشه گوگل" in response.text

def test_gsc_import_csv_api():
    conn = get_connection()
    site = conn.execute("SELECT id FROM sites LIMIT 1").fetchone()
    conn.close()
    assert site is not None
    site_id = site["id"]

    csv_data = "Top queries,Clicks,Impressions,CTR,Position\nتعمیر برد تلویزیون در تبریز,15,220,6.8%,4.2\nتعمیر پنل آبخورده,9,140,6.4%,5.1\n".encode("utf-8")
    files = {
        "file": ("Queries.csv", io.BytesIO(csv_data), "text/csv")
    }
    data = {
        "site_id": site_id
    }
    response = client.post("/api/gsc/import-csv", files=files, data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "تعمیر برد تلویزیون در تبریز" in response.text

def test_content_generator_page():
    response = client.get("/content-generator")
    assert response.status_code == 200
    assert "تولید مقاله با هوش مصنوعی" in response.text

def test_indexer_page():
    response = client.get("/indexer")
    assert response.status_code == 200
    assert "IndexNow" in response.text

def test_health_audit_page():
    response = client.get("/health-audit")
    assert response.status_code == 200
    assert "پایش سلامت فنی" in response.text

def test_generate_content_api():
    conn = get_connection()
    site = conn.execute("SELECT id FROM sites LIMIT 1").fetchone()
    conn.close()
    assert site is not None

    response = client.post("/api/generate-content", data={
        "site_id": site["id"],
        "topic": "تعمیر بک لایت",
        "brand": "ال جی",
        "city": "تبریز"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "ال جی" in response.text

def test_submit_indexing_api():
    conn = get_connection()
    site = conn.execute("SELECT id FROM sites LIMIT 1").fetchone()
    conn.close()

    response = client.post("/api/submit-indexing", data={
        "site_id": site["id"],
        "urls": "https://tbztvrepair.ir/test-page-1\nhttps://tbztvrepair.ir/test-page-2"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "test-page-1" in response.text
