# PhishingCol

Sistema determinístico y explicable para detección de phishing basado en URLs y dominios en el contexto colombiano. La implementación respeta la arquitectura modular por capas definida en la Entrega 2, mantiene reglas y pesos fuera del core en archivos JSON, y ahora incluye UI web, contenedores, PostgreSQL opcional y CI para pruebas.

## Estructura

- `presentation/`: `InputHandler`, `CLIController` y `web_controller`.
- `application/`: orquestación de análisis manual, batch, reportes y alertas.
- `domain/`: extracción de features, scoring, clasificación y explicación.
- `infrastructure/`: acceso a configuración, persistencia mock/PostgreSQL, reportes, logging y análisis HTTP estático.
- `config/`: `empresas.json` y `pesos.json`.
- `tests/`: pruebas unitarias e integración.
- `main.py`: entrada CLI.
- `web_main.py`: entrada de la interfaz web.

## Ejecución local

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar análisis manual por CLI:

```bash
python main.py banc0lombia-seguridad.xyz
```

4. Ejecutar la interfaz web:

```bash
python web_main.py
```

5. Abrir en el navegador:

```text
http://127.0.0.1:8000
```

6. Desde la UI se puede:

- analizar una URL o dominio individual
- cargar archivos `.txt` o `.zip` para monitoreo batch
- pegar listas de dominios para procesamiento batch
- consultar resumen de resultados y reportes generados

7. Ejecutar pruebas:

```bash
pytest
```

## Persistencia

- `RESULT_BACKEND=mock`: guarda resultados en `output/results.json`.
- `RESULT_BACKEND=postgresql`: usa `DATABASE_URL` y persiste en PostgreSQL.

Si PostgreSQL no está disponible o la configuración es inválida, el sistema vuelve de forma controlada a persistencia mock.

## Contenedores

1. Copiar variables base:

```bash
cp .env.example .env
```

2. Levantar base de datos y UI web:

```bash
docker compose up --build
```

3. Abrir la interfaz:

```text
http://127.0.0.1:8000
```

4. Ejecutar análisis manual por CLI dentro del contenedor:

```bash
docker compose --profile cli run --rm app banc0lombia-verificacion.xyz
```

5. Ejecutar pruebas dentro del contenedor:

```bash
docker compose --profile cli run --rm app python -m pytest
```

## CI/CD mínimo

Se incluye el workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) para ejecutar pruebas automáticamente en `push` y `pull_request`.

## Restricciones implementadas

- Solo analiza URLs y dominios.
- Motor determinístico basado en reglas configurables.
- Análisis de contenido opcional, con timeout de 2 segundos y sin JavaScript.
- Manejo de errores con resultados parciales y mensajes controlados.
- Trazabilidad completa: score, reglas activadas, evidencia y limitaciones.
