"""
Unit tests for Normalizer and Deduplicator.
"""
import pytest
from core.normalizer import IssueNormalizer
from core.deduplicator import IssueDeduplicator
from models.schemas import Issue

def test_normalizer():
    raw = [{
        "line": 10,
        "severity": "high",
        "category": "security",
        "tool": "Bandit",
        "rule": "hardcoded-secret",
        "message": "Potential credential detected"
    }]
    normalized = IssueNormalizer.normalize(raw, "python", "app.py")
    assert len(normalized) == 1
    assert normalized[0].severity == "HIGH"
    assert normalized[0].id == "CP-001"

def test_deduplicator():
    issues = [
        Issue(id="CP-001", language="python", file="app.py", line=10, column=0, severity="MEDIUM", category="security", tool="ToolA", rule="secret", message="Secret leaked"),
        Issue(id="CP-002", language="python", file="app.py", line=10, column=0, severity="HIGH", category="security", tool="ToolB", rule="secret", message="Hardcoded secret found")
    ]
    merged = IssueDeduplicator.deduplicate(issues)
    assert len(merged) == 1
    assert merged[0].severity == "HIGH"
    assert "ToolA" in merged[0].detected_by
    assert "ToolB" in merged[0].detected_by
