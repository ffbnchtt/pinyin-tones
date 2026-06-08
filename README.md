# Pinyin Tones

![License](https://img.shields.io/github/license/ffbnchtt/pinyin-tones)
![Release](https://img.shields.io/github/v/release/ffbnchtt/pinyin-tones)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Conversión de tonos de pinyin en tiempo real.

<img width="426" height="240" alt="pinyin_tones" src="https://github.com/user-attachments/assets/b4e897fc-b613-46b1-975f-5fce3b2ab804" />

## Inicio rápido

1. Descargá la versión para tu sistema desde la página de [releases](https://github.com/ffbnchtt/pinyin-tones/releases). Cada release incluye tres paquetes `.zip` (Windows, macOS, Linux).
2. Descomprimí y ejecutá la aplicación; vas a ver el ícono en la bandeja del sistema.

Si preferís ejecutar desde la fuente (desarrollo):

### Prerrequisitos

- Python 3.10+ (recomendado)
- `pip` y (opcional) un entorno virtual

### Instalación desde fuente

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### Ejecutar la aplicación (modo desarrollo)

```bash
python -m pinyin_app
```

Si también querés compilar ejecutables desde la fuente:

```bash
pip install -e ".[dev]"
```

Para generar un paquete local:

```bash
python tools/build_release.py --platform windows
```

Reemplazá `windows` por `macos` o `linux` según corresponda.

Cuando publiques releases en GitHub para que la app pueda detectar actualizaciones, usá nombres de assets estables por plataforma:

- `pinyin-tones-windows.zip`
- `pinyin-tones-macos.zip`
- `pinyin-tones-linux.zip`

## Uso básico

- Activá o desactivá la funcionalidad desde el ícono en la bandeja.
- Escribí un token con número de tono, por ejemplo `ni3` o `hao3` —se reemplaza automáticamente por `nǐ` o `hǎo`.

## Compatibilidad y permisos

- Windows: debería funcionar sin pasos extra en la mayoría de las instalaciones de escritorio.
- macOS: la app necesita permisos de `Accesibilidad` y, según la versión del sistema, también `Input Monitoring` para escuchar el teclado global e inyectar el reemplazo en la app enfocada.
- Linux: funciona mejor en sesiones `X11`; en `Wayland` la captura global y la inyección de teclado pueden estar limitadas por el compositor o directamente bloqueadas.

Si la app parece iniciarse pero no detecta teclas o no reemplaza texto, revisá primero esos permisos del sistema.

## Configuración

La configuración se guarda en `config.json`. La app intenta usar la carpeta del ejecutable o la raíz del proyecto cuando corrés desde fuente; si esa ubicación no es escribible, usa una carpeta de datos del usuario (`%LOCALAPPDATA%\Pinyin Tones` en Windows, `~/Library/Application Support/Pinyin Tones` en macOS o `~/.config/Pinyin Tones` en Linux). Desde la interfaz de configuración podés:

- Cambiar el atajo global.
- Activar/desactivar el inicio automático con el sistema.

Además, la app guarda estado interno para actualizaciones:

- `update_check_enabled`
- `update_check_interval_hours`
- `last_update_check_at`
- `downloaded_update_version`
- `downloaded_update_path`

Para ajustes avanzados de reemplazo, revisá `src/pinyin_app/pinyin_converter.py` y `src/pinyin_app/pinyin_live.py`.

## Ejecutar pruebas

```bash
python tools/run_tests.py
```

## Contribuciones

¿Encontraste un problema o tenés una idea para mejorar el proyecto?

Toda contribución es bienvenida. Antes de abrir un *issue* o enviar un *pull request*, revisá el [código de conducta](CODE_OF_CONDUCT.md) y la guía de [contribuciones](CONTRIBUTING.md).

## Versionado

Usamos [SemVer](https://semver.org/lang/es/) para versionado. Para las versiones disponibles, ver los [tags](https://github.com/ffbnchtt/pinyin-tones/tags) en este repositorio.

## Autores

- Federico Bianchetti - Idea y desarrollo inicial

 Mirá la lista de [colaboradores](https://github.com/ffbnchtt/pinyin-tones/graphs/contributors) que participaron en este proyecto.

## Licencia

Proyecto con licencia MIT — ver [LICENSE.md](LICENSE) para detalles.

---

Hecho con ❤️ por [ffbnchtt](https://github.com/ffbnchtt)
