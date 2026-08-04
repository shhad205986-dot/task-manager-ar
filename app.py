"""Runtime loader for the Arabic Task Manager application.

The complete source archive is stored in bootstrap/xz-* and extracted into a
writable temporary directory when the web process starts. This keeps the
published application deployable even when GitHub Actions are unavailable.
"""

from __future__ import annotations

import base64
import importlib.util
import shutil
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE_PARTS = sorted((ROOT / "bootstrap").glob("xz-*"))
RUNTIME_DIR = Path(tempfile.gettempdir()) / "task_manager_ar_runtime"
RUNTIME_APP = RUNTIME_DIR / "app.py"


def prepare_runtime() -> None:
    if RUNTIME_APP.exists():
        return
    if not ARCHIVE_PARTS:
        raise RuntimeError("Application archive parts were not found.")

    staging = Path(tempfile.mkdtemp(prefix="task_manager_ar_"))
    try:
        encoded = b"".join(part.read_bytes() for part in ARCHIVE_PARTS)
        archive_path = staging / "project.tar.xz"
        archive_path.write_bytes(base64.b64decode(encoded))

        extracted = staging / "extracted"
        extracted.mkdir()
        with tarfile.open(archive_path, mode="r:xz") as archive:
            archive.extractall(extracted)

        if RUNTIME_DIR.exists():
            shutil.rmtree(RUNTIME_DIR)
        shutil.move(str(extracted), str(RUNTIME_DIR))
    finally:
        shutil.rmtree(staging, ignore_errors=True)


prepare_runtime()
spec = importlib.util.spec_from_file_location("task_manager_runtime", RUNTIME_APP)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load the task manager application.")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
