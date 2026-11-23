"""
LLM Client for Google Gemini API with fallback rule-based reasoning engine.
Ensures zero-downtime demonstration capability even if API key is not supplied.
"""
import os
import json
import re
from typing import Dict, Any, Optional
from config import Config

class LLMClient:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.LLM_MODEL
        self._gemini_model = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._gemini_model = genai.GenerativeModel(self.model_name)
            except Exception:
                self._gemini_model = None

    def generate_explanation(
        self,
        language: str,
        tool: str,
        rule: str,
        severity: str,
        message: str,
        source: str,
        line: int
    ) -> Dict[str, Any]:
        """Generate structured explanation via LLM or deterministic expert engine."""
        if self._gemini_model:
            try:
                prompt = (
                    f"You are CodePulse AI. Analyze this static-analysis finding.\n"
                    f"Language: {language}\n"
                    f"Tool: {tool} (Rule: {rule}, Severity: {severity})\n"
                    f"Message: {message}\n"
                    f"Line {line}: {source}\n\n"
                    f"Provide structured JSON response with: explanation, impact, priority, recommendation, fixed_code, reasoning."
                )
                response = self._gemini_model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                text = response.text
                return json.loads(text)
            except Exception:
                pass

        # Intelligent Deterministic Expert Fallback Engine
        return self._generate_expert_fallback(language, tool, rule, severity, message, source)

    def _generate_expert_fallback(
        self,
        language: str,
        tool: str,
        rule: str,
        severity: str,
        message: str,
        source: str
    ) -> Dict[str, Any]:
        """Provides rich, contextual AI explanations when remote LLM is offline."""
        low_rule = rule.lower()
        low_msg = message.lower()

        if "eval" in low_rule or "eval" in low_msg:
            return {
                "explanation": f"The '{source}' statement evaluates arbitrary input strings as executable code. If user-supplied input reaches this statement, an attacker can execute arbitrary system commands.",
                "impact": "Remote Code Execution (RCE), complete system compromise, and unauthorized data exfiltration.",
                "priority": "CRITICAL - Address Immediately",
                "recommendation": "Replace dynamic evaluation with structured data deserialization (e.g. JSON.parse or ast.literal_eval).",
                "fixed_code": "# Secure alternative:\nimport ast\nsafe_data = ast.literal_eval(untrusted_string) if language == 'python' else JSON.parse(untrusted_string)",
                "reasoning": "Static deserialization parses literals without executing arbitrary code instructions."
            }

        if "gets" in low_rule or "gets" in low_msg:
            return {
                "explanation": "gets() reads stdin until a newline without checking target buffer capacity.",
                "impact": "Stack buffer overflow, memory corruption, and arbitrary control flow hijacking.",
                "priority": "CRITICAL - Address Immediately",
                "recommendation": "Use fgets() specifying the exact buffer size limit.",
                "fixed_code": "char buffer[256];\nif (fgets(buffer, sizeof(buffer), stdin) != NULL) {\n    // Process securely\n}",
                "reasoning": "fgets guarantees bounds checking to avoid stack overflow."
            }

        if "secret" in low_rule or "password" in low_rule or "credential" in low_rule:
            return {
                "explanation": "Hardcoded secret or password found in source control.",
                "impact": "Leaked credentials in source control or decompiled binaries allowing unauthorized access.",
                "priority": "HIGH - Immediate Refactor Required",
                "recommendation": "Extract sensitive credentials to environment variables or secret vaults.",
                "fixed_code": "import os\nAPI_SECRET = os.getenv('API_SECRET_KEY')  # Loaded securely at runtime",
                "reasoning": "Decouples credentials from application source code."
            }

        if "shell" in low_rule or "subprocess" in low_rule:
            return {
                "explanation": "Executing subprocesses with shell=True spawns a system shell that parses shell metacharacters.",
                "impact": "Command injection vulnerability if any variable in the command string is user-controllable.",
                "priority": "HIGH - Fix Before Deployment",
                "recommendation": "Pass command arguments as a list with shell=False.",
                "fixed_code": "import subprocess\nsubprocess.run(['ls', '-la', target_path], shell=False, check=True)",
                "reasoning": "Prevents parameter injection by avoiding shell interpreter execution."
            }

        if "nesting" in low_rule or "complexity" in low_rule:
            return {
                "explanation": f"Deeply nested control structures ({rule}) increase cognitive load and cyclomatic complexity.",
                "impact": "High defect rates, difficult unit testing, and increased regression risk during maintenance.",
                "priority": "MEDIUM - Recommended Refactor",
                "recommendation": "Invert conditions using guard clauses and extract subroutines.",
                "fixed_code": "if not is_valid(data):\n    return False\n# Continue linear execution...",
                "reasoning": "Guard clauses flatten nested conditionals into readable sequential steps."
            }

        if "unused" in low_rule:
            return {
                "explanation": f"The entity '{rule}' is imported or assigned but never referenced in subsequent logic.",
                "impact": "Unnecessary memory consumption, namespace pollution, and developer confusion.",
                "priority": "LOW - Code Cleanup",
                "recommendation": f"Safely remove the unused declaration '{source}'.",
                "fixed_code": "# Remove unused line\n",
                "reasoning": "Cleans up namespace and improves module load speed."
            }

        # Default fallback
        return {
            "explanation": f"Static analysis tool '{tool}' flagged this pattern ({rule}) as a violation of {severity.lower()} severity.",
            "impact": "Potential degradation in software reliability, performance, or maintainability over time.",
            "priority": f"{severity.upper()} - Review during code refactoring cycle",
            "recommendation": f"Review line against standard {language.capitalize()} best practices.",
            "fixed_code": f"// Refactored pattern for: {source}",
            "reasoning": "Adhering to standard style and quality rules prevents latent bugs."
        }
