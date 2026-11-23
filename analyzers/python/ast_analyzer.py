"""
Native Python AST Analyzer.
"""
import ast
from typing import List, Dict, Any

class PythonASTAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code: str, filename: str):
        self.source_code = source_code
        self.filename = filename
        self.lines = source_code.splitlines()
        self.issues: List[Dict[str, Any]] = []
        self.imported_names: Dict[str, int] = {}
        self.used_names: set = set()
        self.assigned_vars: Dict[str, int] = {}
        self.current_nesting = 0

    def _get_line_source(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            if not node.id.startswith("_"):
                self.assigned_vars[node.id] = node.lineno
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Framework & Library Specific Security Inspections
        if func_name in ["eval", "exec"]:
            sev = "CRITICAL"
            self.issues.append({
                "line": node.lineno,
                "column": node.col_offset,
                "severity": sev,
                "category": "security",
                "tool": "AST-Analyzer",
                "rule": f"unsafe-{func_name}",
                "message": f"Dynamic code execution via {func_name}() detected. Major Remote Code Execution risk.",
                "source": self._get_line_source(node.lineno),
                "suggested_fix": "Avoid dynamic code execution. Parse structured data using json / ast.literal_eval."
            })

        # Flask Server-Side Template Injection (SSTI)
        elif func_name == "render_template_string":
            self.issues.append({
                "line": node.lineno,
                "column": node.col_offset,
                "severity": "CRITICAL",
                "category": "security",
                "tool": "Flask-Security-Linter",
                "rule": "flask-ssti-vulnerability",
                "message": "render_template_string() with dynamic input leads to Server-Side Template Injection (SSTI).",
                "source": self._get_line_source(node.lineno),
                "suggested_fix": "Use render_template() with static Jinja2 template files instead."
            })

        # Django mark_safe XSS
        elif func_name == "mark_safe":
            self.issues.append({
                "line": node.lineno,
                "column": node.col_offset,
                "severity": "HIGH",
                "category": "security",
                "tool": "Django-Security-Linter",
                "rule": "django-mark-safe-xss",
                "message": "mark_safe() bypasses Django's autoescaping, exposing HTML/JS to Cross-Site Scripting (XSS).",
                "source": self._get_line_source(node.lineno),
                "suggested_fix": "Sanitize user inputs with bleach or escape HTML before marking safe."
            })

        # Django / SQLAlchemy raw SQL execution
        elif func_name in ["raw", "extra", "execute"]:
            if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.BinOp)):
                self.issues.append({
                    "line": node.lineno,
                    "column": node.col_offset,
                    "severity": "CRITICAL",
                    "category": "security",
                    "tool": "SQL-Injection-Linter",
                    "rule": "orm-raw-sql-injection",
                    "message": f"Formatted string passed to database query '{func_name}()'. Critical SQL Injection vulnerability.",
                    "source": self._get_line_source(node.lineno),
                    "suggested_fix": "Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = %s', [id])."
                })

        # Flask app.run(debug=True)
        elif func_name == "run":
            for kw in node.keywords:
                if kw.arg == "debug" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.issues.append({
                        "line": node.lineno,
                        "column": node.col_offset,
                        "severity": "HIGH",
                        "category": "security",
                        "tool": "Flask-Security-Linter",
                        "rule": "flask-debug-enabled-in-run",
                        "message": "Flask debug mode enabled in app.run(). Allows arbitrary debugger PIN code execution.",
                        "source": self._get_line_source(node.lineno),
                        "suggested_fix": "Disable debug mode (debug=False) and run behind production WSGI/ASGI servers (Gunicorn/Uvicorn)."
                    })

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # Check hardcoded SECRET_KEY or DEBUG = True in settings
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name in ["SECRET_KEY", "DJANGO_SECRET_KEY", "JWT_SECRET"]:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        self.issues.append({
                            "line": node.lineno,
                            "column": node.col_offset,
                            "severity": "CRITICAL",
                            "category": "security",
                            "tool": "Django-Security-Linter",
                            "rule": "hardcoded-framework-secret-key",
                            "message": f"Hardcoded secret token in '{var_name}'. Exposed credentials compromise cryptographic signatures.",
                            "source": self._get_line_source(node.lineno),
                            "suggested_fix": f"Load from environment variable: os.environ.get('{var_name}')"
                        })
                elif var_name == "DEBUG" and isinstance(node.value, ast.Constant) and node.value.value is True:
                    self.issues.append({
                        "line": node.lineno,
                        "column": node.col_offset,
                        "severity": "MEDIUM",
                        "category": "security",
                        "tool": "Django-Security-Linter",
                        "rule": "django-debug-true-in-settings",
                        "message": "DEBUG = True exposes stack traces and environment metadata in error pages.",
                        "source": self._get_line_source(node.lineno),
                        "suggested_fix": "Set DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'"
                    })
        self.generic_visit(node)

    def _check_nesting(self, node):
        self.current_nesting += 1
        if self.current_nesting > 3:
            self.issues.append({
                "line": getattr(node, "lineno", 1),
                "column": getattr(node, "col_offset", 0),
                "severity": "MEDIUM",
                "category": "complexity",
                "tool": "AST-Analyzer",
                "rule": "excessive-nesting",
                "message": f"Block nesting level ({self.current_nesting}) exceeds recommended depth (max 3).",
                "source": self._get_line_source(getattr(node, "lineno", 1)),
                "suggested_fix": "Refactor nested loops/conditionals using guard clauses or helper functions."
            })
        self.generic_visit(node)
        self.current_nesting -= 1

    def visit_If(self, node: ast.If):
        self._check_nesting(node)

    def visit_For(self, node: ast.For):
        self._check_nesting(node)

    def visit_While(self, node: ast.While):
        self._check_nesting(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        fn_lines = (node.end_lineno - node.lineno) if hasattr(node, "end_lineno") else 1
        if fn_lines > 60:
            self.issues.append({
                "line": node.lineno,
                "column": node.col_offset,
                "severity": "LOW",
                "category": "maintainability",
                "tool": "AST-Analyzer",
                "rule": "large-function",
                "message": f"Function '{node.name}' is too long ({fn_lines} lines > 60 threshold).",
                "source": self._get_line_source(node.lineno),
                "suggested_fix": "Decompose large function into smaller, single-responsibility units."
            })

        if not ast.get_docstring(node):
            self.issues.append({
                "line": node.lineno,
                "column": node.col_offset,
                "severity": "INFO",
                "category": "style",
                "tool": "AST-Analyzer",
                "rule": "missing-docstring",
                "message": f"Function '{node.name}' has no docstring documentation.",
                "source": self._get_line_source(node.lineno),
                "suggested_fix": "Add a descriptive docstring summarizing parameters and return types."
            })

        self.generic_visit(node)

    def run(self) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(self.source_code, filename=self.filename)
            self.visit(tree)

            for name, lineno in self.imported_names.items():
                if name not in self.used_names and not name.startswith("_"):
                    self.issues.append({
                        "line": lineno,
                        "column": 0,
                        "severity": "LOW",
                        "category": "code-quality",
                        "tool": "AST-Analyzer",
                        "rule": "unused-import",
                        "message": f"Imported module or symbol '{name}' is never used.",
                        "source": self._get_line_source(lineno),
                        "suggested_fix": f"Remove unused import '{name}'."
                    })

        except SyntaxError as e:
            self.issues.append({
                "line": e.lineno or 1,
                "column": e.offset or 0,
                "severity": "CRITICAL",
                "category": "bug-risk",
                "tool": "AST-Analyzer",
                "rule": "syntax-error",
                "message": f"Python Syntax Error: {e.msg}",
                "source": self._get_line_source(e.lineno or 1),
                "suggested_fix": "Correct the syntax error before proceeding."
            })
        except Exception as e:
            self.issues.append({
                "line": 1,
                "column": 0,
                "severity": "HIGH",
                "category": "bug-risk",
                "tool": "AST-Analyzer",
                "rule": "ast-parsing-failure",
                "message": f"Failed to parse AST: {str(e)}",
                "source": ""
            })

        return self.issues

