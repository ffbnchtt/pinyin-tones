# Contribuciones

Gracias por querer colaborar con Pinyin Tones. A continuación tenés pautas para abrir *issues* y *pull requests* que facilitan la revisión y la incorporación de cambios.

## Issues

Los *issues* son muy importantes. Usalos para reportar errores, proponer mejoras o pedir ayuda.

- Describí claramente el problema o la idea.
- Incluí el sistema operativo y la versión de la aplicación si reportás un bug.
- Indicá pasos mínimos para reproducir el problema (si aplica).

Si el problema es una posible vulnerabilidad de seguridad, no uses la plantilla de bug report: consultá [SECURITY.md](SECURITY.md).

## Pull requests (PR)

Los PR son la mejor forma de proponer cambios. Antes de abrir un PR grande, abrí un issue para discutir la propuesta si puede afectar a usuarios o al diseño.

Al crear un PR, tené en cuenta:

### Explicá la intención

Dejá claro qué problema resolvés y por qué. Por ejemplo:

>`ni3` no se reemplaza correctamente a `nǐ` cuando el número de tono es 3.

Esto ayuda a revisar y entender el cambio.

### Calidad del aporte

- Evitá faltas de ortografía y redacción confusa.
- Añadí tests o actualizá los existentes en `tests/` cuando corresponda.
- Asegurate de que el código se ejecute sin errores después de tu cambio.

### ¿Aporta al objetivo del proyecto?

Los cambios deben acercar el repositorio a su objetivo: ofrecer reemplazo en vivo de tokens por tonos con un funcionamiento rápido y confiable.

## Flujo recomendado

1. Forkeá el repo y creá un branch con nombre `feature/tu-feature` o `fix/tu-fix`.
2. Hacé commits pequeños y con mensajes descriptivos.
3. Incluí o actualizá tests cuando el cambio afecta comportamiento.
4. Abrí el PR y enlazá el issue relacionado (si existe).

## Ejecutar pruebas localmente

Para ejecutar las pruebas del proyecto:

```bash
python tools/run_tests.py
```

## Plantillas de issues y PR

Al crear un *issue* o una *PR* podés usar las plantillas preparadas para facilitar la revisión:

- Informe de bug: `.github/ISSUE_TEMPLATE/bug_report.md`
- Propuesta de mejora: `.github/ISSUE_TEMPLATE/feature_request.md`
- Plantilla de Pull Request: `.github/PULL_REQUEST_TEMPLATE.md`

Usar estas plantillas ayuda a incluir la información necesaria (SO, pasos para reproducir, propuesta de solución, tests, etc.).

## Contacto y soporte

Si necesitás ayuda rápida, podés abrir un *issue* describiendo el problema y el sistema operativo.

---

Gracias por contribuir y ayudar a mejorar Pinyin Tones.
