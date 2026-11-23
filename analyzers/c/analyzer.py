"""
C Analyzer for CodePulse AI.
"""
import re
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer

class CAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("c")

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = source_code.splitlines()

        malloc_count = 0
        free_count = 0
        branch_count = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            if re.search(r'\b(if|else if|for|while|case)\b', stripped):
                branch_count += 1

            if re.search(r'\bgets\s*\(', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "Clang-Tidy-C",
                    "rule": "security-insecure-gets",
                    "message": "gets() does not check buffer boundaries and was removed from C11. Major buffer overflow vulnerability.",
                    "source": stripped,
                    "suggested_fix": "Replace with fgets(buf, sizeof(buf), stdin)."
                })

            if re.search(r'\bstrcpy\s*\(', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "Clang-Tidy-C",
                    "rule": "security-insecure-strcpy",
                    "message": "strcpy does not verify destination buffer length. Susceptible to buffer overflow.",
                    "source": stripped,
                    "suggested_fix": "Replace with strncpy() or snprintf() with explicit boundary limits."
                })

            if re.search(r'\bsprintf\s*\(', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "MEDIUM",
                    "category": "security",
                    "tool": "Clang-Tidy-C",
                    "rule": "security-insecure-sprintf",
                    "message": "sprintf may overflow destination buffer. Prefer snprintf.",
                    "source": stripped,
                    "suggested_fix": "Use snprintf(buf, sizeof(buf), ...)."
                })

            if re.search(r'\b(malloc|calloc|realloc)\s*\(', stripped):
                malloc_count += 1
            if re.search(r'\bfree\s*\(', stripped):
                free_count += 1

        if malloc_count > free_count:
            issues.append({
                "line": 1,
                "column": 0,
                "severity": "HIGH",
                "category": "bug-risk",
                "tool": "Clang-Static-Analyzer",
                "rule": "potential-memory-leak",
                "message": f"Potential memory leak: {malloc_count} dynamic allocation(s) detected with only {free_count} free() call(s).",
                "suggested_fix": "Ensure all dynamically allocated memory is freed along all control flow exit paths."
            })

        loc = max(1, len(lines))
        comment_lines = sum(1 for l in lines if l.strip().startswith(("//", "/*", "*")))
        comment_ratio = comment_lines / loc

        total_functions = max(1, len(re.findall(r'\b[a-zA-Z_]\w*\s+[a-zA-Z_]\w*\s*\([^;]*?\)\s*\{', source_code)))
        cc = max(1.0, round(1.0 + (branch_count / total_functions), 1))
        
        import math
        mi = max(25.0, min(100.0, round(100.0 - (cc * 3.0) - (math.log(loc + 1) * 2.2) + (comment_ratio * 12.0), 1)))

        return issues, {
            "cyclomatic_complexity": cc,
            "maintainability_index": mi
        }
