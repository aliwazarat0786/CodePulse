"""
Metrics and Code Quality Score Engine for CodePulse AI.
"""
import re
from typing import List, Tuple
from config import Config
from models.schemas import Issue, Metrics, Summary, SeverityLevel, IssueCategory

class MetricsEngine:
    @staticmethod
    def calculate_loc_and_structure(source_code: str, language: str) -> Tuple[int, int, int, int, int]:
        lines = source_code.splitlines()
        loc = len(lines)
        blank = sum(1 for line in lines if not line.strip())
        
        comment = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if language == "python":
                if stripped.startswith("#"):
                    comment += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    comment += 1
            elif language == "sql":
                if stripped.startswith("--"):
                    comment += 1
                elif "/*" in stripped:
                    in_block_comment = True
                    comment += 1
                elif in_block_comment:
                    comment += 1
                    if "*/" in stripped:
                        in_block_comment = False
            else:
                if "/*" in stripped:
                    in_block_comment = True
                    comment += 1
                elif in_block_comment:
                    comment += 1
                    if "*/" in stripped:
                        in_block_comment = False
                elif stripped.startswith("//"):
                    comment += 1

        fn_count = 0
        cls_count = 0
        
        if language == "python":
            fn_count = len(re.findall(r'^\s*def\s+\w+', source_code, re.MULTILINE))
            cls_count = len(re.findall(r'^\s*class\s+\w+', source_code, re.MULTILINE))
        elif language == "sql":
            cls_count = len(re.findall(r'\bCREATE\s+(TABLE|VIEW|DATABASE|SCHEMA)\b', source_code, re.IGNORECASE))
            fn_count = len(re.findall(r'\bCREATE\s+(OR\s+REPLACE\s+)?(FUNCTION|PROCEDURE|TRIGGER)\b', source_code, re.IGNORECASE))
        elif language in ["java", "c", "cpp", "javascript"]:
            cls_count = len(re.findall(r'\bclass\s+\w+', source_code))
            fn_count = len(re.findall(r'\b(function\s+\w+|\w+\s+\w+\s*\([^;]*?\)\s*\{|const\s+\w+\s*=\s*(\([^)]*\)|[a-zA-Z_$]\w*)\s*=>)', source_code))

        return loc, blank, comment, fn_count, cls_count

    @classmethod
    def compute(
        cls,
        source_code: str,
        language: str,
        issues: List[Issue],
        cyclomatic_complexity: float = 1.0,
        maintainability_index: float = 100.0
    ) -> Tuple[Metrics, Summary]:
        loc, blank, comment, fn_count, cls_count = cls.calculate_loc_and_structure(source_code, language)

        crit = sum(1 for i in issues if i.severity == SeverityLevel.CRITICAL.value)
        high = sum(1 for i in issues if i.severity == SeverityLevel.HIGH.value)
        med = sum(1 for i in issues if i.severity == SeverityLevel.MEDIUM.value)
        low = sum(1 for i in issues if i.severity == SeverityLevel.LOW.value)
        info = sum(1 for i in issues if i.severity == SeverityLevel.INFO.value)

        sec = sum(1 for i in issues if i.category == IssueCategory.SECURITY.value)
        comp = sum(1 for i in issues if i.category == IssueCategory.COMPLEXITY.value)
        qual = len(issues) - sec - comp

        metrics = Metrics(
            lines_of_code=loc,
            blank_lines=blank,
            comment_lines=comment,
            cyclomatic_complexity=round(cyclomatic_complexity, 1),
            maintainability_index=round(maintainability_index, 1),
            functions_count=fn_count,
            classes_count=cls_count,
            total_issues=len(issues),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            info_count=info,
            security_count=sec,
            quality_count=qual,
            complexity_count=comp
        )

        penalty = (
            crit * Config.WEIGHT_CRITICAL +
            high * Config.WEIGHT_HIGH +
            med * Config.WEIGHT_MEDIUM +
            low * Config.WEIGHT_LOW +
            sec * Config.WEIGHT_SECURITY_PENALTY
        )
        
        if cyclomatic_complexity > 10:
            penalty += (cyclomatic_complexity - 10) * 1.5

        raw_score = 100.0 - penalty
        score = max(0, min(100, int(round(raw_score))))

        if score >= 90:
            grade = "A"
            verdict = "Excellent Code Quality"
        elif score >= 75:
            grade = "B"
            verdict = "Good Quality with Minor Issues"
        elif score >= 60:
            grade = "C"
            verdict = "Moderate Quality - Needs Refactoring"
        elif score >= 40:
            grade = "D"
            verdict = "High Risk - Several Flaws Detected"
        else:
            grade = "F"
            verdict = "Critical Quality & Security Deficiencies"

        summary = Summary(
            quality_score=score,
            score_grade=grade,
            verdict=verdict,
            total_issues=len(issues),
            critical=crit,
            high=high,
            medium=med,
            low=low,
            info=info,
            security_issues=sec,
            complexity_issues=comp,
            quality_issues=qual
        )

        return metrics, summary
