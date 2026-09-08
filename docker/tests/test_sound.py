"""The success chime is a valid, self-contained WAV."""
import base64
import struct

import sound


def test_chime_wav_bytes_is_a_valid_wav():
    raw = sound.chime_wav_bytes()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE"
    # declared RIFF size matches the payload
    assert struct.unpack("<I", raw[4:8])[0] == len(raw) - 8
    assert sound.chime_wav_bytes() is raw  # cached


def test_chime_data_uri_wraps_the_same_bytes():
    uri = sound.chime_data_uri()
    assert uri.startswith("data:audio/wav;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]) == sound.chime_wav_bytes()
