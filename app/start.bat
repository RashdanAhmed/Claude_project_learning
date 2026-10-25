@echo off
rem Starts GRC Task Desk and opens it in your browser (Windows).
rem Keep this window open while you use the app; close it or press Ctrl+C to stop.
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 server.py --open %*
  goto done
)
where python >nul 2>nul
if not errorlevel 1 (
  python server.py --open %*
  goto done
)
echo Python 3 is not installed. Download it from https://www.python.org/downloads/ and run this file again.
:done
pause
