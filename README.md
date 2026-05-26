# Pinyin Tones

Convierte tonos de Pinyin en tiempo real mientras escribís. Corre en segundo plano con un ícono en la bandeja y un atajo configurable.

## Para usuarios

1. Andá a los Releases: <https://github.com/ffbnchtt/pinyin-tones/releases>
2. Descarga el archivo para tu sistema operativo.
3. Descomprimí y ejecutá la aplicación.
4. Vas a ver el ícono en la bandeja del sistema.

## Uso rápido

- Activá o desactivá desde el ícono de la bandeja.
- Escribí un token con número de tono, por ejemplo `ni3` o `hao3`.
- Se reemplaza automáticamente por `nǐ` o `hǎo`.

## Configuración

- Cambiá el atajo global desde la ventana de configuración.
- Podés activar el inicio automático con el sistema operativo.

## Guías

- Guía de usuario: [pinyin_app/docs/USER_GUIDE.md](pinyin_app/docs/USER_GUIDE.md)
- Descargas y compilación: [docs/DOWNLOAD.md](docs/DOWNLOAD.md)

## Para desarrolladores

Consultá la arquitectura en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y los pasos de build en [docs/DOWNLOAD.md](docs/DOWNLOAD.md).

Pruebas:

```bash
python -m unittest discover tests
```
