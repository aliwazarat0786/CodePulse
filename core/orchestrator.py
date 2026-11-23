"""
Central Analysis Orchestrator for CodePulse AI.
Coordinates static analysis engines, dynamic sandboxed execution, ML classification,
AI semantic purpose inference, and remediation roadmap synthesis.
"""
import uuid
import datetime
from typing import Dict, Any, Optional, List

from core.language_detector import detect_language
from core.normalizer import IssueNormalizer
from core.deduplicator import IssueDeduplicator
from core.metrics import MetricsEngine
from models.schemas import AnalysisResult, Issue, ExecutionResult, ErrorType
from analyzers.python.analyzer import PythonAnalyzer
from analyzers.java.analyzer import JavaAnalyzer
from analyzers.c.analyzer import CAnalyzer
from analyzers.cpp.analyzer import CppAnalyzer
from analyzers.javascript.analyzer import JavaScriptAnalyzer
from analyzers.sql.analyzer import SQLAnalyzer
from utils.code_executor import CodeExecutor

class AnalysisOrchestrator:
    def __init__(self):
        self.analyzers = {
            "python": PythonAnalyzer(),
            "java": JavaAnalyzer(),
            "c": CAnalyzer(),
            "cpp": CppAnalyzer(),
            "javascript": JavaScriptAnalyzer(),
            "sql": SQLAnalyzer()
        }

    def analyze_code(
        self,
        source_code: str,
        filename: str = "example.py",
        requested_language: str = "auto",
        enable_ai: bool = True,
        execute_code: bool = False,
        execution_result: Optional[ExecutionResult] = None,
        version: int = 1,
        parent_analysis_id: Optional[str] = None
    ) -> AnalysisResult:
        analysis_id = str(uuid.uuid4())[:8]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        warnings = []
        tools_executed = []
        tools_unavailable = []

        detected_lang, confidence, reason = detect_language(filename, source_code, requested_language)
        
        if detected_lang not in self.analyzers:
            warnings.append(f"Language '{detected_lang}' not fully supported. Defaulting to Python pipeline.")
            detected_lang = "python"

        analyzer = self.analyzers[detected_lang]
        tools_executed.append(f"{detected_lang.upper()} Pipeline")

        raw_issues = []
        metrics_dict = {"cyclomatic_complexity": 1.0, "maintainability_index": 80.0}

        try:
            raw_issues, metrics_dict = analyzer.analyze(source_code, filename)
        except Exception as e:
            warnings.append(f"Analyzer pipeline encountered partial error: {str(e)}")

        normalized_issues = IssueNormalizer.normalize(raw_issues, detected_lang, filename)

        # Step 3: Optional Code Execution
        exec_res = execution_result
        if execute_code and exec_res is None:
            try:
                exec_res = CodeExecutor.execute(
                    source_code=source_code,
                    language=detected_lang,
                    filename=filename
                )
                tools_executed.append("CodePulse Execution Sandbox")
            except Exception as e:
                warnings.append(f"Execution sandbox error: {str(e)}")

        # If execution encountered a runtime or compilation error, synthesize a high-priority Issue
        if exec_res and exec_res.status in ["FAILED", "COMPILATION_ERROR", "TIMEOUT"]:
            err_line = exec_res.error_line or 1
            source_lines = source_code.splitlines()
            line_snip = source_lines[err_line - 1].strip() if 0 < err_line <= len(source_lines) else ""
            
            err_type = exec_res.error_type or ("SYNTAX_ERROR" if exec_res.status == "COMPILATION_ERROR" else "RUNTIME_ERROR")
            err_msg = exec_res.error_message or exec_res.stderr.strip().splitlines()[-1] if exec_res.stderr else "Runtime execution error"

            runtime_issue = Issue(
                id=f"CP-RT-{uuid.uuid4().hex[:4].upper()}",
                language=detected_lang,
                file=filename,
                line=err_line,
                column=exec_res.error_column or 0,
                severity="CRITICAL",
                category="runtime" if exec_res.status != "COMPILATION_ERROR" else "syntax",
                tool="Runtime-Execution-Engine",
                rule="runtime-execution-failure" if exec_res.status != "COMPILATION_ERROR" else "compilation-syntax-error",
                message=f"[{err_type}] {err_msg}",
                source=line_snip,
                source_snippet=line_snip,
                description=exec_res.stderr,
                confidence=1.0,
                suggested_fix="Review error diagnostic and apply suggested AI fix.",
                error_type=err_type,
                evidence=exec_res.stderr,
                runtime_evidence=exec_res.stderr,
                root_cause=err_msg
            )
            normalized_issues.insert(0, runtime_issue)

        deduped_issues = IssueDeduplicator.deduplicate(normalized_issues)

        metrics, summary = MetricsEngine.compute(
            source_code=source_code,
            language=detected_lang,
            issues=deduped_issues,
            cyclomatic_complexity=metrics_dict.get("cyclomatic_complexity", 1.0),
            maintainability_index=metrics_dict.get("maintainability_index", 80.0)
        )

        # Step 7: ML Vulnerability Classifier
        ml_prediction = {}
        try:
            from ml.predictor import MLVulnerabilityPredictor
            ml_pred = MLVulnerabilityPredictor()
            ml_prediction = ml_pred.predict(source_code, detected_lang)
            tools_executed.append("CodePulse ML Classifier")
        except Exception as e:
            warnings.append(f"ML Classifier notice: {str(e)}")

        # Step 8: Code Intelligence & Purpose Explanation
        code_purpose = {}
        refactoring_roadmap = {}
        try:
            from core.code_explainer import CodeExplainer
            code_purpose = CodeExplainer.infer_code_purpose(source_code, detected_lang, filename)
            refactoring_roadmap = CodeExplainer.generate_remediation_roadmap(
                issues=deduped_issues,
                summary=summary,
                metrics=metrics,
                language=detected_lang
            )
            tools_executed.append("CodePulse Semantic Purpose & Roadmap Engine")
        except Exception as e:
            warnings.append(f"Code Explainer notice: {str(e)}")

        # Step 9: LLM Layer (Enrich important issues)
        ai_summary = None
        if enable_ai:
            try:
                from llm.analyzer import LLMAnalyzer
                ai_analyzer = LLMAnalyzer()
                deduped_issues, ai_summary = ai_analyzer.enrich_issues(
                    issues=deduped_issues,
                    source_code=source_code,
                    language=detected_lang,
                    quality_score=summary.quality_score
                )
                tools_executed.append("CodePulse AI Explainer")
            except Exception as e:
                warnings.append(f"AI Interpretation layer notice: {str(e)}")

        result = AnalysisResult(
            analysis_id=analysis_id,
            filename=filename,
            language=detected_lang,
            timestamp=timestamp,
            summary=summary,
            metrics=metrics,
            issues=deduped_issues,
            warnings=warnings,
            ai_summary=ai_summary,
            ml_prediction=ml_prediction,
            code_purpose=code_purpose,
            refactoring_roadmap=refactoring_roadmap,
            tools_executed=tools_executed,
            tools_unavailable=tools_unavailable,
            execution=exec_res,
            version=version,
            parent_analysis_id=parent_analysis_id,
            source_code=source_code
        )

        return result
