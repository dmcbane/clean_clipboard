# Clean Clipboard

These simple scripts cleanup the text in your clipboard by restricting the content to allowed characters.  Length is unlimited by default; pass a maximum length on the command line if you want the result truncated.  There is a PowerShell script version for Windows systems without python installed, and a Python version for macOS and Linux systems that will have Python installed by default.

I created this for a single use case in order to simplify the workflow for one very repetitive task.

## Usage
1. Copy your content to be cleaned onto your clipboard (usually Ctrl-C or Cmd-C)
2. Run the script (Clean Clipboard.cmd for Windows systems or clean_clipboard.py for macOS or Linux systems)
3. Paste your cleaned content to the destination (usually Ctrl-V or Cmd-V)

### Limiting the length

By default the whole cleaned text is copied back. To cap it, pass a maximum
length:

```sh
./clean_clipboard.py --max-length 1000   # or -m 1000
./clean_clipboard.py --help
```

```powershell
.\clean_clipboard.ps1 -MaxLength 1000
"Clean Clipboard.cmd" -MaxLength 1000
```

The limit applies to the cleaned text, after characters have been converted or
stripped. It must be 1 or greater.

## Tests

```sh
python3 -m unittest test_clean_clipboard
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File test_clean_clipboard.ps1
```
