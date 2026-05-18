@echo off
pyinstaller --onefile --noconsole --name pinyin_app src\pinyin_live.py
echo Ejecutable en dist\
pause
