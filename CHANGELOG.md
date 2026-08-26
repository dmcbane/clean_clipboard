# Changelog

## 0.3.0 - 2026-08-26

- **Breaking:** the 1000-character limit is no longer applied by default.
  The full cleaned text is copied back unless a maximum is requested.
- Python: added `-m` / `--max-length N` (and `--version`). `clean()` now
  takes an optional `max_length`; `main()` takes an optional `argv`.
- PowerShell: added a `-MaxLength` parameter, validated to be 1 or
  greater. `Clean` takes an optional max length, where 0 means no limit.
- `Clean Clipboard.cmd` forwards its arguments to the PowerShell script.
- To restore the old behavior, pass `--max-length 1000` / `-MaxLength 1000`.

## 0.2.1 - 2026-08-07

- PowerShell version now matches the Python version's newline handling:
  CRLF / lone CR are normalized to LF (previously CRLF passed through
  unchanged).
- Extracted a `Clean` function with a dot-source guard so the script is
  testable without touching the clipboard.
- Added a PowerShell test suite (`test_clean_clipboard.ps1`) with stubbed
  clipboard cmdlets.

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
