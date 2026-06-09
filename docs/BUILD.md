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

Genera la carpeta `dist\pinyin_tones_release\windows` y el asset listo para GitHub Releases: `dist\pinyin-tones-windows.zip`.

Windows con firma Authenticode:

```cmd
set PINYIN_SIGN_CERT_SHA1=THUMBPRINT_DEL_CERTIFICADO
set PINYIN_SIGN_TIMESTAMP_URL=http://timestamp.digicert.com
python tools\build_release.py --platform windows
```

También se puede firmar con un PFX:

```cmd
set PINYIN_SIGN_CERT_FILE=C:\ruta\pinyin-tones.pfx
set PINYIN_SIGN_CERT_PASSWORD=contraseña
python tools\build_release.py --platform windows
```

Opcionalmente definí `PINYIN_SIGNTOOL_PATH` si `signtool.exe` no está en el `PATH`. La firma se aplica al `pinyin_tones.exe` generado por PyInstaller antes de copiarlo a `dist\pinyin_tones_release\windows`.

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

Notas de confianza en Windows:
- El texto "Editor" que muestra Windows sale del sujeto del certificado de firma. Para que diga "Federico Bianchetti" o "Pinyin Tones", el certificado debe estar emitido con esa identidad legal.
- Un certificado autofirmado no evita advertencias de SmartScreen en equipos de usuarios.
- Incluso con un certificado válido, SmartScreen puede mostrar advertencias iniciales hasta que el archivo o el certificado acumulen reputación.
- Verificá el build firmado con `signtool verify /pa /v dist\pinyin_tones_release\windows\pinyin_tones.exe`.
