@echo off
chcp 65001 > nul
echo ======================================================
echo   🌽 กำลังเปิดระบบคำนวณกำไรอบข้าวโพด (สำหรับคุณแม่)...
echo ======================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)

pause
