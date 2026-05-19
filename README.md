# Pinyin Tones

Conversor de tonos Pinyin en tiempo real, con listener global, icono en bandeja y hotkey configurable.

## Estructura

- `pinyin_app/src/pinyin_converter.py`: reglas de conversión.
- `pinyin_app/src/pinyin_live.py`: listeners, tray icon y reemplazo en vivo.
- `tests/`: pruebas automatizadas.
- `docs/ARCHITECTURE.md`: cómo está programada la app.
- `docs/DOWNLOAD.md`: cómo instalar, ejecutar y compilar.
- `pinyin_app/docs/USER_GUIDE.md`: guía de uso para usuarios finales.

## Inicio rápido

```bash
cd pinyin_app
pip install -r requirements.txt
python src/pinyin_live.py
```

## Pruebas

```bash
python -m unittest discover tests
```

## Archivos generados en runtime

- `pinyin_app/config.json`
- `pinyin_app/pinyin_app.log`

## Compilación

Ver `docs/DOWNLOAD.md` para ejemplos con PyInstaller. El build empaqueta también `LICENSE` y `USER_GUIDE.md` junto al binario, y genera un icono propio para la app.
