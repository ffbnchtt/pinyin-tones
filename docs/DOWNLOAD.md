# Download and Build

## For users

If you only want to use the app, the project is designed to be packaged with PyInstaller into a standalone executable.
The settings window includes an option to start the app automatically with the operating system.

## For developers

Install dependencies and run locally:

```bash
cd pinyin_app
pip install -r requirements.txt
python src/pinyin_live.py
```

Build examples (recommended):

Windows:

```cmd
python pinyin_app\scripts\build_release.py --platform windows
```

macOS:

```bash
python3 pinyin_app/scripts/build_release.py --platform macos
```

Linux:

```bash
python3 pinyin_app/scripts/build_release.py --platform linux
```

Build examples (direct PyInstaller):

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_app --paths src --hidden-import pinyin_converter src/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_app --paths src --hidden-import pinyin_converter src/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_app --paths src --hidden-import pinyin_converter src/pinyin_live.py
```

## Autostart behavior

- Windows writes a value under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- macOS writes a `LaunchAgent` plist in `~/Library/LaunchAgents`.
- Linux writes a desktop autostart entry in `~/.config/autostart`.
