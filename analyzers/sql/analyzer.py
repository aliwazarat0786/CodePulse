"""
SQL & Database Analyzer for CodePulse AI.
Supports ANSI SQL, PostgreSQL (PL/pgSQL), MySQL, SQLite, and database query security analysis.
"""
import re
import math
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer

class SQLAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("sql")

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = source_code.splitlines()
        loc = max(1, len(lines))
        comment_lines = 0
        branch_count = 0

        code_upper = source_code.upper()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            upper_line = stripped.upper()

            if stripped.startswith(("--", "/*", "*")):
                comment_lines += 1
                continue

            # Branch & Complexity detection in SQL
            if re.search(r'\b(CASE|WHEN|IF|ELSE|WHILE|LOOP|EXCEPTION|UNION|INTERSECT)\b', upper_line):
                branch_count += 1

            # 1. Unsafe DELETE / UPDATE without WHERE clause
            if re.search(r'^\s*DELETE\s+FROM\s+\w+\s*;?$', stripped, re.IGNORECASE) or (
                re.search(r'\bDELETE\s+FROM\s+\w+', upper_line) and "WHERE" not in code_upper
            ):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "bug-risk",
                    "tool": "SQL-Safety-Linter",
                    "rule": "unbounded-delete",
                    "message": "DELETE statement without a WHERE clause will truncate/delete all rows in the table.",
                    "source": stripped,
                    "suggested_fix": "Add a specific WHERE clause with primary key or boundary conditions."
                })

            if re.search(r'^\s*UPDATE\s+\w+\s+SET\s+[^;]+;?$', stripped, re.IGNORECASE) and "WHERE" not in upper_line and "WHERE" not in code_upper:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "bug-risk",
                    "tool": "SQL-Safety-Linter",
                    "rule": "unbounded-update",
                    "message": "UPDATE statement without a WHERE clause will overwrite all records across the entire table.",
                    "source": stripped,
                    "suggested_fix": "Specify a WHERE condition to target only required rows."
                })

            # 2. Dynamic SQL Concatenation (SQL Injection in PL/pgSQL / Stored Procedures)
            if re.search(r'\bEXECUTE\s+[\'"].*?\|\|', stripped, re.IGNORECASE) or re.search(r'EXECUTE\s+format\s*\([^%]*?\+', stripped, re.IGNORECASE):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "PostgreSQL-Security-Audit",
                    "rule": "plpgsql-dynamic-sql-injection",
                    "message": "Dynamic SQL concatenation inside EXECUTE statement opens SQL Injection vulnerabilities.",
                    "source": stripped,
                    "suggested_fix": "Use parameterized queries with USING clause or format() with %I (identifier) and %L (literal)."
                })

            # 3. Plaintext Password Column in DDL
            if re.search(r'\b(password|passwd|secret|api_key|token)\s+(VARCHAR|TEXT|CHAR)\b', upper_line, re.IGNORECASE) and "HASH" not in upper_line and "ENCRYPT" not in upper_line:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "SQL-Schema-Audit",
                    "rule": "plaintext-password-column",
                    "message": "Column name suggests storage of plaintext credentials without cryptographic hashing.",
                    "source": stripped,
                    "suggested_fix": "Store salted hashes (e.g., bcrypt / Argon2) and rename column to password_hash."
                })

            # 4. Excessive Database Privileges
            if re.search(r'\bGRANT\s+ALL\s+(PRIVILEGES\s+)?ON\s+.*?\s+TO\s+(PUBLIC|\'\w+\'@\'%\')', upper_line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "security",
                    "tool": "SQL-Security-Audit",
                    "rule": "excessive-privileges-grant",
                    "message": "GRANT ALL PRIVILEGES to PUBLIC violates the Principle of Least Privilege.",
                    "source": stripped,
                    "suggested_fix": "Grant only required permissions (SELECT, INSERT, UPDATE) to specific application roles."
                })

            # 5. Dangerous DROP / TRUNCATE
            if re.search(r'\bDROP\s+(DATABASE|SCHEMA|TABLE)\s+.*?CASCADE\b', upper_line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "HIGH",
                    "category": "bug-risk",
                    "tool": "SQL-Safety-Linter",
                    "rule": "destructive-drop-cascade",
                    "message": "DROP ... CASCADE will recursively drop all dependent views, foreign keys, and constraints.",
                    "source": stripped,
                    "suggested_fix": "Drop specific objects explicitly and verify dependency tree beforehand."
                })

            # 6. Performance: SELECT * in queries with JOINs
            if re.search(r'\bSELECT\s+\*\s+FROM\b', upper_line) and "JOIN" in code_upper:
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "LOW",
                    "category": "code-quality",
                    "tool": "SQL-Performance-Optimizer",
                    "rule": "avoid-select-star-in-joins",
                    "message": "Use of 'SELECT *' across multi-table JOINs transfers unneeded columns and defeats index-only scans.",
                    "source": stripped,
                    "suggested_fix": "Explicitly project only required column names."
                })

            # 7. Unsafe MD5 or SHA1 in SQL expressions
            if re.search(r'\b(MD5|SHA1)\s*\(', upper_line):
                issues.append({
                    "line": idx,
                    "column": 0,
                    "severity": "MEDIUM",
                    "category": "security",
                    "tool": "SQL-Security-Audit",
                    "rule": "weak-hash-function-sql",
                    "message": "MD5/SHA1 is cryptographically broken and prone to collision attacks.",
                    "source": stripped,
                    "suggested_fix": "Use SHA256 (SHA2) or pgcrypto extension with crypt() for sensitive data."
                })

        # Count queries / statements / procedures
        statements = max(1, len(re.findall(r';|\bCREATE\s+(TABLE|FUNCTION|PROCEDURE|VIEW|INDEX)\b', source_code, re.IGNORECASE)))
        cc = max(1.0, round(1.0 + (branch_count / statements), 1))

        comment_ratio = comment_lines / loc
        mi = max(30.0, min(100.0, round(100.0 - (cc * 2.8) - (math.log(loc + 1) * 2.0) + (comment_ratio * 12.0), 1)))

        return issues, {
            "cyclomatic_complexity": cc,
            "maintainability_index": mi
        }
