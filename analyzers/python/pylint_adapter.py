"""
Pylint adapter for Python code-quality analysis.
"""
import json
import uuid
import re
from typing import List, Dict, Any
from utils.subprocess_runner import run_tool_command, is_tool_available
from utils.file_handler import create_temp_workspace, cleanup_temp_workspace

class PylintAdapter:
    @staticmethod
    def _fallback_quality_check(source_code: str) -> List[Dict[str, Any]]:
        issues = []
        lines = source_code.splitlines()

        for idx, line in enumerate(lines, start=1):
            if re.match(r'^\s*except\s*:', line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                    "category": "code-quality",
                    "tool": "Pylint-Heuristic",
                    "rule": "bare-except",
                    "message": "Do not use bare 'except:'. Specify explicit exception types like 'except Exception:'.",
                    "source": line.strip()
                })
            if re.match(r'^\s*from\s+[\w.]+\s+import\s+\*', line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "WARNING",
                    "category": "code-quality",
                    "tool": "Pylint-Heuristic",
                    "rule": "wildcard-import",
                    "message": "Wildcard import makes code unpredictable and pollutes namespace.",
                    "source": line.strip()
                })
            if len(line) > 100:
                issues.append({
                    "line": idx,
                    "column": 100,
                    "severity": "CONVENTION",
                    "category": "style",
                    "tool": "Pylint-Heuristic",
                    "rule": "line-too-long",
                    "message": f"Line exceeds 100 characters ({len(line)} chars).",
                    "source": line.strip()[:60] + "..."
                })

        return issues

    @classmethod
    def analyze(cls, source_code: str, filename: str) -> List[Dict[str, Any]]:
        if not is_tool_available("pylint"):
            return cls._fallback_quality_check(source_code)

        temp_id = f"pylint_{uuid.uuid4().hex[:8]}"
        file_path = create_temp_workspace(temp_id, filename, source_code)
        issues = []

        try:
            cmd = ["pylint", "--output-format=json", "--disable=all", "--enable=E,W,C,R", str(file_path)]
            code, stdout, stderr = run_tool_command(cmd, timeout_sec=10)

            if stdout.strip():
                try:
                    data = json.loads(stdout)
                    for item in data:
                        issues.append({
                            "line": item.get("line", 1),
                            "column": item.get("column", 0),
                            "severity": item.get("type", "warning").upper(),
                            "category": "code-quality",
                            "tool": "Pylint",
                            "rule": item.get("symbol", "pylint-check"),
                            "message": item.get("message", "Quality rule violation"),
                            "source": ""
                        })
                except json.JSONDecodeError:
                    issues.extend(cls._fallback_quality_check(source_code))
            else:
                issues.extend(cls._fallback_quality_check(source_code))

        except Exception:
            issues.extend(cls._fallback_quality_check(source_code))
        finally:
            cleanup_temp_workspace(temp_id)

        return issues
