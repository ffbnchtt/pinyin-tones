# Download and Build

## For users
If you only want to use the app, the project is designed to be packaged with PyInstaller into a standalone executable.

## For developers
Install dependencies and run locally:

```bash
cd pinyin_app
pip install -r requirements.txt
python src/pinyin_live.py
```

Build examples:

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_app src/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_app src/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_app src/pinyin_live.py
```
