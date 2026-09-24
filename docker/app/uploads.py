"""
Save products uploaded through the interface into /data/input.

Streamlit's uploader cannot receive a folder, so satellite products that are
directories (`.SEN3`, `.SAFE`) must be uploaded as a `.zip`. Single-file
products (`.nc`, `.he5`, `.N1`, `.L1C`, …) are saved as-is.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

INPUT_DIR = Path("/data/input")

# Extensions accepted directly (no unzip).
SINGLE_FILE_EXT = {".nc", ".he5", ".h5", ".hdf", ".n1", ".l1c", ".csv"}


# Free space kept in reserve after an extraction (bytes).
_SPACE_MARGIN = 500 * 1024 * 1024


def _is_junk(name: str) -> bool:
    """macOS Finder metadata added to zips ("__MACOSX/", "._file", ".DS_Store")."""
    parts = Path(name).parts
    return (
        not parts
        or parts[0] == "__MACOSX"
        or parts[-1].startswith("._")
        or parts[-1] == ".DS_Store"
    )


def _members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    return [m for m in zf.infolist() if m.filename.strip() and not _is_junk(m.filename)]


def _safe_extract(zf: zipfile.ZipFile, dest: Path, members: list[zipfile.ZipInfo]) -> None:
    dest = dest.resolve()
    for m in members:
        target = (dest / m.filename).resolve()
        if target != dest and not target.is_relative_to(dest):
            raise ValueError(f"unsafe path in zip: {m.filename}")
    # Refuse archives that would not fit (also stops "zip bombs" filling the disk).
    need = sum(m.file_size for m in members)
    free = shutil.disk_usage(str(dest if dest.exists() else dest.parent)).free
    if need + _SPACE_MARGIN > free:
        raise ValueError(
            f"not enough free space: needs {need / 1e6:.0f} MB, "
            f"{free / 1e6:.0f} MB available"
        )
    zf.extractall(dest, members=members)


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
                    members = _members(zf)
                    if not members:
                        raise ValueError("the archive is empty")
                    tops = {Path(m.filename).parts[0] for m in members}
                    if len(tops) == 1:
                        # zip already contains a single top-level folder/file
                        _safe_extract(zf, INPUT_DIR, members)
                        messages.append(f"extracted: {next(iter(tops))}")
                    else:
                        out = INPUT_DIR / stem
                        out.mkdir(exist_ok=True)
                        _safe_extract(zf, out, members)
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
