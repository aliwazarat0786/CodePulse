"""
Java Analyzer for CodePulse AI.
"""
import re
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer

class JavaAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("java")

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = source_code.splitlines()
        branch_count = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            if re.search(r'\b(if|else if|for|while|case|catch)\b', stripped):
                branch_count += 1

            # Empty catch block
            if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "bug-risk",
                    "tool": "Java-Checkstyle-Adapter",
                    "rule": "empty-catch-block",
                    "message": "Empty catch block suppresses exceptions silently, concealing runtime failures.",
                    "source": stripped,
                    "suggested_fix": "Log the exception using a logger (e.g., logger.error()) or rethrow."
                })

            # Hardcoded Credentials
            if re.search(r'(?i)(password|secret|apiKey|authToken)\s*=\s*"[^"]{4,}"', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "Java-SpotBugs-Adapter",
                    "rule": "hardcoded-credential",
                    "message": "Potential hardcoded credential or secret detected in Java source.",
                    "source": stripped,
                    "suggested_fix": "Read credentials from System.getenv() or a secure configuration vault."
                })

            # Wildcard import
            if re.match(r'import\s+[\w.]+\.\*;', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "Java-PMD-Adapter",
                    "rule": "wildcard-import",
                    "message": "Avoid wildcard imports in Java. Import specific classes instead.",
                    "source": stripped,
                    "suggested_fix": "Replace .* with the specific class required."
                })

            # System.out.println
            if "System.out.print" in stripped:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "INFO",
                    "category": "code-quality",
                    "tool": "Java-PMD-Adapter",
                    "rule": "avoid-system-out",
                    "message": "Use of System.out.println. Prefer a formal logging framework (SLF4J, Logback).",
                    "source": stripped,
                    "suggested_fix": "Use Logger.info() instead of System.out.println()."
                })

        loc = max(1, len(lines))
        comment_lines = sum(1 for l in lines if l.strip().startswith(("//", "/*", "*")))
        comment_ratio = comment_lines / loc

        total_methods = max(1, len(re.findall(r'(public|private|protected|static)\s+[\w<>\[\]]+\s+\w+\s*\(', source_code)))
        cc = max(1.0, round(1.0 + (branch_count / total_methods), 1))
        
        import math
        mi = max(25.0, min(100.0, round(100.0 - (cc * 3.0) - (math.log(loc + 1) * 2.2) + (comment_ratio * 12.0), 1)))

        return issues, {
            "cyclomatic_complexity": cc,
            "maintainability_index": mi
        }
