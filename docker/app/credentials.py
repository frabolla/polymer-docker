"""
Credential handling for the auxiliary meteorological data.

- NASA Earthdata  -> file  ~/.netrc      (machine urs.earthdata.nasa.gov ...)
- Copernicus CDS  -> file  ~/.cdsapirc   (url + key)

Both files live in /data/config (a host bind mount) so they survive container
restarts. HOME is set to /data/config in the Dockerfile / entrypoint.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("HOME", "/data/config"))

NETRC = CONFIG_DIR / ".netrc"
CDSAPIRC = CONFIG_DIR / ".cdsapirc"

EARTHDATA_MACHINE = "urs.earthdata.nasa.gov"
CDS_URL = "https://cds.climate.copernicus.eu/api"


def _write_private(path: Path, text: str) -> None:
    """Write `text` to `path` with mode 0600 from the start (no world-readable window)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.unlink(missing_ok=True)
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_DIR.chmod(0o700)
    except OSError:
        pass


# --------------------------------------------------------------------------- NASA
def _netrc_tokens(text: str) -> list[str]:
    """Split .netrc text into tokens, honouring "double quotes" and backslash escapes."""
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        buf = []
        if c == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    i += 1
                buf.append(text[i])
                i += 1
            i += 1  # closing quote
        else:
            while i < n and not text[i].isspace():
                if text[i] == "\\" and i + 1 < n:
                    i += 1
                buf.append(text[i])
                i += 1
        tokens.append("".join(buf))
    return tokens


def _netrc_quote(value: str) -> str:
    """Quote a .netrc token when it holds whitespace, '#', quotes or backslashes."""
    if value and not any(c.isspace() or c in '"#\\' for c in value):
        return value
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def invalid_credential_chars(*values: str) -> bool:
    """True if a value holds a line break / control character (cannot go in a file line)."""
    return any(ord(c) < 32 or ord(c) == 127 for v in values for c in (v or ""))


def read_earthdata() -> dict:
    """Return {'login': ..., 'password': ...} if present in .netrc, else {}."""
    if not NETRC.exists():
        return {}
    tokens = _netrc_tokens(NETRC.read_text())
    out: dict[str, str] = {}
    for i, tok in enumerate(tokens):
        if tok == "machine" and i + 1 < len(tokens) and tokens[i + 1] == EARTHDATA_MACHINE:
            rest = tokens[i + 2 :]
            for j in range(0, len(rest) - 1, 2):
                if rest[j] in ("login", "password"):
                    out[rest[j]] = rest[j + 1]
                if rest[j] == "machine":
                    break
    return out


def write_earthdata(login: str, password: str) -> None:
    """
    Create/update the Earthdata line in ~/.netrc, leaving other lines intact.

    Values holding spaces, '#' or quotes are written quoted (understood by wget
    and Python's netrc); line breaks are rejected with ValueError.
    """
    if invalid_credential_chars(login, password):
        raise ValueError("line break or control character in the credentials")
    _ensure_config_dir()
    lines = []
    if NETRC.exists():
        lines = [
            ln
            for ln in NETRC.read_text().splitlines()
            if EARTHDATA_MACHINE not in ln
        ]
    lines.append(
        f"machine {EARTHDATA_MACHINE} login {_netrc_quote(login)} "
        f"password {_netrc_quote(password)}"
    )
    _write_private(NETRC, "\n".join(ln for ln in lines if ln.strip()) + "\n")


def clear_earthdata() -> None:
    if NETRC.exists():
        lines = [
            ln for ln in NETRC.read_text().splitlines() if EARTHDATA_MACHINE not in ln
        ]
        if any(ln.strip() for ln in lines):
            _write_private(NETRC, "\n".join(lines) + "\n")
        else:
            NETRC.unlink()


# ---------------------------------------------------------------------------- CDS
def read_cds() -> dict:
    if not CDSAPIRC.exists():
        return {}
    out: dict[str, str] = {}
    for ln in CDSAPIRC.read_text().splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            out[k.strip()] = v.strip()
    return out


def write_cds(key: str, url: str = CDS_URL) -> None:
    if invalid_credential_chars(key, url):
        raise ValueError("line break or control character in the CDS key")
    _ensure_config_dir()
    _write_private(CDSAPIRC, f"url: {url}\nkey: {key}\n")


def clear_cds() -> None:
    if CDSAPIRC.exists():
        CDSAPIRC.unlink()


# --------------------------------------------------------------- lightweight tests
# Return values: ("ok", "") | ("bad", detail) | ("skip", detail)
_TIMEOUT = 12


def test_earthdata(login: str, password: str) -> tuple[str, str]:
    """Check NASA Earthdata credentials against the tokens endpoint (HTTP basic)."""
    url = "https://urs.earthdata.nasa.gov/api/users/tokens"
    mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    mgr.add_password(None, "https://urs.earthdata.nasa.gov/", login, password)
    opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(mgr))
    try:
        with opener.open(url, timeout=_TIMEOUT) as resp:
            return ("ok", "") if resp.status == 200 else ("bad", f"HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return ("bad", "wrong username or password")
        return ("skip", f"HTTP {e.code}")
    except Exception as e:  # network/DNS/timeout
        return ("skip", str(e))


def test_cds(key: str, url: str = CDS_URL) -> tuple[str, str]:
    """Check a Copernicus CDS API key against the account profile endpoint."""
    endpoint = url.rstrip("/") + "/profiles/v1/account"
    req = urllib.request.Request(endpoint, headers={"PRIVATE-TOKEN": key})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return ("ok", "") if resp.status == 200 else ("bad", f"HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return ("bad", "invalid API key")
        return ("skip", f"HTTP {e.code}")
    except Exception as e:
        return ("skip", str(e))


# ------------------------------------------------------------------------- status
def status() -> dict:
    """Boolean summary for the 'Setup status' sidebar."""
    ed = read_earthdata()
    cds = read_cds()
    return {
        "earthdata": bool(ed.get("login") and ed.get("password")),
        "earthdata_login": ed.get("login", ""),
        "cds": bool(cds.get("key")),
    }
