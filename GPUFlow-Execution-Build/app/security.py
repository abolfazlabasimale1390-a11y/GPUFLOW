from __future__ import annotations

import hashlib
from pathlib import Path

# Demo-only access gate. This is not a production licensing/security system.
PASSWORD_SHA256 = "605b2a50f4ec7a1feb7706690eafe82b4751ff253daf3bb07031822a2b7c4c6e"
RUNTIME_FILE_NAME = "gpuflow.runtime"
RUNTIME_FILE_SHA256 = "33b83ccf7f63f939fdebbee5f34e7d4f8e3197262de52d6dd79b2fd7b557f730"


def project_root() -> Path:
    """Return the directory containing the launcher (also when PyInstaller-frozen)."""
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def verify_runtime_file() -> tuple[bool, str]:
    runtime_path = project_root() / RUNTIME_FILE_NAME
    if not runtime_path.is_file():
        return False, f"Required companion file is missing: {RUNTIME_FILE_NAME}"
    try:
        content = runtime_path.read_bytes()
    except OSError as exc:
        return False, f"Cannot read {RUNTIME_FILE_NAME}: {exc}"
    digest = hashlib.sha256(content).hexdigest()
    if digest != RUNTIME_FILE_SHA256:
        return False, f"{RUNTIME_FILE_NAME} is invalid or damaged"
    return True, "Runtime companion verified"


def verify_password(password: str) -> bool:
    candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return candidate == PASSWORD_SHA256


def static_dir() -> Path:
    """Resolve bundled frontend files in source and PyInstaller builds."""
    import sys

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app" / "static"
    return Path(__file__).resolve().parent / "static"
