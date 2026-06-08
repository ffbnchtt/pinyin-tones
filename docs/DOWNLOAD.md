# Descargar y compilar

## Para usuarios

Si solo querés usar la aplicación, el proyecto está pensado para empaquetarse con PyInstaller en un ejecutable independiente. La ventana de configuración incluye una opción para iniciar la aplicación automáticamente con el sistema operativo.

## Para desarrolladores

Instalá dependencias y ejecutá en desarrollo:

```powershell
pip install -e .
python src/pinyin_app/pinyin_live.py

# Alternativa si querés ejecutar como módulo instalado
python -m pinyin_app
```

Si también vas a compilar ejecutables:

```powershell
pip install -e ".[dev]"
```

Construcción recomendada (usá el helper de release):

Windows:

```powershell
python tools\build_release.py --platform windows
```

Firma Authenticode para Windows:

```powershell
$env:PINYIN_SIGN_CERT_SHA1 = "THUMBPRINT_DEL_CERTIFICADO"
$env:PINYIN_SIGN_TIMESTAMP_URL = "http://timestamp.digicert.com"
python tools\build_release.py --platform windows
```

Si usás un PFX, definí `PINYIN_SIGN_CERT_FILE` y, si corresponde, `PINYIN_SIGN_CERT_PASSWORD`. Si `signtool.exe` no está en el `PATH`, definí `PINYIN_SIGNTOOL_PATH`.

La firma usa la identidad del certificado para el campo "Editor" de Windows. Un certificado autofirmado no alcanza para distribución pública, y SmartScreen puede seguir mostrando advertencias iniciales hasta que el archivo o el certificado ganen reputación.

macOS:

```bash
python3 tools/build_release.py --platform macos
```

Linux:

```bash
python3 tools/build_release.py --platform linux
```

Ejemplos directos con PyInstaller (solo si necesitas personalizar):

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_tones --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_tones --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_tones --paths src --hidden-import pinyin_app.pinyin_converter src/pinyin_app/pinyin_live.py
```

## Íconos del tray

- Los PNG del tray se cargan desde `src/pinyin_app/assets/tray`.
- Mantené variantes en 16/20/24/32/64 px con el prefijo `tray_quicksand_o_caron_`.
- El helper `build_release.py` empaqueta esos assets automáticamente cuando existen.

## Comportamiento de inicio automático

- Windows escribe una entrada en `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- macOS escribe un `LaunchAgent` plist en `~/Library/LaunchAgents`.
- Linux escribe un archivo desktop en `~/.config/autostart`.
