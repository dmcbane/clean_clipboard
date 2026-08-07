"""Read clipboard, normalize/strip characters, copy first 1000 chars back."""

import subprocess
import sys

CONVERSIONS = {
    # Tab -> 2 spaces
    "\t": "  ",
    # Line breaks -> space (newlines are not in allowlist; concatenating without
    # a separator would fuse adjacent words)
    "\r": " ",
    "\n": " ",
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
    " ()\"'-_.,/\\"
)

MAX_LEN = 1000

GET_CB = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
    "Get-Clipboard -Raw"
)
SET_CB = (
    "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
    "$text = [Console]::In.ReadToEnd(); "
    "Set-Clipboard -Value $text"
)


def get_clipboard() -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", GET_CB],
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    # Get-Clipboard -Raw appends a trailing CRLF
    return r.stdout.rstrip("\r\n")


def set_clipboard(text: str) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", SET_CB],
        input=text,
        encoding="utf-8",
        check=True,
    )


def clean(text: str) -> str:
    converted = "".join(CONVERSIONS.get(ch, ch) for ch in text)
    return "".join(ch for ch in converted if ch in ALLOWED)


def main() -> int:
    raw = get_clipboard()
    if not raw:
        print("Clipboard is empty (or contains no text).", file=sys.stderr)
        return 1
    cleaned = clean(raw)[:MAX_LEN]
    set_clipboard(cleaned)
    print(f"in: {len(raw)} chars  ->  out: {len(cleaned)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
