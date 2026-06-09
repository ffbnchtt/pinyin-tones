# Instrucciones de compilación y ejecución

Requisitos: Python 3.10+ y `pip`.

Instalación en desarrollo:

```bash
pip install -e .
python src/pinyin_tones/pinyin_live.py

# Alternativa si querés ejecutar como módulo instalado
python -m pinyin_tones
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

Genera la carpeta `dist\pinyin_tones_release\windows` y el asset listo para GitHub Releases: `dist\pinyin-tones-windows.zip`. El zip guarda los archivos directamente en la raíz del archivo para que al extraerlo quede una sola carpeta.

macOS:

```bash
python3 tools/build_release.py --platform macos
```

Genera `dist/pinyin-tones-macos.zip`.

Linux:

```bash
python3 tools/build_release.py --platform linux
```

Genera `dist/pinyin-tones-linux.zip`.

Compilación directa con PyInstaller (ejemplos):

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_tones --paths src --hidden-import pinyin_tones.pinyin_converter src/pinyin_tones/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_tones --paths src --hidden-import pinyin_tones.pinyin_converter src/pinyin_tones/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_tones --paths src --hidden-import pinyin_tones.pinyin_converter src/pinyin_tones/pinyin_live.py
```

Permisos especiales:
- macOS: conceder Accesibilidad y Grabación de pantalla.
- Linux/Wayland: pynput puede no funcionar; usar X11 o alternativas.
