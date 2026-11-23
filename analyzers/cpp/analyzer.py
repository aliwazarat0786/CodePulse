"""
C++ Analyzer for CodePulse AI.
"""
import re
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer
from analyzers.c.analyzer import CAnalyzer

class CppAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("cpp")
        self.c_analyzer = CAnalyzer()

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        c_issues, metrics = self.c_analyzer.analyze(source_code, filename)
        issues = [iss for iss in c_issues if "gets" in iss["rule"] or "strcpy" in iss["rule"]]
        lines = source_code.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            if re.search(r'(=|\(|,)\s*NULL\b', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "Modern-Cpp-CoreGuidelines",
                    "rule": "modernize-use-nullptr",
                    "message": "Use of NULL macro in C++. Prefer type-safe 'nullptr'.",
                    "source": stripped,
                    "suggested_fix": "Replace NULL with nullptr."
                })

            if re.search(r'\bnew\s+\w+', stripped) and "unique_ptr" not in stripped:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "MEDIUM",
                    "category": "maintainability",
                    "tool": "Modern-Cpp-CoreGuidelines",
                    "rule": "avoid-raw-new",
                    "message": "Raw 'new' operator used. Modern C++ favors std::make_unique or std::make_shared for RAII.",
                    "source": stripped,
                    "suggested_fix": "Use std::make_unique<T>() to avoid manual memory leaks."
                })

            if re.search(r'\(\s*(int|float|double|char|long)\s*\)\s*\w+', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "Clang-Tidy-Cpp",
                    "rule": "cppcoreguidelines-pro-type-cstyle-cast",
                    "message": "C-style cast used in C++. Prefer static_cast or explicit constructors.",
                    "source": stripped,
                    "suggested_fix": "Replace with static_cast<type>(expression)."
                })

            if re.match(r'using\s+namespace\s+std;', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "INFO",
                    "category": "style",
                    "tool": "Modern-Cpp-CoreGuidelines",
                    "rule": "avoid-using-namespace-std",
                    "message": "'using namespace std;' causes global symbol collisions, especially in headers.",
                    "source": stripped,
                    "suggested_fix": "Scope explicitly with std:: prefix or import specific symbols."
                })

        return issues, metrics
