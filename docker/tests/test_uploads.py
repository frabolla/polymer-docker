import io
import zipfile

import uploads


class FakeUpload:
    def __init__(self, name, data: bytes):
        self.name = name
        self._data = data

    def getbuffer(self):
        return self._data


def _zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_single_file_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    msgs = uploads.save_uploads([FakeUpload("scene.nc", b"data")])
    assert (tmp_path / "scene.nc").read_bytes() == b"data"
    assert any("saved" in m for m in msgs)


def test_zip_with_single_top_folder_extracts(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    z = _zip({"S3A_X.SEN3/a.txt": b"1", "S3A_X.SEN3/b.txt": b"2"})
    msgs = uploads.save_uploads([FakeUpload("S3A_X.zip", z)])
    assert (tmp_path / "S3A_X.SEN3" / "a.txt").exists()
    assert any("extracted" in m for m in msgs)


def test_zip_path_traversal_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    z = _zip({"../evil.txt": b"x", "ok.txt": b"y"})
    msgs = uploads.save_uploads([FakeUpload("bad.zip", z)])
    assert any("failed to extract" in m for m in msgs)
    assert not (tmp_path.parent / "evil.txt").exists()


def test_unknown_extension_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    msgs = uploads.save_uploads([FakeUpload("notes.docx", b"x")])
    assert any("ignored" in m for m in msgs)
    assert not (tmp_path / "notes.docx").exists()
