#! /usr/bin/env python3
"""Read clipboard, normalize/strip characters, copy the result back.

Length is unlimited unless --max-length is given.
Works on Windows, macOS, and Linux (X11, Wayland, and WSL).
"""

import argparse
import os
import platform
import subprocess
import sys
from typing import NamedTuple, Optional

__version__ = "0.3.0"

CONVERSIONS = {
    # Tab -> 2 spaces
    "\t": "  ",
    # Smart / typographic double quotes -> "
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u00ab": '"', "\u00bb": '"', "\u2033": '"', "\u2036": '"',
    # Smart single quotes / apostrophes / backtick -> '
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u2032": "'", "\u2035": "'", "\u00b4": "'", "\u0060": "'",
    # Dashes (hyphen, non-breaking hyphen, figure/en/em/horizontal-bar, minus,
    # hyphen bullet, small/full-width variants) -> -
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
    "\u2014": "-", "\u2015": "-", "\u2212": "-", "\u2043": "-",
    "\ufe58": "-", "\ufe63": "-", "\uff0d": "-",
    # Ellipsis -> ...
    "\u2026": "...",
    # Non-breaking / unicode spaces -> space
    "\u00a0": " ", "\u2000": " ", "\u2001": " ", "\u2002": " ",
    "\u2003": " ", "\u2004": " ", "\u2005": " ", "\u2006": " ",
    "\u2007": " ", "\u2008": " ", "\u2009": " ", "\u200a": " ",
    "\u202f": " ", "\u205f": " ", "\u3000": " ",
    # Zero-width / BOM -> drop
    "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
}

ALLOWED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " \n()\"'-_.,/\\"
)

GET_CB = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
    "Get-Clipboard -Raw"
)
SET_CB = (
    "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
    "$text = [Console]::In.ReadToEnd(); "
    "Set-Clipboard -Value $text"
)


class ClipboardBackend(NamedTuple):
    read_cmd: list
    write_cmd: list
    # Get-Clipboard -Raw appends one trailing CRLF that is not clipboard data
    strips_trailing_crlf: bool


def _clipboard_backend() -> ClipboardBackend:
    if sys.platform == "win32":
        return ClipboardBackend(
            ["powershell", "-NoProfile", "-Command", GET_CB],
            ["powershell", "-NoProfile", "-Command", SET_CB],
            strips_trailing_crlf=True,
        )
    if sys.platform == "darwin":
        return ClipboardBackend(["pbpaste"], ["pbcopy"], False)
    # WSL: the clipboard belongs to the Windows host, not the Linux guest
    if "microsoft" in platform.uname().release.lower():
        return ClipboardBackend(
            ["powershell.exe", "-NoProfile", "-Command", GET_CB],
            ["powershell.exe", "-NoProfile", "-Command", SET_CB],
            strips_trailing_crlf=True,
        )
    # Wayland sessions also set DISPLAY (XWayland), so check Wayland first
    if os.environ.get("WAYLAND_DISPLAY"):
        return ClipboardBackend(["wl-paste", "-n"], ["wl-copy"], False)
    return ClipboardBackend(
        ["xclip", "-selection", "clipboard", "-o"],
        ["xclip", "-selection", "clipboard"],
        False,
    )


def get_clipboard() -> str:
    backend = _clipboard_backend()
    r = subprocess.run(
        backend.read_cmd,
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    text = r.stdout
    if backend.strips_trailing_crlf:
        text = text.removesuffix("\r\n")
    return text


def set_clipboard(text: str) -> None:
    subprocess.run(
        _clipboard_backend().write_cmd,
        input=text,
        encoding="utf-8",
        check=True,
    )


def clean(text: str, max_length: Optional[int] = None) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    converted = "".join(CONVERSIONS.get(ch, ch) for ch in text)
    kept = "".join(ch for ch in converted if ch in ALLOWED)
    return kept if max_length is None else kept[:max_length]


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer")
    if number < 1:
        raise argparse.ArgumentTypeError(
            f"must be 1 or greater, got {number}"
        )
    return number


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean the text on the clipboard and copy it back.",
    )
    parser.add_argument(
        "-m",
        "--max-length",
        type=_positive_int,
        metavar="N",
        help="truncate the cleaned text to N characters (default: no limit)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    try:
        raw = get_clipboard()
    except FileNotFoundError as e:
        print(
            f"Clipboard tool not found: {e.filename}. "
            "On Linux, install xclip (X11) or wl-clipboard (Wayland).",
            file=sys.stderr,
        )
        return 1
    if not raw:
        print("Clipboard is empty (or contains no text).", file=sys.stderr)
        return 1
    cleaned = clean(raw, args.max_length)
    set_clipboard(cleaned)
    print(f"in: {len(raw)} chars  ->  out: {len(cleaned)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
