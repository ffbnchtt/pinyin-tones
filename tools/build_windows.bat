@echo off
python "%~dp0build_release.py" --platform windows
echo Build Windows completo en dist\pinyin_tones_release\windows
pause
