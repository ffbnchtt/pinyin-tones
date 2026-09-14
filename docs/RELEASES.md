# Publicar releases

## Flujo

1. Actualizá la versión en `pyproject.toml` y `src/pinyin_tones/version.py`.
2. Ejecutá la suite local y creá el tag `vX.Y.Z`.
3. El workflow construye Windows x64, macOS x64, macOS arm64 y Linux x64 de forma nativa.
4. GitHub crea una release en borrador con ZIPs portables, AppImage, DEB y `SHA256SUMS.txt`; también agrega DMGs cuando macOS se firma y notariza.
5. Probá los instaladores antes de publicar el borrador.

## Firma y notarización de macOS

El workflow puede crear los assets de los tres sistemas sin certificados. Si faltan los secretos de macOS, publica ZIPs sin firma ni notarización; probalos y dejá esa condición explícita en las notas de la release para que los usuarios sepan que Gatekeeper puede mostrar una advertencia.

Para publicar macOS firmado y notarizado, configurá estos secretos y la variable de repositorio `MACOS_SIGNING_ENABLED` con el valor `true` antes de crear el tag:

- `MACOS_CERTIFICATE_P12_BASE64`
- `MACOS_CERTIFICATE_PASSWORD`
- `MACOS_SIGNING_IDENTITY`
- `APPLE_API_KEY_P8_BASE64`
- `APPLE_API_KEY_ID`
- `APPLE_API_ISSUER_ID`

El certificado, la clave privada y las credenciales de App Store Connect no deben incorporarse al repositorio.

## Checklist manual

- Abrir la app, conceder permisos de macOS y verificar reemplazo, bandeja y autostart en Intel y Apple Silicon.
- Si macOS se publicó sin firma, verificar que los ZIP lleven una advertencia visible en las notas de la release.
- Probar AppImage y DEB en Ubuntu 22.04 y 24.04 con X11.
- Verificar Windows x64 y que cada asset coincida con `SHA256SUMS.txt`.
- Publicar la release borrador sólo cuando esas pruebas estén completas.
