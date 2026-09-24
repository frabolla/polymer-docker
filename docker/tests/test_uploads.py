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


def test_zip_from_macos_finder_ignores_metadata(tmp_path, monkeypatch):
    # Finder's "Compress" adds __MACOSX/ and ._* entries next to the product.
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    z = _zip({
        "S3A_X.SEN3/xfdumanifest.xml": b"1",
        "__MACOSX/S3A_X.SEN3/._xfdumanifest.xml": b"meta",
        "S3A_X.SEN3/._junk": b"meta",
    })
    uploads.save_uploads([FakeUpload("S3A_X.SEN3.zip", z)])
    assert (tmp_path / "S3A_X.SEN3" / "xfdumanifest.xml").exists()
    assert not (tmp_path / "__MACOSX").exists()
    assert not (tmp_path / "S3A_X.SEN3" / "._junk").exists()
    assert not (tmp_path / "S3A_X.SEN3" / "S3A_X.SEN3").exists()  # not nested


def test_zip_larger_than_free_space_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "INPUT_DIR", tmp_path)
    monkeypatch.setattr(uploads, "_SPACE_MARGIN", 10**18)
    msgs = uploads.save_uploads([FakeUpload("p.zip", _zip({"P/a.txt": b"1"}))])
    assert any("free space" in m for m in msgs)
    assert not (tmp_path / "P").exists()
