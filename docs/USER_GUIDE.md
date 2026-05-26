# Guía de Usuario - Pinyin Tones

## Qué hace esta aplicación

Pinyin Tones escucha lo que escribís y convierte tokens como `ni3` o `hao3` en Pinyin con marcas de tono en tiempo real.

Esta aplicación es portable: no se instala nada en el sistema. Todo queda en la carpeta donde la ejecutás.

## Uso básico

1. Iniciá la aplicación.
2. Usá el atajo o el ícono en la bandeja del sistema para activarla o desactivarla.
3. Escribí un token de Pinyin seguido por un número de tono (1-5).
4. La aplicación reemplaza el token con la versión con marca de tono.

## Configuración

Abrí la ventana de configuración desde el ícono de la bandeja para cambiar:

- el atajo global
- si la aplicación inicia con el sistema operativo

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

## Cómo desinstalar

Antes de borrar la carpeta, abrí la configuración y desactivá "Iniciar con el sistema operativo".
Si borrás la carpeta sin desactivar esa opción, el sistema intentará iniciar la app en el próximo inicio de sesión.

1. Desactivá el inicio automático desde la configuración.
2. Borrá la carpeta donde descomprimiste la aplicación.

## Archivos incluidos en un release

- el ejecutable o bundle de la aplicación
- `LICENSE` (licencia MIT)
- `USER_GUIDE.md` (esta guía)
