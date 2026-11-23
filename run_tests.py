"""
Built-in Comprehensive Test Runner for CodePulse AI
Tests static analysis, sandboxed execution, exact error diagnostics,
AI fixation, backend verification, diff engine, report comparisons, and API routes.
"""
import sys
import unittest
from core.language_detector import detect_language
from analyzers.python.ast_analyzer import PythonASTAnalyzer
from analyzers.python.analyzer import PythonAnalyzer
from analyzers.java.analyzer import JavaAnalyzer
from analyzers.c.analyzer import CAnalyzer
from analyzers.cpp.analyzer import CppAnalyzer
from analyzers.javascript.analyzer import JavaScriptAnalyzer
from analyzers.sql.analyzer import SQLAnalyzer
from core.normalizer import IssueNormalizer
from core.deduplicator import IssueDeduplicator
from core.metrics import MetricsEngine
from core.code_explainer import CodeExplainer
from core.diff_engine import DiffEngine
from core.report_comparator import ReportComparator
from utils.code_executor import CodeExecutor
from llm.fixer import AIFixer
from models.schemas import Issue, ExecutionResult
from app import create_app

class TestCodePulseFull(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(detect_language("script.py", "")[0], "python")
        self.assertEqual(detect_language("Main.java", "")[0], "java")
        self.assertEqual(detect_language("test.c", "")[0], "c")
        self.assertEqual(detect_language("engine.cpp", "")[0], "cpp")
        self.assertEqual(detect_language("app.js", "")[0], "javascript")
        self.assertEqual(detect_language("schema.sql", "")[0], "sql")
        self.assertEqual(detect_language("migration.pgsql", "")[0], "sql")

        py_snippet = "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef index(): return 'ok'"
        self.assertEqual(detect_language("", py_snippet)[0], "python")

        js_snippet = "import React, { useState } from 'react'; export default function Widget() { const [c, setC] = useState(0); return <div className='w'>{c}</div>; }"
        self.assertEqual(detect_language("", js_snippet)[0], "javascript")

        sql_snippet = "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50)); DELETE FROM users;"
        self.assertEqual(detect_language("", sql_snippet)[0], "sql")

    def test_code_executor_python_success(self):
        code = "print('CodePulse Execution Success')\nx = 10 + 32\nprint(f'Total: {x}')"
        res = CodeExecutor.execute(code, "python", "test.py")
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Total: 42", res.stdout)

    def test_code_executor_python_syntax_error(self):
        code = "def calculate(a, b):\n    print(a / b"
        res = CodeExecutor.execute(code, "python", "syntax.py")
        self.assertEqual(res.status, "COMPILATION_ERROR")
        self.assertEqual(res.error_type, "SYNTAX_ERROR")
        self.assertEqual(res.error_line, 2)
        self.assertIn("Syntax", res.stderr)

    def test_code_executor_python_runtime_error(self):
        code = "a = 10\nb = 0\nprint(a / b)"
        res = CodeExecutor.execute(code, "python", "zero.py")
        self.assertEqual(res.status, "FAILED")
        self.assertEqual(res.error_type, "DIVISION_BY_ZERO")
        self.assertEqual(res.error_line, 3)

    def test_code_executor_timeout(self):
        code = "import time\nwhile True:\n    time.sleep(0.1)"
        res = CodeExecutor.execute(code, "python", "loop.py", timeout_sec=1)
        self.assertEqual(res.status, "TIMEOUT")
        self.assertTrue(res.timed_out)

    def test_code_executor_sql_sandbox(self):
        code = "CREATE TABLE users (id INT PRIMARY KEY, name TEXT); INSERT INTO users VALUES (1, 'Alice');"
        res = CodeExecutor.execute(code, "sql", "query.sql")
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.exit_code, 0)

    def test_ai_fixer_and_verification(self):
        code = "def calculate(a, b):\n    result = a / b\n    print(result\n\ncalculate(10, 0)"
        issues = [
            Issue(id="CP-001", language="python", file="demo.py", line=3, column=10, severity="CRITICAL", category="syntax", tool="AST", rule="syntax-error", message="Missing closing parenthesis"),
            Issue(id="CP-002", language="python", file="demo.py", line=2, column=13, severity="HIGH", category="runtime", tool="Runtime", rule="zero-division", message="Division by zero")
        ]

        fixer = AIFixer()
        fixed_code, fix_results = fixer.generate_fix(code, "python", issues, selected_issue_ids=["CP-001"], fix_all=False)
        self.assertIn("print(result)", fixed_code)
        self.assertGreaterEqual(len(fix_results), 1)

    def test_diff_engine(self):
        orig = "def add(a, b):\n    return a + b\n"
        fixed = "def add(a, b):\n    # docstring\n    return a + b\n"
        diff = DiffEngine.compare_code(orig, fixed)
        self.assertGreater(diff.total_additions, 0)
        self.assertIn("+", diff.diff_unified)

    def test_report_comparator(self):
        flask_app = create_app()
        orchestrator = flask_app.config.get("ORCHESTRATOR")
        from core.orchestrator import AnalysisOrchestrator
        orch = AnalysisOrchestrator()

        orig_code = "def calc(a, b):\n    print(a / b"
        fixed_code = "def calc(a, b):\n    if b != 0:\n        print(a / b)\n    else:\n        print(0)\n\ncalc(10, 2)"

        res1 = orch.analyze_code(orig_code, "test.py", "python", enable_ai=False, execute_code=True)
        res2 = orch.analyze_code(fixed_code, "test.py", "python", enable_ai=False, execute_code=True)

        comp = ReportComparator.compare(res1, res2, original_code=orig_code, fixed_code=fixed_code)
        self.assertGreater(comp.score_after, comp.score_before)
        self.assertGreater(comp.score_delta, 0)
        self.assertIn("quality_score", comp.metrics_comparison)

    def test_api_workflow(self):
        flask_app = create_app()
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            # 1. Health
            res = client.get("/api/health")
            self.assertEqual(res.status_code, 200)

            # 2. Execute
            exec_payload = {
                "source_code": "print('API Execution Test')",
                "language": "python"
            }
            res_exec = client.post("/api/execute", json=exec_payload)
            self.assertEqual(res_exec.status_code, 200)
            self.assertEqual(res_exec.get_json()["execution"]["status"], "SUCCESS")

            # 3. Analyze + Run
            ar_payload = {
                "source_code": "def run():\n    x = 10\n    return x\nprint(run())",
                "language": "python",
                "filename": "run.py",
                "enable_ai": True
            }
            res_ar = client.post("/api/analyze-and-run", json=ar_payload)
            self.assertEqual(res_ar.status_code, 200)
            data_ar = res_ar.get_json()
            self.assertIn("execution", data_ar["analysis"])
            orig_id = data_ar["analysis"]["analysis_id"]

            # 4. AI Fix
            fix_payload = {
                "source_code": "def divide(a, b):\n    return a / b",
                "language": "python",
                "analysis_id": orig_id,
                "fix_all": True
            }
            res_fix = client.post("/api/ai/fix", json=fix_payload)
            self.assertEqual(res_fix.status_code, 200)
            fix_data = res_fix.get_json()
            self.assertIn("candidate_fixed_code", fix_data)
            self.assertIn("verification", fix_data)

            # 5. Re-analyze & Report Comparison
            re_payload = {
                "source_code": fix_data["candidate_fixed_code"],
                "original_analysis_id": orig_id,
                "original_code": "def divide(a, b):\n    return a / b",
                "language": "python"
            }
            res_re = client.post("/api/reanalyze", json=re_payload)
            self.assertEqual(res_re.status_code, 200)
            re_data = res_re.get_json()
            self.assertIn("comparison", re_data)
            cmp_id = re_data["comparison"]["comparison_id"]

            # 6. Download Comparison Report
            res_cmp_html = client.get(f"/api/report/comparison/{cmp_id}?format=html")
            self.assertEqual(res_cmp_html.status_code, 200)

            # 7. Download ZIP Package
            res_zip = client.get(f"/api/report/download-all/{cmp_id}")
            self.assertEqual(res_zip.status_code, 200)
            self.assertEqual(res_zip.mimetype, "application/zip")

if __name__ == "__main__":
    unittest.main(verbosity=2)
