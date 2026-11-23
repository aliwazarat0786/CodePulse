"""
JavaScript Analyzer for CodePulse AI.
"""
import re
import math
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer

class JavaScriptAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("javascript")

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = source_code.splitlines()
        loc = max(1, len(lines))
        branch_count = 0
        comment_lines = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            if stripped.startswith(("//", "/*", "*")):
                comment_lines += 1
                continue

            if re.search(r'\b(if|else if|for|while|case|catch)\b', stripped):
                branch_count += 1

            # 1. Core JS eval check
            if re.search(r'\beval\s*\(', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "ESLint-Adapter",
                    "rule": "no-eval",
                    "message": "eval() allows arbitrary code execution and opens XSS vulnerabilities.",
                    "source": stripped,
                    "suggested_fix": "Parse structured data with JSON.parse() instead of eval()."
                })

            # 2. React / Next.js dangerouslySetInnerHTML XSS
            if "dangerouslySetInnerHTML" in stripped:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "React-Security-Audit",
                    "rule": "react-dangerouslysetinnerhtml-xss",
                    "message": "dangerouslySetInnerHTML renders unescaped HTML directly to the DOM, creating Cross-Site Scripting (XSS) risks.",
                    "source": stripped,
                    "suggested_fix": "Sanitize HTML payload using DOMPurify before injecting: DOMPurify.sanitize(content)."
                })

            # 3. React href="javascript:..." pseudo-protocol
            if re.search(r'href\s*=\s*["\']javascript:', stripped, re.IGNORECASE):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "React-Security-Audit",
                    "rule": "react-javascript-url-xss",
                    "message": "Use of 'javascript:' URI in href/src triggers arbitrary script execution on click.",
                    "source": stripped,
                    "suggested_fix": "Use an onClick event handler with proper state dispatching instead of javascript: URI."
                })

            # 4. Node.js Command Injection in child_process
            if re.search(r'\b(exec|execSync)\s*\([^)]*?\+', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "NodeJS-Security-Audit",
                    "rule": "nodejs-command-injection",
                    "message": "String concatenation inside child_process.exec() leads to Remote Command Injection.",
                    "source": stripped,
                    "suggested_fix": "Use child_process.execFile() or spawn() with separate arguments array without shell: true."
                })

            # 5. MongoDB / Mongoose NoSQL Injection ($where / unsanitized query)
            if "$where" in stripped:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "MongoDB-Security-Audit",
                    "rule": "mongodb-nosql-where-injection",
                    "message": "Use of MongoDB '$where' clause allows JavaScript execution on the database server.",
                    "source": stripped,
                    "suggested_fix": "Replace $where with native MongoDB query operators ($eq, $in, $regex)."
                })

            # 6. Hardcoded JWT Secret / API Token in Express/Node
            if re.search(r'(jwt\.sign\s*\([^,]+,\s*["\'][^"\']{4,}["\']|const\s+(JWT_SECRET|SECRET_KEY)\s*=\s*["\'][^"\']{4,}["\'])', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "NodeJS-Security-Audit",
                    "rule": "hardcoded-jwt-secret",
                    "message": "Hardcoded JWT secret token detected. Compromised secrets allow token forgery.",
                    "source": stripped,
                    "suggested_fix": "Store secrets in process.env and load with dotenv/config."
                })

            # 7. Check loose equality '==' (avoiding '===', '!==', '<=', '>=')
            if re.search(r'(?<![!=<>])==(?![=])', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "ESLint-Adapter",
                    "rule": "eqeqeq",
                    "message": "Use of loose equality '=='. Type coercion may cause unexpected behavior.",
                    "source": stripped,
                    "suggested_fix": "Use strict equality '==='."
                })

            # 8. Variable declared with var
            if re.search(r'\bvar\s+[a-zA-Z_$]', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "ESLint-Adapter",
                    "rule": "no-var",
                    "message": "Variable declared with 'var' has function scope and hoisting anomalies. Use 'let' or 'const'.",
                    "source": stripped,
                    "suggested_fix": "Replace 'var' with 'const' (for immutable values) or 'let'."
                })

            # 9. console.log left in production
            if re.search(r'\bconsole\.(log|debug)\s*\(', stripped):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "INFO",
                    "category": "code-quality",
                    "tool": "ESLint-Adapter",
                    "rule": "no-console",
                    "message": "console.log left in production source code.",
                    "source": stripped,
                    "suggested_fix": "Remove console logging before deployment."
                })

        # Detect total functions & class methods for per-function cyclomatic complexity
        fn_patterns = [
            r'function\s+[\w$]+\s*\(',
            r'async\s+function\s+[\w$]+\s*\(',
            r'[\w$]+\s*=\s*(async\s*)?\([^)]*\)\s*=>',
            r'^\s*(async\s+)?[\w$]+\s*\([^)]*\)\s*\{'
        ]
        total_functions = 0
        for pat in fn_patterns:
            total_functions += len(re.findall(pat, source_code, re.MULTILINE))
        
        # If no explicit functions found, treat whole script as 1 execution block
        total_functions = max(1, total_functions)

        # Average cyclomatic complexity per function (McCabe standard)
        cc = max(1.0, round(1.0 + (branch_count / total_functions), 1))

        # Standard maintainability index calculation
        comment_ratio = comment_lines / loc
        mi = max(25.0, min(100.0, round(100.0 - (cc * 3.0) - (math.log(loc + 1) * 2.2) + (comment_ratio * 12.0), 1)))

        return issues, {
            "cyclomatic_complexity": cc,
            "maintainability_index": mi
        }
