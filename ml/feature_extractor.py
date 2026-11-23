"""
Multi-Modal Code Feature Extractor.
Extracts:
1. Token N-Grams and Word TF-IDF Vectors
2. Structural AST metrics:
   - Entropy of identifiers
   - Branch / nesting density
   - Dangerous API keyword matches
   - LOC and comment ratios
"""
import re
import math
from typing import List, Dict, Any
import numpy as np

# Precise regex patterns indicating genuine security vulnerabilities
DANGEROUS_PATTERNS = [
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\bgets\s*\(',
    r'\bstrcpy\s*\(',
    r'\bsprintf\s*\(',
    r'\b(system|popen)\s*\(',
    r'shell\s*=\s*True',
    r'(?i)(password|secret|apikey|api_key|auth_token)\s*=\s*["\'][^"\']{6,}["\']',
    r'\bpickle\.loads\s*\(',
    r'\bhashlib\.md5\s*\(',
    r'(?i)select\s+.*\s+from\s+.*\s+where\s+.*[\'\"]\s*\+'
]

class CodeFeatureExtractor:
    @staticmethod
    def extract_structural_features(code: str, language: str) -> np.ndarray:
        lines = code.splitlines()
        loc = max(1, len(lines))
        
        # 1. Dangerous vulnerability pattern density
        danger_matches = sum(len(re.findall(pat, code)) for pat in DANGEROUS_PATTERNS)
        danger_density = (danger_matches / loc) * 10.0
        
        # 2. Nesting depth heuristic
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                if indent > max_indent:
                    max_indent = indent
        nesting_ratio = min(10.0, max_indent / 4.0)

        # 3. Branch density (if, for, while, switch, catch)
        branch_count = len(re.findall(r'\b(if|for|while|switch|case|catch|except)\b', code))
        branch_density = branch_count / loc

        # 4. Keyword entropy
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
        unique_words = len(set(words))
        entropy = unique_words / max(1, len(words))

        # 5. Comment ratio
        comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*")))
        comment_ratio = comment_lines / loc

        return np.array([
            float(danger_density),
            float(nesting_ratio),
            float(branch_density),
            float(entropy),
            float(comment_ratio)
        ], dtype=np.float32)

