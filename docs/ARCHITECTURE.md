# Arquitectura

## Flujo en tiempo de ejecución

- `pinyin_app/pinyin_live.py` inicia los listeners globales de teclado y el icono en la bandeja.
- `pinyin_app/pinyin_converter.py` convierte tokens como `ni3` o `hao3` en pinyin con marcas de tono.
- El listener en vivo mantiene un buffer pequeño, detecta el atajo configurado y reemplaza el último token usando el portapapeles para asegurar la compatibilidad Unicode.
- Durante el reemplazo se activa una ventana corta de supresión de entrada para evitar que las pulsaciones sintetizadas reingresen al listener.

## Componentes

- Icono en bandeja: muestra el estado activo/inactivo y abre la ventana de configuración.
- Diálogo de configuración: captura el atajo directamente desde las teclas presionadas y lo guarda en `pinyin_app/config.json`.
- El diálogo usa una vista previa de solo lectura y botones alineados para una experiencia sencilla.
- La opción "Iniciar con el sistema" escribe la entrada nativa correspondiente en Windows, macOS o Linux.
- Registro (logging): se escribe en `pinyin_app/pinyin_app.log` para depuración.
- Salir desde la bandeja envía la señal para terminar el bucle principal de forma ordenada.

## Objetivos de diseño

- Dependencias mínimas.
- Comportamiento multiplataforma en Windows, macOS y Linux (cuando `pynput` lo soporta).
- Reemplazo en vivo rápido y con mínima interrupción a la escritura.
