"""
Save products uploaded through the interface into /data/input.

Streamlit's uploader cannot receive a folder, so satellite products that are
directories (`.SEN3`, `.SAFE`) must be uploaded as a `.zip`. Single-file
products (`.nc`, `.he5`, `.N1`, `.L1C`, …) are saved as-is.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

INPUT_DIR = Path("/data/input")

# Extensions accepted directly (no unzip).
SINGLE_FILE_EXT = {".nc", ".he5", ".h5", ".hdf", ".n1", ".l1c", ".csv"}


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in zf.namelist():
        target = (dest / member).resolve()
        if target != dest and not target.is_relative_to(dest):
            raise ValueError(f"unsafe path in zip: {member}")
    zf.extractall(dest)


def save_uploads(uploaded_files) -> list[str]:
    """Persist the given Streamlit UploadedFile objects. Returns status messages."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []

    for uf in uploaded_files or []:
        name = Path(uf.name).name
        ext = Path(name).suffix.lower()

        if ext == ".zip":
            stem = Path(name).stem
            tmp_zip = INPUT_DIR / f".{stem}.upload.zip"
            tmp_zip.write_bytes(uf.getbuffer())
            try:
                with zipfile.ZipFile(tmp_zip) as zf:
                    tops = {Path(n).parts[0] for n in zf.namelist() if n.strip()}
                    if len(tops) == 1:
                        # zip already contains a single top-level folder/file
                        _safe_extract(zf, INPUT_DIR)
                        messages.append(f"extracted: {next(iter(tops))}")
                    else:
                        out = INPUT_DIR / stem
                        out.mkdir(exist_ok=True)
                        _safe_extract(zf, out)
                        messages.append(f"extracted: {stem}/")
            except Exception as exc:
                messages.append(f"failed to extract {name}: {exc}")
            finally:
                tmp_zip.unlink(missing_ok=True)

        elif ext in SINGLE_FILE_EXT:
            (INPUT_DIR / name).write_bytes(uf.getbuffer())
            messages.append(f"saved: {name}")

        else:
            messages.append(
                f"ignored {name}: use a .zip for folder products, or one of "
                + ", ".join(sorted(SINGLE_FILE_EXT))
            )

    return messages
