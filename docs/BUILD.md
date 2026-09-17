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

## Releases nativos

PyInstaller genera binarios para el sistema y arquitectura donde se ejecuta. Compilá Windows en Windows, macOS Intel en un runner Intel, macOS Apple Silicon en ARM y Linux x64 en Linux x64.

Compilación con el script de release:

Windows:

```cmd
python tools\build_release.py --platform windows
```

Genera `dist\pinyin-tones-windows.zip`.

macOS:

```bash
python3 tools/build_release.py --platform macos --arch arm64 --formats portable,dmg
```

Reemplazá `arm64` por `x64` para Mac Intel. Genera un ZIP portable y un DMG; los nombres incluyen la arquitectura.

Linux:

```bash
APPIMAGETOOL=/ruta/a/appimagetool python3 tools/build_release.py --platform linux --arch x64 --formats portable,appimage,deb
```

Genera `pinyin-tones-linux.zip`, AppImage y DEB. Para el DEB se necesita `dpkg-deb`; para AppImage, `appimagetool`.

`--formats` acepta `portable`, `dmg`, `appimage` y `deb` según la plataforma. Sin ese argumento se crean todos los formatos soportados en el sistema actual.

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
- macOS: conceder Accesibilidad y, si el sistema lo solicita, Input Monitoring. El bundle se ejecuta como app de barra de menú, por lo que no mantiene un ícono en el Dock. Una firma Developer ID y la notarización no son necesarias para compilar, pero sí son recomendables para evitar advertencias de Gatekeeper en una distribución pública. El workflow genera ZIPs portables sin firma salvo que se active explícitamente la firma con credenciales válidas.
- Linux: la primera matriz soportada es Ubuntu 22.04+ x64 con X11. En Wayland, pynput puede no recibir el teclado global o sólo operar mediante Xwayland.
