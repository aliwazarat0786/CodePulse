"""
Report Comparison Engine for CodePulse AI.
Calculates deterministic deltas between original and re-analyzed codebases:
- Score change (e.g. 64 -> 91, +27 points)
- Resolved issues
- Remaining issues
- Newly introduced issues
- Metrics comparison table
"""
import uuid
import datetime
from typing import Dict, Any, List, Optional
from models.schemas import AnalysisResult, ReportComparison, CodeComparison
from core.diff_engine import DiffEngine

class ReportComparator:
    @classmethod
    def compare(
        cls,
        original_result: AnalysisResult,
        fixed_result: AnalysisResult,
        verification_data: Optional[Dict[str, Any]] = None,
        original_code: str = "",
        fixed_code: str = ""
    ) -> ReportComparison:
        comparison_id = f"cmp_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        score_before = original_result.summary.quality_score
        score_after = fixed_result.summary.quality_score
        score_delta = score_after - score_before

        orig_issues = [i.to_dict() for i in original_result.issues]
        fixed_issues = [i.to_dict() for i in fixed_result.issues]

        resolved_issues: List[Dict[str, Any]] = []
        remaining_issues: List[Dict[str, Any]] = []
        new_issues: List[Dict[str, Any]] = []

        # Match issues by rule and relative line position
        matched_orig_indices = set()
        matched_fixed_indices = set()

        # Step 1: Exact matches (same rule and same line)
        for o_idx, o_iss in enumerate(orig_issues):
            for f_idx, f_iss in enumerate(fixed_issues):
                if f_idx in matched_fixed_indices:
                    continue
                if o_iss.get("rule") == f_iss.get("rule") and o_iss.get("line") == f_iss.get("line"):
                    remaining_issues.append(f_iss)
                    matched_orig_indices.add(o_idx)
                    matched_fixed_indices.add(f_idx)
                    break

        # Step 2: Near matches (same rule, line within 3 lines)
        for o_idx, o_iss in enumerate(orig_issues):
            if o_idx in matched_orig_indices:
                continue
            for f_idx, f_iss in enumerate(fixed_issues):
                if f_idx in matched_fixed_indices:
                    continue
                if o_iss.get("rule") == f_iss.get("rule") and abs(o_iss.get("line", 0) - f_iss.get("line", 0)) <= 3:
                    remaining_issues.append(f_iss)
                    matched_orig_indices.add(o_idx)
                    matched_fixed_indices.add(f_idx)
                    break

        # Step 3: Resolved are original issues that were not found in fixed code
        for o_idx, o_iss in enumerate(orig_issues):
            if o_idx not in matched_orig_indices:
                resolved_issues.append(o_iss)

        # Step 4: New issues are fixed issues that were not in original code
        for f_idx, f_iss in enumerate(fixed_issues):
            if f_idx not in matched_fixed_indices:
                new_issues.append(f_iss)

        # Metrics comparison map
        metrics_comparison = {
            "quality_score": {
                "label": "Code Quality Score",
                "before": score_before,
                "after": score_after,
                "delta": score_delta,
                "improved": score_delta >= 0
            },
            "lines_of_code": {
                "label": "Lines of Code",
                "before": original_result.metrics.lines_of_code,
                "after": fixed_result.metrics.lines_of_code,
                "delta": fixed_result.metrics.lines_of_code - original_result.metrics.lines_of_code
            },
            "cyclomatic_complexity": {
                "label": "Cyclomatic Complexity",
                "before": original_result.metrics.cyclomatic_complexity or 1.0,
                "after": fixed_result.metrics.cyclomatic_complexity or 1.0,
                "delta": round((fixed_result.metrics.cyclomatic_complexity or 1.0) - (original_result.metrics.cyclomatic_complexity or 1.0), 1),
                "improved": (fixed_result.metrics.cyclomatic_complexity or 1.0) <= (original_result.metrics.cyclomatic_complexity or 1.0)
            },
            "maintainability_index": {
                "label": "Maintainability Index",
                "before": original_result.metrics.maintainability_index or 80.0,
                "after": fixed_result.metrics.maintainability_index or 80.0,
                "delta": round((fixed_result.metrics.maintainability_index or 80.0) - (original_result.metrics.maintainability_index or 80.0), 1),
                "improved": (fixed_result.metrics.maintainability_index or 80.0) >= (original_result.metrics.maintainability_index or 80.0)
            },
            "critical_issues": {
                "label": "Critical Vulnerabilities",
                "before": original_result.summary.critical,
                "after": fixed_result.summary.critical,
                "delta": fixed_result.summary.critical - original_result.summary.critical,
                "improved": fixed_result.summary.critical <= original_result.summary.critical
            },
            "high_issues": {
                "label": "High-Risk Defects",
                "before": original_result.summary.high,
                "after": fixed_result.summary.high,
                "delta": fixed_result.summary.high - original_result.summary.high,
                "improved": fixed_result.summary.high <= original_result.summary.high
            },
            "total_issues": {
                "label": "Total Findings",
                "before": len(orig_issues),
                "after": len(fixed_issues),
                "delta": len(fixed_issues) - len(orig_issues),
                "improved": len(fixed_issues) <= len(orig_issues)
            }
        }

        # Code Diff
        code_comp = None
        if original_code and fixed_code:
            code_comp = DiffEngine.compare_code(original_code, fixed_code).to_dict()

        return ReportComparison(
            comparison_id=comparison_id,
            original_analysis_id=original_result.analysis_id,
            fixed_analysis_id=fixed_result.analysis_id,
            timestamp=timestamp,
            score_before=score_before,
            score_after=score_after,
            score_delta=score_delta,
            grade_before=original_result.summary.score_grade,
            grade_after=fixed_result.summary.score_grade,
            total_issues_before=len(orig_issues),
            total_issues_after=len(fixed_issues),
            resolved_issues=resolved_issues,
            remaining_issues=remaining_issues,
            new_issues=new_issues,
            metrics_comparison=metrics_comparison,
            execution_before=original_result.execution.to_dict() if original_result.execution else None,
            execution_after=fixed_result.execution.to_dict() if fixed_result.execution else None,
            verification=verification_data or {},
            code_comparison=code_comp
        )
