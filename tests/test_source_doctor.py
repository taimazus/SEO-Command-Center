import os
import pytest
from app.services.source_doctor import SourceDoctor
from app.services.gsc_service import GSCService

def test_source_doctor_analysis():
    # Test on real TabrizTv project
    doctor = SourceDoctor(r"F:\Projects\TabrizTv")
    result = doctor.analyze()
    assert result["success"] is True
    assert "ASP.NET" in result["framework"]
    assert "score" in result
    assert result["score"] >= 0

def test_source_doctor_manifest():
    doctor = SourceDoctor(r"F:\Projects\TabrizTv")
    manifest = doctor.generate_publish_manifest(days_modified=30)
    assert "total_files" in manifest
    assert "manifest" in manifest
    assert manifest["total_files"] >= 0

def test_gsc_service():
    gsc = GSCService()
    summary = gsc.get_performance_summary(site_id=1, days=28)
    assert summary["site_id"] == 1
    assert summary["total_clicks"] > 0
    assert summary["total_impressions"] > 0
    assert len(summary["top_queries"]) > 0
    assert summary["maps_status"]["rating"] == 4.8
