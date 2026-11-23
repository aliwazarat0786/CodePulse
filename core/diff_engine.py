"""
Diff and Code Comparison Engine for CodePulse AI.
Computes unified and side-by-side line diffs between original and AI-fixed source code.
"""
import difflib
from typing import List, Dict, Any, Tuple
from models.schemas import CodeComparison

class DiffEngine:
    @staticmethod
    def compare_code(original_code: str, fixed_code: str) -> CodeComparison:
        """
        Generates structured line-by-line diff and metrics.
        """
        orig_lines = original_code.splitlines(keepends=True)
        fixed_lines = fixed_code.splitlines(keepends=True)

        # 1. Generate standard unified diff text
        unified_generator = difflib.unified_diff(
            orig_lines,
            fixed_lines,
            fromfile="original",
            tofile="ai_fixed",
            lineterm=""
        )
        diff_unified = "\n".join(unified_generator)

        # 2. Generate side-by-side aligned line map
        diff_lines: List[Dict[str, Any]] = []
        additions = 0
        deletions = 0
        modifications = 0

        orig_clean = original_code.splitlines()
        fixed_clean = fixed_code.splitlines()

        matcher = difflib.SequenceMatcher(None, orig_clean, fixed_clean)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for idx in range(i2 - i1):
                    diff_lines.append({
                        "line_orig": i1 + idx + 1,
                        "line_fixed": j1 + idx + 1,
                        "type": "unchanged",
                        "orig_text": orig_clean[i1 + idx],
                        "fixed_text": fixed_clean[j1 + idx]
                    })
            elif tag == "replace":
                max_len = max(i2 - i1, j2 - j1)
                for idx in range(max_len):
                    has_orig = idx < (i2 - i1)
                    has_fixed = idx < (j2 - j1)
                    
                    orig_t = orig_clean[i1 + idx] if has_orig else ""
                    fixed_t = fixed_clean[j1 + idx] if has_fixed else ""
                    
                    diff_lines.append({
                        "line_orig": (i1 + idx + 1) if has_orig else None,
                        "line_fixed": (j1 + idx + 1) if has_fixed else None,
                        "type": "modified",
                        "orig_text": orig_t,
                        "fixed_text": fixed_t
                    })
                    modifications += 1
            elif tag == "delete":
                for idx in range(i2 - i1):
                    diff_lines.append({
                        "line_orig": i1 + idx + 1,
                        "line_fixed": None,
                        "type": "removed",
                        "orig_text": orig_clean[i1 + idx],
                        "fixed_text": ""
                    })
                    deletions += 1
            elif tag == "insert":
                for idx in range(j2 - j1):
                    diff_lines.append({
                        "line_orig": None,
                        "line_fixed": j1 + idx + 1,
                        "type": "added",
                        "orig_text": "",
                        "fixed_text": fixed_clean[j1 + idx]
                    })
                    additions += 1

        return CodeComparison(
            original_code=original_code,
            fixed_code=fixed_code,
            diff_unified=diff_unified,
            diff_lines=diff_lines,
            total_additions=additions,
            total_deletions=deletions,
            total_modifications=modifications
        )
