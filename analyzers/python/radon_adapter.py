"""
Radon adapter for Python complexity analysis.
"""
from typing import Dict, Any, List, Tuple
import re

class RadonAdapter:
    @staticmethod
    def analyze(source_code: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        metrics: Dict[str, Any] = {
            "cyclomatic_complexity": 1.0,
            "maintainability_index": 85.0
        }

        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit

            blocks = cc_visit(source_code)
            total_cc = 0
            count = 0
            
            for b in blocks:
                total_cc += b.complexity
                count += 1
                if b.complexity > 10:
                    severity = "HIGH" if b.complexity > 20 else "MEDIUM"
                    issues.append({
                        "line": b.lineno,
                        "column": b.col_offset,
                        "severity": severity,
                        "category": "complexity",
                        "tool": "Radon",
                        "rule": "high-cyclomatic-complexity",
                        "message": f"Function '{b.name}' has high cyclomatic complexity ({b.complexity}, grade {b.letter}).",
                        "suggested_fix": "Refactor by breaking complex branches into smaller subroutines."
                    })

            if count > 0:
                metrics["cyclomatic_complexity"] = round(total_cc / count, 1)

            mi = mi_visit(source_code, multi=True)
            metrics["maintainability_index"] = round(mi, 1)
            
            if mi < 50:
                issues.append({
                    "line": 1,
                    "column": 0,
                    "severity": "MEDIUM",
                    "category": "maintainability",
                    "tool": "Radon",
                    "rule": "low-maintainability",
                    "message": f"Code maintainability index is low ({round(mi, 1)}/100).",
                    "suggested_fix": "Refactor monolithic functions and reduce branch complexity."
                })

        except ImportError:
            branches = len(re.findall(r'\b(if|elif|for|while|except)\b', source_code))
            metrics["cyclomatic_complexity"] = max(1.0, round(1.0 + (branches * 0.8), 1))
            metrics["maintainability_index"] = max(20.0, round(100.0 - (branches * 2.5), 1))

        except Exception:
            pass

        return issues, metrics
