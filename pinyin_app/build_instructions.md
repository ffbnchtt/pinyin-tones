# Instrucciones de compilación y ejecución

Requisitos: Python 3.8+ y `pip`.

Instalación en desarrollo:

```bash
pip install -r requirements.txt
python src/pinyin_live.py
```

Compilación con PyInstaller (ejemplos):

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

Permisos especiales:
- macOS: conceder Accesibilidad y Grabación de pantalla.
- Linux/Wayland: pynput puede no funcionar; usar X11 o alternativas.
