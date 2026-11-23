"""
Unit tests for Python AST & analyzers.
"""
import pytest
from analyzers.python.ast_analyzer import PythonASTAnalyzer
from analyzers.python.analyzer import PythonAnalyzer

def test_unused_import_detection():
    code = "import os\nimport sys\nx = 10\nprint(x)"
    analyzer = PythonASTAnalyzer(code, "test.py")
    issues = analyzer.run()
    
    unused_rules = [i["rule"] for i in issues]
    assert "unused-import" in unused_rules

def test_unsafe_eval_detection():
    code = "def run(cmd):\n    return eval(cmd)"
    analyzer = PythonASTAnalyzer(code, "test.py")
    issues = analyzer.run()
    
    rules = [i["rule"] for i in issues]
    assert "unsafe-eval" in rules

def test_excessive_nesting():
    code = """
def deeply_nested():
    if True:
        if True:
            if True:
                if True:
                    print("Deep")
"""
    analyzer = PythonASTAnalyzer(code, "test.py")
    issues = analyzer.run()
    rules = [i["rule"] for i in issues]
    assert "excessive-nesting" in rules

def test_full_python_pipeline():
    code = """
import os
password = "super_secret_123"

def compute():
    x = eval("2 + 2")
    return x
"""
    analyzer = PythonAnalyzer()
    issues, metrics = analyzer.analyze(code, "test.py")
    assert len(issues) > 0
    assert "cyclomatic_complexity" in metrics
