@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python serial_bridge.py --list
set /p ROBOT_PORT=Enter robot COM port (USB or HC-05): 
set /p ROBOT_TRANSPORT=Enter USB or Bluetooth: 
python serial_bridge.py --port %ROBOT_PORT% --transport %ROBOT_TRANSPORT% 
pause
