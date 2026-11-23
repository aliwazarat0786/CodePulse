"""
LLM Analyzer module that prioritizes and enriches issues with AI insights.
"""
from typing import List, Dict, Any, Tuple
from models.schemas import Issue, AIAnalysis
from llm.client import LLMClient

class LLMAnalyzer:
    def __init__(self):
        self.client = LLMClient()

    def enrich_issues(
        self,
        issues: List[Issue],
        source_code: str,
        language: str,
        quality_score: int
    ) -> Tuple[List[Issue], Dict[str, Any]]:
        # Sort issues by severity priority: CRITICAL, HIGH, MEDIUM, LOW, INFO
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        sorted_issues = sorted(issues, key=lambda x: priority_order.get(x.severity, 5))

        # Enrich top issues with AI insights
        for issue in sorted_issues[:15]:
            explanation_data = self.client.generate_explanation(
                language=language,
                tool=issue.tool,
                rule=issue.rule,
                severity=issue.severity,
                message=issue.message,
                source=issue.source,
                line=issue.line
            )

            issue.ai_analysis = AIAnalysis(
                explanation=explanation_data.get("explanation", ""),
                impact=explanation_data.get("impact", ""),
                priority=explanation_data.get("priority", issue.severity),
                recommendation=explanation_data.get("recommendation", ""),
                fixed_code=explanation_data.get("fixed_code"),
                confidence=float(explanation_data.get("confidence", 0.90)),
                reasoning=explanation_data.get("reasoning", "")
            )

        ai_summary = {
            "executive_summary": f"Analysis complete for {language.capitalize()} file. Identified {len(issues)} findings with an overall Code Quality Score of {quality_score}/100.",
            "security_posture": "High Attention Needed" if any(i.severity in ["CRITICAL", "HIGH"] for i in issues) else "Stable / Low Risk",
            "key_recommendation": "Prioritize critical security vulnerabilities and flatten nested complexity.",
            "ai_engine_status": "Active (Deterministic AI & Gemini Layer)"
        }

        return issues, ai_summary
