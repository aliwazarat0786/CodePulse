"""
Bandit adapter for Python security analysis.
"""
import json
import uuid
import re
from typing import List, Dict, Any
from utils.subprocess_runner import run_tool_command, is_tool_available
from utils.file_handler import create_temp_workspace, cleanup_temp_workspace

class BanditAdapter:
    @staticmethod
    def _fallback_security_check(source_code: str) -> List[Dict[str, Any]]:
        issues = []
        lines = source_code.splitlines()

        for idx, line in enumerate(lines, start=1):
            if re.search(r'(?i)(password|secret|api_key|token)\s*=\s*["\']([^"\']{4,})["\']', line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "Bandit-Heuristic",
                    "rule": "hardcoded-secret",
                    "message": "Potential hardcoded credential or secret key found.",
                    "source": line.strip(),
                    "suggested_fix": "Load secrets securely from environment variables using os.getenv()."
                })

            if "subprocess" in line and "shell=True" in line:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "Bandit-Heuristic",
                    "rule": "subprocess-shell-true",
                    "message": "Subprocess executed with shell=True invites Shell Injection vulnerabilities.",
                    "source": line.strip(),
                    "suggested_fix": "Use a list of arguments and set shell=False."
                })

            if re.search(r'hashlib\.(md5|sha1)\(', line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "MEDIUM",
                    "category": "security",
                    "tool": "Bandit-Heuristic",
                    "rule": "weak-hash",
                    "message": "Weak cryptographic hash function detected.",
                    "source": line.strip(),
                    "suggested_fix": "Use stronger hash functions such as SHA-256 or SHA-512."
                })

        return issues

    @classmethod
    def analyze(cls, source_code: str, filename: str) -> List[Dict[str, Any]]:
        if not is_tool_available("bandit"):
            return cls._fallback_security_check(source_code)

        temp_id = f"bandit_{uuid.uuid4().hex[:8]}"
        file_path = create_temp_workspace(temp_id, filename, source_code)
        issues = []

        try:
            cmd = ["bandit", "-f", "json", "-q", str(file_path)]
            code, stdout, stderr = run_tool_command(cmd, timeout_sec=10)

            if stdout.strip():
                try:
                    data = json.loads(stdout)
                    results = data.get("results", [])
                    for res in results:
                        issues.append({
                            "line": res.get("line_number", 1),
                            "column": res.get("col_offset", 0),
                            "severity": res.get("issue_severity", "MEDIUM").upper(),
                            "category": "security",
                            "tool": "Bandit",
                            "rule": res.get("test_id", "security-issue"),
                            "message": res.get("issue_text", "Security risk detected"),
                            "source": res.get("code", "").strip(),
                            "confidence": 0.95 if res.get("issue_confidence") == "HIGH" else 0.75,
                            "documentation_url": res.get("more_info", "")
                        })
                except json.JSONDecodeError:
                    issues.extend(cls._fallback_security_check(source_code))
            else:
                issues.extend(cls._fallback_security_check(source_code))

        except Exception:
            issues.extend(cls._fallback_security_check(source_code))
        finally:
            cleanup_temp_workspace(temp_id)

        return issues
