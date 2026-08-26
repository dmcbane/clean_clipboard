@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0clean_clipboard.ps1" %*
