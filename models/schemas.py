"""
Data models and schemas for CodePulse AI.
Enforces a uniform representation across all static analysis, dynamic execution,
AI diagnosis, verification, and comparison modules.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class IssueCategory(str, Enum):
    SECURITY = "security"
    CODE_QUALITY = "code-quality"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    BUG_RISK = "bug-risk"
    SYNTAX = "syntax"
    RUNTIME = "runtime"

class ErrorType(str, Enum):
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INDENTATION_ERROR = "INDENTATION_ERROR"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    LOGICAL_ERROR = "LOGICAL_ERROR"
    TYPE_ERROR = "TYPE_ERROR"
    NAME_ERROR = "NAME_ERROR"
    REFERENCE_ERROR = "REFERENCE_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    NULL_POINTER_ERROR = "NULL_POINTER_ERROR"
    INDEX_ERROR = "INDEX_ERROR"
    DIVISION_BY_ZERO = "DIVISION_BY_ZERO"
    SECURITY_ISSUE = "SECURITY_ISSUE"
    PERFORMANCE_ISSUE = "PERFORMANCE_ISSUE"
    CODE_QUALITY = "CODE_QUALITY"
    STYLE = "STYLE"
    COMPLEXITY = "COMPLEXITY"
    POTENTIAL_BUG = "POTENTIAL_BUG"

class FixVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    NOT_VERIFIED = "NOT_VERIFIED"
    REQUIRES_USER_REVIEW = "REQUIRES_USER_REVIEW"

@dataclass
class AIAnalysis:
    explanation: str = ""
    impact: str = ""
    priority: str = "medium"
    recommendation: str = ""
    fixed_code: Optional[str] = None
    confidence: float = 0.85
    reasoning: str = ""
    exact_fix: str = ""
    root_cause: str = ""
    fix_type: str = "AUTOMATIC"
    fix_confidence: float = 0.90
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Issue:
    id: str
    language: str
    file: str
    line: int
    column: int
    severity: str
    category: str
    tool: str
    rule: str
    message: str
    source: str = ""
    description: str = ""
    confidence: float = 1.0
    suggested_fix: str = ""
    documentation_url: str = ""
    detected_by: List[str] = field(default_factory=list)
    ai_analysis: Optional[AIAnalysis] = None
    # Extended diagnostic fields
    error_type: str = ""
    error_code: str = ""
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    source_snippet: str = ""
    evidence: str = ""
    root_cause: str = ""
    exact_fix: str = ""
    fix_type: str = "AUTOMATIC"
    verification_status: str = "NOT_VERIFIED"
    runtime_evidence: str = ""

    def __post_init__(self):
        if not self.detected_by:
            self.detected_by = [self.tool]
        if not self.source_snippet and self.source:
            self.source_snippet = self.source
        if not self.error_type:
            # Map basic category to error type
            cat = self.category.lower()
            if cat in ["syntax", "bug-risk"] and "syntax" in self.rule.lower():
                self.error_type = ErrorType.SYNTAX_ERROR.value
            elif "indent" in self.rule.lower():
                self.error_type = ErrorType.INDENTATION_ERROR.value
            elif cat == "security":
                self.error_type = ErrorType.SECURITY_ISSUE.value
            elif cat == "complexity":
                self.error_type = ErrorType.COMPLEXITY.value
            else:
                self.error_type = ErrorType.POTENTIAL_BUG.value

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.ai_analysis:
            data["ai_analysis"] = self.ai_analysis.to_dict()
        return data

@dataclass
class ExecutionResult:
    status: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT, COMPILATION_ERROR, UNAVAILABLE
    stdout: str = ""
    stderr: str = ""
    compilation_output: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_line: Optional[int] = None
    error_column: Optional[int] = None
    timed_out: bool = False
    output_limit_exceeded: bool = False
    runtime_evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FixResult:
    fix_id: str
    issue_id: str
    problem: str
    root_cause: str
    exact_fix: str
    change_summary: str
    original_snippet: str
    fixed_snippet: str
    fix_type: str = "AUTOMATIC"
    confidence: float = 0.95
    verification_status: str = "NOT_VERIFIED"
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class VerificationResult:
    status: str = "VERIFIED"  # VERIFIED, PARTIALLY_VERIFIED, FAILED_VERIFICATION, NOT_VERIFIED, REQUIRES_USER_REVIEW
    summary: str = ""
    syntax_valid: bool = True
    compilation_passed: bool = True
    execution_passed: bool = True
    resolved_issues_count: int = 0
    introduced_issues_count: int = 0
    introduced_issues: List[Dict[str, Any]] = field(default_factory=list)
    before_execution: Optional[Dict[str, Any]] = None
    after_execution: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CodeComparison:
    original_code: str
    fixed_code: str
    diff_unified: str = ""
    diff_lines: List[Dict[str, Any]] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    total_modifications: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Metrics:
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    cyclomatic_complexity: Optional[float] = None
    maintainability_index: Optional[float] = None
    functions_count: int = 0
    classes_count: int = 0
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    security_count: int = 0
    quality_count: int = 0
    complexity_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Summary:
    quality_score: int = 100
    score_grade: str = "A"
    verdict: str = "Clean Code"
    total_issues: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    security_issues: int = 0
    complexity_issues: int = 0
    quality_issues: int = 0
    disclaimer: str = (
        "This score is an internal CodePulse heuristic intended for relative analysis, "
        "not a universal software-quality standard."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalysisResult:
    analysis_id: str
    filename: str
    language: str
    timestamp: str
    summary: Summary
    metrics: Metrics
    issues: List[Issue]
    warnings: List[str] = field(default_factory=list)
    ai_summary: Optional[Dict[str, Any]] = None
    ml_prediction: Optional[Dict[str, Any]] = None
    code_purpose: Optional[Dict[str, Any]] = None
    refactoring_roadmap: Optional[Dict[str, Any]] = None
    tools_executed: List[str] = field(default_factory=list)
    tools_unavailable: List[str] = field(default_factory=list)
    execution: Optional[ExecutionResult] = None
    version: int = 1
    parent_analysis_id: Optional[str] = None
    source_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "filename": self.filename,
            "language": self.language,
            "timestamp": self.timestamp,
            "summary": self.summary.to_dict(),
            "metrics": self.metrics.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "warnings": self.warnings,
            "ai_summary": self.ai_summary or {},
            "ml_prediction": self.ml_prediction or {},
            "code_purpose": self.code_purpose or {},
            "refactoring_roadmap": self.refactoring_roadmap or {},
            "tools_executed": self.tools_executed,
            "tools_unavailable": self.tools_unavailable,
            "execution": self.execution.to_dict() if self.execution else None,
            "version": self.version,
            "parent_analysis_id": self.parent_analysis_id,
            "source_code": self.source_code
        }

@dataclass
class ReportComparison:
    comparison_id: str
    original_analysis_id: str
    fixed_analysis_id: str
    timestamp: str
    score_before: int
    score_after: int
    score_delta: int
    grade_before: str
    grade_after: str
    total_issues_before: int
    total_issues_after: int
    resolved_issues: List[Dict[str, Any]] = field(default_factory=list)
    remaining_issues: List[Dict[str, Any]] = field(default_factory=list)
    new_issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics_comparison: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    execution_before: Optional[Dict[str, Any]] = None
    execution_after: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    code_comparison: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
