import os
from typing import NoReturn


class SecurityError(Exception):
    pass


def read_file(file_path: str) -> str:
    """
    Reads the file data and outputs the content of the file
    The file path passed should be the relative file path to the project
    """
    # Security check
    normalized_path = os.path.normpath(file_path)
    FORBIDDEN_PATTERNS = [".env", "secret", "password", "credential", "private_key"]

    if any(pattern in normalized_path.lower() for pattern in FORBIDDEN_PATTERNS):
        raise SecurityError(f"Access denied: Cannot read sensitive file {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        return f.read()
