#!/usr/bin/env bash
pyinstaller --onefile --noconsole --name pinyin_app src/pinyin_live.py
echo "Binario generado en dist/"
