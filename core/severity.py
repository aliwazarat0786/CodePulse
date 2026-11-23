"""
Centralized severity mapping module.
Normalizes divergent tool outputs into standard CodePulse levels:
CRITICAL, HIGH, MEDIUM, LOW, INFO.
"""
from models.schemas import SeverityLevel

SEVERITY_MAPPINGS = {
    "fatal": SeverityLevel.CRITICAL.value,
    "error": SeverityLevel.HIGH.value,
    "warning": SeverityLevel.MEDIUM.value,
    "refactor": SeverityLevel.LOW.value,
    "convention": SeverityLevel.INFO.value,
    "info": SeverityLevel.INFO.value,
    "high": SeverityLevel.HIGH.value,
    "medium": SeverityLevel.MEDIUM.value,
    "low": SeverityLevel.LOW.value,
    "critical": SeverityLevel.CRITICAL.value,
    "blocker": SeverityLevel.CRITICAL.value,
    "major": SeverityLevel.HIGH.value,
    "minor": SeverityLevel.LOW.value,
    "trivial": SeverityLevel.INFO.value,
    "note": SeverityLevel.INFO.value,
}

CRITICAL_PATTERNS = [
    "buffer_overflow", "gets", "strcpy", "command_injection", "rce",
    "sql_injection", "eval", "deserialization", "memory_corruption", "use_after_free"
]

HIGH_PATTERNS = [
    "hardcoded_password", "hardcoded_secret", "subprocess_shell",
    "untrusted_input", "null_pointer_dereference", "memory_leak"
]

def map_severity(raw_severity: str, rule: str = "", message: str = "") -> str:
    """Normalize raw tool severity into standard CodePulse enum."""
    raw_lower = (raw_severity or "").strip().lower()
    combined = f"{rule} {message}".lower()

    for pat in CRITICAL_PATTERNS:
        if pat in combined:
            return SeverityLevel.CRITICAL.value

    for pat in HIGH_PATTERNS:
        if pat in combined and raw_lower not in ["critical"]:
            return SeverityLevel.HIGH.value

    if raw_lower in SEVERITY_MAPPINGS:
        return SEVERITY_MAPPINGS[raw_lower]

    return SeverityLevel.MEDIUM.value
