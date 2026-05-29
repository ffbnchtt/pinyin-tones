# Pinyin Tones

![License](https://img.shields.io/github/license/ffbnchtt/pinyin-tones)
![Release](https://img.shields.io/github/v/release/ffbnchtt/pinyin-tones)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Convierte tonos de Pinyin en tiempo real mientras escribís. Se ejecuta en segundo plano con un ícono en la bandeja y un atajo global configurable.

## Inicio rápido

1. Descargá la versión para tu sistema desde la página de [releases](https://github.com/ffbnchtt/pinyin-tones/releases). Cada release incluye tres paquetes `.zip` (Windows, macOS, Linux).
2. Descomprimí y ejecutá la aplicación; verás el ícono en la bandeja del sistema.

Si preferís ejecutar desde la fuente (desarrollo):

### Prerrequisitos

- Python 3.8+ (recomendado)
- `pip` y (opcional) un entorno virtual

### Instalación desde fuente

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ejecutar la aplicación (modo desarrollo)

```bash
python -m src.pinyin_app
```

## Uso básico

- Activá o desactivá la funcionalidad desde el ícono en la bandeja.
- Escribí un token con número de tono, por ejemplo `ni3` o `hao3` —se reemplaza automáticamente por `nǐ` o `hǎo`.

## Configuración

La configuración se guarda en [src/pinyin_app/config.json](src/pinyin_app/config.json). Desde la interfaz de configuración podés:

- Cambiar el atajo global.
- Activar/desactivar el inicio automático con el sistema.

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
