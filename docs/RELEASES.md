# Publicar releases

## Flujo

1. Actualizá la versión en `pyproject.toml` y `src/pinyin_tones/version.py`.
2. Ejecutá la suite local y creá el tag `vX.Y.Z`.
3. El workflow construye Windows x64, macOS x64, macOS arm64 y Linux x64 de forma nativa.
4. GitHub crea una release en borrador con ZIPs portables, DMGs, AppImage, DEB y `SHA256SUMS.txt`.
5. Probá los instaladores antes de publicar el borrador.

## Secretos de macOS

Configurá estos secretos antes de crear un tag de release:

- `MACOS_CERTIFICATE_P12_BASE64`
- `MACOS_CERTIFICATE_PASSWORD`
- `MACOS_SIGNING_IDENTITY`
- `APPLE_API_KEY_P8_BASE64`
- `APPLE_API_KEY_ID`
- `APPLE_API_ISSUER_ID`

El certificado, la clave privada y las credenciales de App Store Connect no deben incorporarse al repositorio.

## Checklist manual

- Abrir la app, conceder permisos de macOS y verificar reemplazo, bandeja y autostart en Intel y Apple Silicon.
- Probar AppImage y DEB en Ubuntu 22.04 y 24.04 con X11.
- Verificar Windows x64 y que cada asset coincida con `SHA256SUMS.txt`.
- Publicar la release borrador sólo cuando esas pruebas estén completas.
