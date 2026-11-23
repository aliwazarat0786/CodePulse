"""
Issue normalizer module for CodePulse AI.
"""
from typing import List, Dict, Any
from models.schemas import Issue, IssueCategory
from core.severity import map_severity

class IssueNormalizer:
    @staticmethod
    def normalize(raw_issues: List[Dict[str, Any]], language: str, filename: str) -> List[Issue]:
        normalized: List[Issue] = []
        counter = 1

        for raw in raw_issues:
            issue_id = raw.get("id") or f"CP-{counter:03d}"
            counter += 1

            raw_severity = str(raw.get("severity", "MEDIUM"))
            rule = str(raw.get("rule", "general-check"))
            msg = str(raw.get("message", "Potential issue detected"))
            
            normalized_sev = map_severity(raw_severity, rule, msg)
            
            category = raw.get("category", IssueCategory.CODE_QUALITY.value)
            if isinstance(category, IssueCategory):
                category = category.value

            if category in ["code-quality", "general"]:
                low_msg = msg.lower()
                low_rule = rule.lower()
                if any(w in low_msg or w in low_rule for w in ["security", "injection", "vulnerability", "password", "secret", "overflow", "leak"]):
                    category = IssueCategory.SECURITY.value
                elif any(w in low_msg or w in low_rule for w in ["complexity", "cyclomatic", "nesting", "too many branches"]):
                    category = IssueCategory.COMPLEXITY.value
                elif any(w in low_msg or w in low_rule for w in ["unused", "naming", "docstring", "style", "convention"]):
                    category = IssueCategory.STYLE.value

            issue = Issue(
                id=issue_id,
                language=language,
                file=raw.get("file", filename),
                line=int(raw.get("line", 1)),
                column=int(raw.get("column", 0)),
                severity=normalized_sev,
                category=category,
                tool=raw.get("tool", "static-analyzer"),
                rule=rule,
                message=msg,
                source=raw.get("source", ""),
                description=raw.get("description", ""),
                confidence=float(raw.get("confidence", 0.9)),
                suggested_fix=raw.get("suggested_fix", ""),
                documentation_url=raw.get("documentation_url", ""),
                detected_by=[raw.get("tool", "static-analyzer")]
            )
            normalized.append(issue)

        return normalized
