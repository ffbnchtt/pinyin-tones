#!/usr/bin/env bash
pyinstaller --onefile --windowed --name pinyin_app src/pinyin_live.py
echo "Aplicación generada en dist/"
