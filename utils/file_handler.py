"""
Safe temporary file handling for CodePulse AI.
"""
import os
import shutil
import uuid
import re
from pathlib import Path
from config import Config

Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str, default_ext: str = ".txt") -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    if not filename:
        return f"submitted_code{default_ext}"
    base = os.path.basename(filename)
    safe = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    if not safe or safe.startswith('.'):
        safe = f"code_{uuid.uuid4().hex[:6]}{default_ext}"
    return safe

def create_temp_workspace(analysis_id: str, filename: str, code_content: str) -> Path:
    """Create a temporary workspace directory for a single analysis."""
    work_dir = Config.TEMP_DIR / analysis_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = sanitize_filename(filename)
    file_path = work_dir / safe_name
    
    with open(file_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(code_content)
        
    return file_path

def cleanup_temp_workspace(analysis_id: str):
    """Safely remove a temporary analysis workspace."""
    work_dir = Config.TEMP_DIR / analysis_id
    if work_dir.exists():
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
