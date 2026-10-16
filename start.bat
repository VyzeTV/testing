@echo off
cd /d "%~dp0"
echo Starting Murder Channel viewer on http://localhost:8766  (close this window or press Ctrl+C to stop)
python server.py
pause
