# Guía de Usuario - Pinyin Tones

## Qué hace esta aplicación

Pinyin Tones escucha lo que escribes y convierte tokens como `ni3` o `hao3` en Pinyin con marcas de tono en tiempo real.

## Uso básico

1. Inicia la aplicación.
2. Usa el icono en la bandeja del sistema para activarla o desactivarla.
3. Escribe un token de Pinyin seguido por un número de tono (1-5).
4. La aplicación reemplaza el token con la versión con marca de tono.

## Configuración

Abre la ventana de configuración desde el icono de la bandeja para cambiar:

- el atajo global
- si la aplicación inicia con el sistema operativo

## Atajos recomendados

Usa un atajo basado en una letra con modificadores, como:

- `Ctrl+Alt+P`
- `Ctrl+Shift+P`
- `Ctrl+Alt+T`

Evita atajos que ya estén en uso por Windows, macOS, Linux u otras aplicaciones.

## Solución de problemas

- Si el atajo no se activa, prueba con otra letra.
- Si la app no reemplaza el texto, asegúrate de que está activa desde el menú de la bandeja.
- Si la opción de inicio automático falla, abre nuevamente la ventana de configuración e intenta nuevamente.

## Cómo desinstalar

### Windows

1. Abre el Panel de Control o Configuración.
2. Ve a "Programas" → "Programas y características".
3. Busca "Pinyin Tones" en la lista.
4. Haz clic en el programa y selecciona "Desinstalar".
5. Confirma la desinstalación.

Si iniciaste automáticamente, también se eliminará la entrada del registro de Windows.

### macOS

1. Abre la carpeta Aplicaciones.
2. Busca "Pinyin Tones" (o `pinyin_app`).
3. Arrastra la aplicación a la Papelera o haz clic derecho y selecciona "Mover a la Papelera".
4. Vacía la Papelera.

Si habilitaste el inicio automático, el `LaunchAgent` será limpiado automáticamente la próxima vez que inicie el sistema.

### Linux

1. Elimina el ejecutable de tu carpeta de descargas o aplicaciones:
   ```bash
   rm ~/Desktop/pinyin_app
   # O la ruta donde lo hayas guardado
   ```
2. Si habilitaste inicio automático, también puedes eliminar:
   ```bash
   rm ~/.config/autostart/pinyin-tones.desktop
   ```

## Archivos incluidos en un release

Un release empaquetado debe incluir:

- el ejecutable o bundle de la aplicación
- `LICENSE` (licencia MIT)
- `USER_GUIDE.md` (esta guía)
