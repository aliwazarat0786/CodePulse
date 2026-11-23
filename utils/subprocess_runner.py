"""
Controlled subprocess execution utility for static-analysis tools.
"""
import subprocess
import shutil
from typing import List, Tuple, Optional
from config import Config

def is_tool_available(tool_name: str) -> bool:
    """Check if an executable is available on the system PATH."""
    return shutil.which(tool_name) is not None

def run_tool_command(
    cmd: List[str],
    timeout_sec: Optional[int] = None,
    cwd: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Run an external static analysis tool securely.
    Returns: (exit_code, stdout, stderr)
    """
    if timeout_sec is None:
        timeout_sec = Config.ANALYSIS_TIMEOUT

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            cwd=cwd,
            shell=False
        )
        return process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Execution timed out after {timeout_sec} seconds"
    except FileNotFoundError:
        return -2, "", f"Tool executable '{cmd[0]}' not found on system PATH"
    except Exception as e:
        return -3, "", f"Execution failed: {str(e)}"
