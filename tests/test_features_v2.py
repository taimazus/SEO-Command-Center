import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_content import get_suggested_topics_for_site, detect_site_niche, generate_seo_article

client = TestClient(app)

def test_browse_folder_api_drives():
    response = client.get("/api/utils/browse-folder")
    assert response.status_code == 200
    data = response.json()
    assert "drives" in data
    assert len(data["drives"]) > 0

def test_site_niche_detection():
    niche_spinora = detect_site_niche("گردونه شانس اسپینورا", "spinora.ir", "فروش و سرگرمی", ["گردونه شانس"])
    assert niche_spinora == "gamification"
    
    niche_tv = detect_site_niche("تعمیر تلویزیون تبریز", "tbztvrepair.ir", "تعمیرات", ["تعمیر تلویزیون"])
    assert niche_tv == "tv_repair"

def test_dynamic_topics_for_sites():
    # Site 1 is Tabriz TV
    topics_site1 = get_suggested_topics_for_site(1)
    assert len(topics_site1) > 0
    assert any("تلویزیون" in t["title"] or "بک لایت" in t["title"] for t in topics_site1)

    # Site 2 is Spinora
    topics_site2 = get_suggested_topics_for_site(2)
    assert len(topics_site2) > 0
    assert any("گردونه" in t["title"] or "گیمیفیکیشن" in t["title"] or "تبدیل" in t["title"] for t in topics_site2)

def test_generate_seo_article_isolation():
    # Generating for site 2 should be about gamification/spinora
    res = generate_seo_article(2, "راهنمای گردونه شانس", "گردونه شانس", "آنلاین")
    assert res["status"] == "published"
    assert "گردونه" in res["title"] or "شانس" in res["title"]
