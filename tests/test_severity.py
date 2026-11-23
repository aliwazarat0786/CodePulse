"""
Unit tests for Severity mapping.
"""
import pytest
from core.severity import map_severity

def test_severity_mappings():
    assert map_severity("fatal") == "CRITICAL"
    assert map_severity("error") == "HIGH"
    assert map_severity("warning") == "MEDIUM"
    assert map_severity("convention") == "INFO"

def test_rule_based_severity_boost():
    assert map_severity("low", rule="unsafe-eval", message="eval called") == "CRITICAL"
    assert map_severity("low", rule="buffer_overflow_gets", message="gets used") == "CRITICAL"
    assert map_severity("low", rule="hardcoded_secret", message="API key") == "HIGH"
