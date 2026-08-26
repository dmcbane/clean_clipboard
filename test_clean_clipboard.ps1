# Tests for clean_clipboard.ps1's Clean function. Run with:
#   powershell -NoProfile -ExecutionPolicy Bypass -File test_clean_clipboard.ps1

$ErrorActionPreference = 'Stop'

# Shadow the clipboard cmdlets so dot-sourcing can never touch the real
# clipboard, whatever the script under test does.
function Get-Clipboard { param([switch]$Raw) 'stub' }
function Set-Clipboard { param($Value) }

. (Join-Path $PSScriptRoot 'clean_clipboard.ps1')

$script:passes = 0
$script:failures = 0

function Assert-Clean([string]$name, [string]$text, [string]$expected, [int]$MaxLength = 0) {
    $actual = Clean $text $MaxLength
    if ($actual -ceq $expected) {
        $script:passes++
        Write-Host "ok - $name"
    } else {
        $script:failures++
        Write-Host "FAIL - $name"
        Write-Host "  expected: [$expected]"
        Write-Host "  actual:   [$actual]"
    }
}

# Newline handling (matches clean_clipboard.py)
Assert-Clean 'newline is preserved' "line one`nline two" "line one`nline two"
Assert-Clean 'CRLF is normalized to LF' "line one`r`nline two" "line one`nline two"
Assert-Clean 'lone CR is normalized to LF' "line one`rline two" "line one`nline two"
Assert-Clean 'CRLF does not double line breaks' "a`r`n`r`nb" "a`n`nb"

# Existing behavior
Assert-Clean 'tab becomes two spaces' "a`tb" 'a  b'
Assert-Clean 'smart double quotes' "$([char]0x201C)hi$([char]0x201D)" '"hi"'
Assert-Clean 'smart apostrophe' "it$([char]0x2019)s" "it's"
Assert-Clean 'em dash' "a$([char]0x2014)b" 'a-b'
Assert-Clean 'ellipsis' "wait$([char]0x2026)" 'wait...'
Assert-Clean 'nbsp becomes space' "a$([char]0x00A0)b" 'a b'
Assert-Clean 'zero-width dropped' "a$([char]0x200B)b" 'ab'
Assert-Clean 'disallowed chars stripped' "a$([char]0x263A)b$([char]0x20AC)c" 'abc'

# Max length is opt-in; text is unlimited unless -MaxLength is passed
$long = 'a' * 5000
Assert-Clean 'no max length leaves text untruncated' $long $long
Assert-Clean 'max length truncates' 'abcdef' 'abc' -MaxLength 3
Assert-Clean 'max length longer than text is a no-op' 'abc' 'abc' -MaxLength 100
# The tab expands to two spaces first, so 3 chars is 'a  ', not 'a b'.
Assert-Clean 'max length applies after cleaning' "a`tb" 'a  ' -MaxLength 3

Write-Host ''
Write-Host "$script:passes passed, $script:failures failed"
if ($script:failures -gt 0) { exit 1 }
exit 0
