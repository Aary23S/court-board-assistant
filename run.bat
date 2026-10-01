@echo off
echo Starting Court Board Assistant...
call .venv\Scripts\activate.bat
python -m streamlit run src\court_board\ui\app.py
pause
