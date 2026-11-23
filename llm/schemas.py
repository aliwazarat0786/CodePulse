"""
Schemas for LLM integration.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMIssueExplanation:
    explanation: str
    impact: str
    priority: str
    recommendation: str
    fixed_code: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.90
