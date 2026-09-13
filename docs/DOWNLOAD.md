# Descargar y compilar

## Para usuarios

Las releases ofrecen una variante portable y, cuando corresponde, una variante instalable:

- Windows: `pinyin-tones-windows.zip`.
- macOS: DMG firmado para Apple Silicon o Intel; también ZIPs portables.
- Linux x64: `pinyin-tones-linux-amd64.deb` para Ubuntu/Debian, AppImage portable y ZIP portable.

La ventana de configuración incluye una opción para iniciar la aplicación automáticamente con el sistema operativo. En AppImage, la app guarda la ruta del archivo AppImage original para que el inicio automático persista después de cerrar sesión.

## Para desarrolladores

Instalá dependencias y ejecutá en desarrollo:

```powershell
pip install -e .
python src/pinyin_tones/pinyin_live.py

# Alternativa si querés ejecutar como módulo instalado
python -m pinyin_tones
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

El comando genera la carpeta `dist\pinyin_tones_release\windows` y el zip listo para subir a GitHub Releases: `dist\pinyin-tones-windows.zip`. El zip guarda los archivos directamente en la raíz del archivo para que al extraerlo quede una sola carpeta.

macOS:

```bash
python3 tools/build_release.py --platform macos --arch arm64 --formats portable,dmg
```

Genera los assets portables e instalables para Apple Silicon. Usá `--arch x64` en una Mac Intel.

Linux:

```bash
APPIMAGETOOL=/ruta/a/appimagetool python3 tools/build_release.py --platform linux --arch x64 --formats portable,appimage,deb
```

Genera ZIP, AppImage y DEB para Linux x64.

Ejemplos directos con PyInstaller (solo si necesitas personalizar):

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

## Íconos del tray

- Los PNG del tray se cargan desde `src/pinyin_tones/assets/tray`.
- Mantené variantes en 16/20/24/32/64 px con el prefijo `tray_quicksand_o_caron_`.
- El helper `build_release.py` empaqueta esos assets automáticamente cuando existen.

## Comportamiento de inicio automático

- Windows escribe una entrada en `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- macOS escribe un `LaunchAgent` plist en `~/Library/LaunchAgents`.
- Linux escribe un archivo desktop en `~/.config/autostart`.

## Publicar una release

Crear un tag SemVer `vX.Y.Z` que coincida con `pyproject.toml` y `src/pinyin_tones/version.py` inicia el workflow de release. El workflow crea un borrador con los assets y `SHA256SUMS.txt`; publicalo sólo después de probar Windows, Mac Intel, Apple Silicon y Ubuntu con X11. La descarga automática sólo acepta assets cuyo hash SHA-256 figura en ese archivo.
