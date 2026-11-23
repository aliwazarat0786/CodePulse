"""
Issue deduplicator module for CodePulse AI.
Merges duplicate reports from overlapping tools.
"""
from typing import List
from models.schemas import Issue

class IssueDeduplicator:
    @staticmethod
    def deduplicate(issues: List[Issue]) -> List[Issue]:
        if not issues:
            return []

        merged: List[Issue] = []
        
        for issue in issues:
            duplicate_found = False
            for existing in merged:
                same_file = existing.file == issue.file
                near_line = abs(existing.line - issue.line) <= 2
                
                # Check category or error type overlap
                is_syntax_overlap = (
                    ("syntax" in existing.category.lower() or "syntax" in existing.rule.lower() or "compilation" in existing.rule.lower()) and
                    ("syntax" in issue.category.lower() or "syntax" in issue.rule.lower() or "compilation" in issue.rule.lower())
                )
                is_runtime_overlap = (
                    existing.rule == issue.rule or
                    (existing.error_type and issue.error_type and existing.error_type == issue.error_type)
                )
                
                rule_sim = (
                    existing.rule.lower() == issue.rule.lower() or 
                    existing.rule.lower() in issue.message.lower() or 
                    issue.rule.lower() in existing.message.lower() or
                    is_syntax_overlap or
                    is_runtime_overlap
                )
                
                if same_file and near_line and rule_sim:
                    if issue.tool not in existing.detected_by:
                        existing.detected_by.append(issue.tool)
                    
                    sev_rank = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}
                    if sev_rank.get(issue.severity, 0) > sev_rank.get(existing.severity, 0):
                        existing.severity = issue.severity
                    
                    # Merge diagnostics and runtime evidence
                    if not existing.source and issue.source:
                        existing.source = issue.source
                    if issue.runtime_evidence and not existing.runtime_evidence:
                        existing.runtime_evidence = issue.runtime_evidence
                    if issue.error_type and not existing.error_type:
                        existing.error_type = issue.error_type
                        
                    duplicate_found = True
                    break

            if not duplicate_found:
                merged.append(issue)

        for idx, item in enumerate(merged, start=1):
            item.id = f"CP-{idx:03d}"

        return merged
