# Guía de Usuario - Pinyin Tones

## Qué hace esta aplicación

Pinyin Tones escucha lo que escribís y convierte tokens como `ni3` o `hao3` en Pinyin con marcas de tono en tiempo real.

Esta aplicación es portable: no requiere instalación. La app intenta guardar configuración, logs y descargas de actualizaciones en la carpeta donde la ejecutás; si esa carpeta no es escribible, usa una carpeta de datos del usuario.

## Uso básico

1. Iniciá la aplicación.
2. Usá el atajo o el ícono en la bandeja del sistema para activarla o desactivarla.
3. Escribí un token de Pinyin seguido por un número de tono (1-4).
4. La aplicación reemplaza el token con la versión con marca de tono.

## Configuración

Abrí la ventana de configuración desde el ícono de la bandeja para cambiar:

- el atajo global
- si la aplicación inicia con el sistema operativo

La configuración se guarda en `config.json`. En Windows, si la carpeta del ejecutable no permite escritura, la ruta alternativa es `%LOCALAPPDATA%\Pinyin Tones`.

## Atajos recomendados

Usá un atajo basado en una letra con modificadores, como:

- `Ctrl+Alt+P`
- `Ctrl+Shift+P`
- `Ctrl+Alt+T`

Evitá atajos que ya estén en uso por el sistema operativo u otras aplicaciones.

## Solución de problemas

- Si el atajo no se activa, probá con otra letra.
- Si la app no reemplaza el texto, aseguráte de que está activa desde el menú de la bandeja.
- Si la opción de inicio automático falla, abrí nuevamente la ventana de configuración e intentá de nuevo.
- Si no aparece el ícono en la bandeja, reiniciá la aplicación.
- Si ejecutás la app desde una carpeta protegida o sincronizada y no guarda cambios, movela a una carpeta escribible o revisá la carpeta de datos del usuario.

## Cómo desinstalar

Antes de borrar la carpeta, abrí la configuración y desactivá "Iniciar con el sistema operativo".
Si borrás la carpeta sin desactivar esa opción, el sistema intentará iniciar la app en el próximo inicio de sesión.

1. Desactivá el inicio automático desde la configuración.
2. Borrá la carpeta donde descomprimiste la aplicación.

## Archivos incluidos en un release

- el ejecutable o bundle de la aplicación
- `LICENSE` (licencia MIT)
- `USER_GUIDE.md` (esta guía)
