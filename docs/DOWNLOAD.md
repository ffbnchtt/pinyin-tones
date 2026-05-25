# Descargar y compilar

## Para usuarios

Si solo quieres usar la aplicación, el proyecto está diseñado para empaquetarse con PyInstaller en un ejecutable independiente. La ventana de configuración incluye una opción para iniciar la aplicación automáticamente con el sistema operativo.

## Para desarrolladores

Instalar dependencias y ejecutar en desarrollo:

```powershell
cd pinyin_app
pip install -r requirements.txt
python pinyin_live.py
```

Construcción recomendada (usa el helper de release):

Windows:

```powershell
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

Ejemplos directos con PyInstaller (solo si necesitas personalizar):

Windows:

```cmd
pyinstaller --onefile --noconsole --name pinyin_app --paths pinyin_app --hidden-import pinyin_app.pinyin_converter pinyin_app/pinyin_live.py
```

macOS:

```bash
pyinstaller --onefile --windowed --name pinyin_app --paths pinyin_app --hidden-import pinyin_app.pinyin_converter pinyin_app/pinyin_live.py
```

Linux:

```bash
pyinstaller --onefile --noconsole --name pinyin_app --paths pinyin_app --hidden-import pinyin_app.pinyin_converter pinyin_app/pinyin_live.py
```

## Iconos del tray

- Los PNG del tray se cargan desde `pinyin_app/assets/tray`.
- Mantén variantes en 16/20/24/32/64 px con el prefijo `tray_quicksand_a_macron_`.
- El helper `build_release.py` empaqueta esos assets automáticamente cuando existen.

## Comportamiento de inicio automático

- Windows escribe una entrada en `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- macOS escribe un `LaunchAgent` plist en `~/Library/LaunchAgents`.
- Linux escribe un archivo desktop en `~/.config/autostart`.
