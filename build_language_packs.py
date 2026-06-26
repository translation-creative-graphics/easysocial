#!/usr/bin/env python3
"""
Phase 3 — CRE8 Social language pack builder.

For every non-en-GB locale present in the repo, builds one installable ZIP:
  dist/com_easysocial_{locale}.zip

Each ZIP contains:
  easysocial_{locale}.xml          — Joomla file-extension manifest (root)
  administrator/language/{locale}/ — admin .ini files (if any)
  language/{locale}/               — site .ini files (if any)
"""

import re
import zipfile
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import (
    Element, SubElement, ElementTree, indent
)

_EMPTY_VAL_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*\s*=\s*(""|\'\'|)\s*$')

def strip_empty_values(content: bytes) -> bytes:
    """Remove KEY= / KEY="" lines so Joomla falls back to en-GB instead of showing blank."""
    lines = content.decode('utf-8', errors='replace').splitlines(keepends=True)
    return ''.join(l for l in lines if not _EMPTY_VAL_RE.match(l)).encode('utf-8')

REPO       = Path(__file__).parent
DIST       = REPO / "dist"
VERSION    = "5.0.6"
AUTHOR     = "Erik Winnelinckx, Pascal Kemper"
EMAIL      = "info@creative-graphics.ch"
URL        = "https://creative-graphics.ch/en"
COPYRIGHT  = f"Copyright {date.today().year} Creative Graphics. All rights reserved"
LICENSE    = "GPL License"

LOCALE_NAMES = {
    "ar-SA": "Arabic (Saudi Arabia)",
    "bg-BG": "Bulgarian",
    "ca-ES": "Catalan",
    "cs-CZ": "Czech",
    "da-DK": "Danish",
    "de-DE": "German",
    "el-GR": "Greek",
    "es-ES": "Spanish (Spain)",
    "et-EE": "Estonian",
    "fa-IR": "Persian",
    "fr-FR": "French",
    "gl-ES": "Galician",
    "he-IL": "Hebrew",
    "hr-HR": "Croatian",
    "hu-HU": "Hungarian",
    "it-IT": "Italian",
    "ja-JP": "Japanese",
    "kk-KZ": "Kazakh",
    "nb-NO": "Norwegian Bokmål",
    "nl-NL": "Dutch",
    "pl-PL": "Polish",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "ro-RO": "Romanian",
    "ru-RU": "Russian",
    "sk-SK": "Slovak",
    "sl-SI": "Slovenian",
    "sq-AL": "Albanian",
    "sv-SE": "Swedish",
    "tr-TR": "Turkish",
    "uk-UA": "Ukrainian",
    "vi-VN": "Vietnamese",
    "zh-CN": "Chinese Simplified",
}

SECTIONS = [
    "administrator/language",
    "language",
]


def make_manifest(locale: str, sections_files: dict[str, list[str]]) -> bytes:
    lang_name = LOCALE_NAMES.get(locale, locale)
    root = Element("extension", type="file", version="3.0.0", method="upgrade")
    SubElement(root, "name").text    = f"CRE8 Social - Language Pack {lang_name} ({locale})"
    SubElement(root, "version").text = VERSION
    SubElement(root, "creationDate").text = date.today().strftime("%-d %B %Y")
    SubElement(root, "author").text       = AUTHOR
    SubElement(root, "authorEmail").text  = EMAIL
    SubElement(root, "authorUrl").text    = URL
    SubElement(root, "copyright").text    = COPYRIGHT
    SubElement(root, "license").text      = LICENSE
    SubElement(root, "description").text  = f"{lang_name} Language Pack for CRE8 Social {VERSION}"

    fileset = SubElement(root, "fileset")
    for section, filenames in sections_files.items():
        if not filenames:
            continue
        folder = f"{section}/{locale}"
        files_el = SubElement(fileset, "files", folder=folder, target=folder)
        for fname in sorted(filenames):
            SubElement(files_el, "filename").text = fname

    indent(root, space="    ")
    tree = ElementTree(root)

    import io
    buf = io.StringIO()
    buf.write('<?xml version="1.0" encoding="utf-8"?>\n')
    tree.write(buf, encoding="unicode", xml_declaration=False)
    return buf.getvalue().encode("utf-8")


def build_locale(locale: str) -> bool:
    sections_files: dict[str, list[str]] = {}
    any_files = False

    for section in SECTIONS:
        locale_dir = REPO / section / locale
        if locale_dir.is_dir():
            filenames = [f.name for f in sorted(locale_dir.glob("*.ini"))]
        else:
            filenames = []
        sections_files[section] = filenames
        if filenames:
            any_files = True

    if not any_files:
        print(f"  SKIP {locale}  (no .ini files found)")
        return False

    manifest_bytes = make_manifest(locale, sections_files)
    manifest_name  = f"easysocial_{locale}.xml"
    zip_path       = DIST / f"com_easysocial_{locale}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(manifest_name, manifest_bytes)
        for section, filenames in sections_files.items():
            for fname in filenames:
                src = REPO / section / locale / fname
                zf.writestr(f"{section}/{locale}/{fname}",
                            strip_empty_values(src.read_bytes()))

    total = sum(len(v) for v in sections_files.values())
    print(f"  {locale:8s}  {total:3d} files  →  {zip_path.name}")
    return True


def main():
    DIST.mkdir(exist_ok=True)

    locales = sorted(
        d.name
        for d in (REPO / "language").iterdir()
        if d.is_dir() and d.name != "en-GB"
    )

    print(f"Building {len(locales)} language packs into {DIST}/\n")
    built = 0
    for locale in locales:
        if build_locale(locale):
            built += 1

    print(f"\nDone — {built} ZIPs written to {DIST}/")


if __name__ == "__main__":
    main()
