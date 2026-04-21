
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

def run(cmd: list[str], cwd: str | None = None) -> None:
   
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

def libreoffice_convert(src: Path, target_ext: str, out_dir: Path) -> bytes:
    
    run([
        "libreoffice", "--headless",
        "--convert-to", target_ext,
        "--outdir", str(out_dir),
        str(src),
    ])
    out_file = out_dir / f"{src.stem}.{target_ext}"
    if not out_file.exists():
        raise FileNotFoundError(f"LibreOffice did not produce {out_file}")
    return out_file.read_bytes()


def pandoc_convert(src: Path, to_fmt: str) -> bytes:
   
    with tempfile.NamedTemporaryFile(suffix=f".{to_fmt}", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        run(["pandoc", str(src), "-o", tmp_path])
        return Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

