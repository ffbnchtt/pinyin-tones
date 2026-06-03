# Instrucciones de compilación y ejecución

Requisitos: Python 3.10+ y `pip`.

Instalación en desarrollo:

```bash
pip install -e .
python src/pinyin_app/pinyin_live.py

# Alternativa si querés ejecutar como módulo instalado
python -m pinyin_app
```

Si también vas a compilar ejecutables:

```bash
pip install -e ".[dev]"
```

Compilación con el script de release (recomendado):

Windows:

```cmd
python tools\build_release.py --platform windows
```

macOS:

```bash
python3 tools/build_release.py --platform macos
```

Linux:

```bash
python3 tools/build_release.py --platform linux
```

Compilación directa con PyInstaller (ejemplos):

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_app --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_app --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_app --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

Permisos especiales:
- macOS: conceder Accesibilidad y Grabación de pantalla.
- Linux/Wayland: pynput puede no funcionar; usar X11 o alternativas.
