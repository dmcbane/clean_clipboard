# Changelog

## 0.2.0 - 2026-08-07

- Python version now works on macOS (pbcopy/pbpaste), Linux X11 (xclip),
  Linux Wayland (wl-clipboard), and WSL (Windows host clipboard via
  powershell.exe), in addition to Windows.
- Newlines are no longer converted to spaces: `\n` is preserved, and
  `\r\n` / lone `\r` are normalized to `\n`.
- PowerShell's phantom trailing CRLF is now removed exactly once, so a
  genuine trailing newline in the clipboard text survives.
- A missing Linux clipboard tool now produces an install hint and exit
  code 1 instead of a traceback.
- Added a stdlib-only unittest suite (`test_clean_clipboard.py`).

## 0.1.0

- Initial Python and PowerShell versions for Windows 11.
