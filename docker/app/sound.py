"""
A short success chime, built in memory (no audio asset shipped).

`chime_wav_bytes()` returns a small WAV to hand to `st.audio(..., autoplay=True)`
when a job finishes. `chime_data_uri()` wraps the same bytes as a data: URI.
"""
from __future__ import annotations

import base64
import math
import struct
from functools import lru_cache


@lru_cache(maxsize=1)
def chime_wav_bytes() -> bytes:
    sr = 22050
    dur = 0.28
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 660.0 if t < dur / 2 else 880.0            # two rising notes
        env = min(1.0, t * 30) * min(1.0, (dur - t) * 12)  # fade in / out
        samples.append(int(0.35 * env * math.sin(2 * math.pi * freq * t) * 32767))

    pcm = b"".join(struct.pack("<h", s) for s in samples)
    return b"".join(
        [
            b"RIFF", struct.pack("<I", 36 + len(pcm)), b"WAVE",
            b"fmt ", struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16),
            b"data", struct.pack("<I", len(pcm)), pcm,
        ]
    )


def chime_data_uri() -> str:
    return "data:audio/wav;base64," + base64.b64encode(chime_wav_bytes()).decode("ascii")
