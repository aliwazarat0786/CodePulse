"""
Integration tests for Flask API endpoints.
"""
import pytest
import json
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"

def test_languages_endpoint(client):
    res = client.get("/api/languages")
    assert res.status_code == 200
    data = res.get_json()
    assert "python" in data["languages"]
    assert len(data["languages"]) >= 5

def test_analyze_python_code(client):
    payload = {
        "source_code": "import os\npassword = '123'\ndef run(): eval('1+1')",
        "language": "python",
        "filename": "demo.py",
        "enable_ai": True
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "summary" in data["analysis"]
    assert "issues" in data["analysis"]
    assert len(data["analysis"]["issues"]) > 0

def test_analyze_empty_code(client):
    res = client.post("/api/analyze", json={"source_code": ""})
    assert res.status_code == 400
