# Guía de Usuario - Pinyin Tones

## Qué hace esta aplicación

Pinyin Tones convierte sílabas de pinyin con número de tono, como `ni3` o `hao3`, en pinyin con marcas de tono: `nǐ`, `hǎo`.

Esta aplicación es portable: no requiere instalación. La app intenta guardar configuración, logs y descargas de actualizaciones en la carpeta donde la ejecutás; si esa carpeta no es escribible, usa una carpeta de datos del usuario.

## Uso básico

1. Iniciá la aplicación.
2. Usá el atajo o el ícono en la bandeja del sistema para activarla o desactivarla.
3. Escribí una sílaba de pinyin y agregá el número del tono al final.
4. La aplicación reemplaza automáticamente lo que escribiste por la versión con marca de tono.

Ejemplos:

- `ni3` se convierte en `nǐ`
- `hao3` se convierte en `hǎo`
- `zhong1` se convierte en `zhōng`
- `guo2` se convierte en `guó`

Usá los números `1`, `2`, `3` y `4` para los tonos.

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
