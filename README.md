# PhishingCol

Sistema determinístico y explicable para detección de phishing basado en URLs y dominios en el contexto colombiano. La implementación respeta la arquitectura modular por capas definida en la Entrega 2 y mantiene reglas y pesos fuera del core en archivos JSON.

## Estructura

- `presentation/`: `InputHandler` y `CLIController`.
- `application/`: orquestación de análisis manual, batch, reportes y alertas.
- `domain/`: extracción de features, scoring, clasificación y explicación.
- `infrastructure/`: acceso a configuración, persistencia mock, reportes, logging y análisis HTTP estático.
- `config/`: `empresas.json` y `pesos.json`.
- `tests/`: pruebas unitarias e integración.
- `main.py`: punto de entrada.

## Ejecución

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar análisis manual:

```bash
python main.py banc0lombia-seguridad.xyz
```

4. Ejecutar monitoreo batch:

```bash
python main.py --batch listas/2026-01-31.txt --output-dir output
```

5. Ejecutar pruebas:

```bash
pytest
```

## Restricciones implementadas

- Solo analiza URLs y dominios.
- Motor determinístico basado en reglas configurables.
- Análisis de contenido opcional, con timeout de 2 segundos y sin JavaScript.
- Manejo de errores con resultados parciales y mensajes controlados.
- Trazabilidad completa: score, reglas activadas, evidencia y limitaciones.
