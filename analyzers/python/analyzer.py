"""
Unified Python Analyzer.
"""
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseAnalyzer
from analyzers.python.ast_analyzer import PythonASTAnalyzer
from analyzers.python.radon_adapter import RadonAdapter
from analyzers.python.bandit_adapter import BanditAdapter
from analyzers.python.pylint_adapter import PylintAdapter

class PythonAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("python")

    def analyze(self, source_code: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        all_issues: List[Dict[str, Any]] = []

        # 1. AST Analysis
        ast_checker = PythonASTAnalyzer(source_code, filename)
        ast_issues = ast_checker.run()
        all_issues.extend(ast_issues)

        # 2. Radon Metrics & Complexity
        radon_issues, metrics = RadonAdapter.analyze(source_code)
        all_issues.extend(radon_issues)

        # 3. Bandit Security
        bandit_issues = BanditAdapter.analyze(source_code, filename)
        all_issues.extend(bandit_issues)

        # 4. Pylint Quality
        pylint_issues = PylintAdapter.analyze(source_code, filename)
        all_issues.extend(pylint_issues)

        return all_issues, metrics
