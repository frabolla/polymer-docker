"""Every user-facing string is translated consistently in both languages."""
import re
from pathlib import Path

import i18n

APP = Path(__file__).resolve().parents[1] / "app"


def test_every_key_has_both_languages():
    missing = [k for k, v in i18n._STRINGS.items() if "en" not in v or "it" not in v]
    assert not missing, f"keys missing a language: {missing}"


def test_placeholders_match_between_languages():
    bad = []
    for k, v in i18n._STRINGS.items():
        en = set(re.findall(r"{(\w+)", v["en"]))
        it = set(re.findall(r"{(\w+)", v["it"]))
        if en != it:
            bad.append((k, en, it))
    assert not bad, f"placeholder mismatch: {bad}"


def test_no_empty_translations():
    empty = [k for k, v in i18n._STRINGS.items() if not v["en"].strip() or not v["it"].strip()]
    assert not empty


def test_streamlit_app_only_uses_defined_keys():
    src = (APP / "streamlit_app.py").read_text()
    keys = set(i18n._STRINGS)

    static = set(re.findall(r"i18n\.t\(\s*[\"']([a-zA-Z0-9_.]+)[\"']", src))
    assert not (static - keys), f"undefined i18n keys: {sorted(static - keys)}"

    # dynamic families like i18n.t(f"ancillary.{k}")
    for prefix in set(re.findall(r"i18n\.t\(\s*f[\"']([a-z_]+)\.\{", src)):
        assert any(k.startswith(prefix + ".") for k in keys), f"no keys for prefix {prefix!r}"


def test_translate_formats_and_falls_back():
    i18n.set_lang("it")
    assert i18n.t("sidebar.version", v="9") == "Versione 9"
    i18n.set_lang("en")
    assert i18n.t("sidebar.version", v="9") == "Version 9"
    assert i18n.t("does.not.exist") == "does.not.exist"
