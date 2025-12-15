@echo off

echo === Tao virtual environment ===
if not exist venv (
    python -m venv venv
)

echo === Kich hoat venv ===
call venv\Scripts\activate

echo === Cai thu vien ===
pip install -r requirements.txt

echo === Chay ung dung Flask ===
set FLASK_APP=eapp.index
set FLASK_ENV=development
flask run

pause
