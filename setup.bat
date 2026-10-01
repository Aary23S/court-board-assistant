@echo off
echo ==========================================
echo Setting up Court Board Assistant
echo ==========================================

echo 1. Creating virtual environment...
python -m venv .venv

echo 2. Activating virtual environment...
call .venv\Scripts\activate.bat

echo 3. Installing dependencies...
pip install -r requirements.txt
pip install streamlit

echo ==========================================
echo Setup Complete! 
echo You can now double-click "run.bat" to start the app.
echo ==========================================
pause
