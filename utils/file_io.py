"""
Robust file I/O utilities that guard against [Errno 5] Input/output errors.

Errno 5 (EIO) typically occurs when:
  - The underlying storage is unavailable or flaky (network drives, temp mounts).
  - A file descriptor becomes stale (e.g. container volume detached).
  - Streamlit's uploaded-file buffer is consumed more than once.

Strategy: copy upload bytes into memory first, then write to a verified temp
path with retry logic, and always close handles explicitly.
"""

import io
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, Union

import streamlit as st

MAX_RETRIES = 3
BACKOFF_BASE = 0.5  # seconds


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_dir() -> Path:
    """Return a guaranteed-writable temp directory."""
    base = Path(tempfile.gettempdir()) / "zippr_workspace"
    return _ensure_dir(base)


def safe_read_upload(uploaded_file) -> Optional[bytes]:
    """Read a Streamlit UploadedFile into memory safely.

    This avoids repeated .read() calls on the same buffer and guards
    against I/O errors from the upload transport.
    """
    if uploaded_file is None:
        return None
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
        if not data:
            st.warning("Uploaded file appears to be empty.")
            return None
        return data
    except (IOError, OSError) as exc:
        st.error(f"Failed to read uploaded file: {exc}")
        return None


def safe_write_bytes(data: bytes, filename: str, subdir: str = "") -> Optional[Path]:
    """Write *data* to a temp file with retry logic.

    Returns the Path on success, None on failure.
    """
    target_dir = get_temp_dir()
    if subdir:
        target_dir = _ensure_dir(target_dir / subdir)

    dest = target_dir / filename
    last_exc: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            dest.write_bytes(data)
            return dest
        except (IOError, OSError) as exc:
            last_exc = exc
            time.sleep(BACKOFF_BASE * (2 ** attempt))

    st.error(f"Could not write file after {MAX_RETRIES} attempts: {last_exc}")
    return None


def safe_read_bytes(path: Union[str, Path]) -> Optional[bytes]:
    """Read bytes from *path* with retry logic."""
    path = Path(path)
    if not path.exists():
        st.error(f"File not found: {path.name}")
        return None

    last_exc: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            return path.read_bytes()
        except (IOError, OSError) as exc:
            last_exc = exc
            time.sleep(BACKOFF_BASE * (2 ** attempt))

    st.error(f"Could not read file after {MAX_RETRIES} attempts: {last_exc}")
    return None


def safe_read_text(path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """Read text from *path* with retry logic."""
    raw = safe_read_bytes(path)
    if raw is None:
        return None
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError as exc:
        st.error(f"Encoding error reading {Path(path).name}: {exc}")
        return None


def cleanup_temp(subdir: str = "") -> None:
    """Remove temp files for the given subdir (or all if empty)."""
    target = get_temp_dir()
    if subdir:
        target = target / subdir
    try:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    except (IOError, OSError):
        pass
