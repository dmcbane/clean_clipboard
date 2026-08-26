# Read clipboard, normalize/strip characters, copy the result back.
# Length is unlimited unless -MaxLength is given.

[CmdletBinding()]
param(
    # Truncate the cleaned text to this many characters. Omit for no limit.
    # Upper bound is [int]::MaxValue, spelled out because Windows PowerShell
    # wants a literal constant in an attribute argument.
    [ValidateRange(1, 2147483647)]
    [int]$MaxLength
)

$ErrorActionPreference = 'Stop'

$conversions = @{
    # Tab -> 2 spaces
    [char]0x0009 = '  '
    # Smart / typographic double quotes -> "
    [char]0x201C = '"'; [char]0x201D = '"'; [char]0x201E = '"'; [char]0x201F = '"'
    [char]0x00AB = '"'; [char]0x00BB = '"'; [char]0x2033 = '"'; [char]0x2036 = '"'
    # Smart single quotes / apostrophes / backtick -> '
    [char]0x2018 = "'"; [char]0x2019 = "'"; [char]0x201A = "'"; [char]0x201B = "'"
    [char]0x2032 = "'"; [char]0x2035 = "'"; [char]0x00B4 = "'"; [char]0x0060 = "'"
    # Dashes -> -
    [char]0x2010 = '-'; [char]0x2011 = '-'; [char]0x2012 = '-'; [char]0x2013 = '-'
    [char]0x2014 = '-'; [char]0x2015 = '-'; [char]0x2212 = '-'; [char]0x2043 = '-'
    [char]0xFE58 = '-'; [char]0xFE63 = '-'; [char]0xFF0D = '-'
    # Ellipsis -> ...
    [char]0x2026 = '...'
    # Non-breaking / unicode spaces -> space
    [char]0x00A0 = ' '; [char]0x2000 = ' '; [char]0x2001 = ' '; [char]0x2002 = ' '
    [char]0x2003 = ' '; [char]0x2004 = ' '; [char]0x2005 = ' '; [char]0x2006 = ' '
    [char]0x2007 = ' '; [char]0x2008 = ' '; [char]0x2009 = ' '; [char]0x200A = ' '
    [char]0x202F = ' '; [char]0x205F = ' '; [char]0x3000 = ' '
    # Zero-width / BOM -> drop
    [char]0x200B = ''; [char]0x200C = ''; [char]0x200D = ''; [char]0xFEFF = ''
}

$allowed = [System.Collections.Generic.HashSet[char]]::new(
    [char[]]("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ()`"'-_.,/\`n")
)

function Clean([string]$text, [int]$maxLength = 0) {
    # CRLF / lone CR -> LF, matching clean_clipboard.py
    $text = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $sb = [System.Text.StringBuilder]::new($text.Length)
    foreach ($ch in $text.ToCharArray()) {
        if ($conversions.ContainsKey($ch)) {
            [void]$sb.Append($conversions[$ch])
        } elseif ($allowed.Contains($ch)) {
            [void]$sb.Append($ch)
        }
        # else: drop
    }
    $result = $sb.ToString()
    # 0 is the unbound -MaxLength default and means "no limit"
    if ($maxLength -gt 0 -and $result.Length -gt $maxLength) {
        return $result.Substring(0, $maxLength)
    }
    return $result
}

# Dot-sourcing (as the tests do) loads Clean without touching the clipboard.
if ($MyInvocation.InvocationName -ne '.') {
    $raw = Get-Clipboard -Raw
    if ([string]::IsNullOrEmpty($raw)) {
        Write-Error 'Clipboard is empty (or contains no text).'
        exit 1
    }
    $cleaned = Clean $raw $MaxLength
    Set-Clipboard -Value $cleaned
    "in: $($raw.Length) chars  ->  out: $($cleaned.Length) chars"
}
