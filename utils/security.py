"""
Security-related helpers (path sanitization, validation).
"""
from pathlib import Path
from typing import Optional


def sanitize_path(base_directory: str, candidate_path: str) -> Optional[str]:
    """Resolve candidate_path against base_directory and ensure it stays within.

    Returns the safe absolute path string if valid; otherwise returns None.
    """
    base = Path(base_directory).resolve()
    cand = (base / candidate_path).resolve() if not Path(candidate_path).is_absolute() else Path(candidate_path).resolve()

    try:
        cand.relative_to(base)
    except ValueError:
        return None
    return str(cand)