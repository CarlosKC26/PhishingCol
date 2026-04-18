# PhishingCol

Sistema deterministico y explicable para deteccion de phishing basado en URLs y dominios en el contexto colombiano. La implementacion respeta la arquitectura modular por capas definida en la Entrega 2, mantiene reglas y pesos fuera del core en archivos JSON, e incluye CLI, UI web, monitoreo batch, persistencia mock/PostgreSQL, contenedores y CI para pruebas.

## Alcance y restricciones

- Solo analiza URLs y dominios.
- El motor es deterministico: misma entrada, mismo resultado.
- El scoring usa reglas configurables y trazables.
- El analisis de contenido es opcional, sin JavaScript y con timeout corto.
- Las reglas y el catalogo de marcas se cargan desde archivos JSON externos.

## Capacidades actuales

- Analisis manual por CLI.
- Analisis manual desde UI web.
- Resumen narrativo asistido por IA para consultas manuales desde la UI.
- Monitoreo batch desde CLI.
- Monitoreo batch desde UI web mediante archivos `.txt`, `.zip` o texto pegado.
- Persistencia en `output/results.json` o en PostgreSQL.
- Generacion de reportes y alertas para hallazgos de alto riesgo.
- Pipeline trazable con score, nivel de riesgo, reglas activadas, evidencia y limitaciones.

## Estructura del proyecto

- `presentation/`: `InputHandler`, `CLIController`, `web_controller` y templates HTML.
- `application/`: orquestacion de analisis manual, batch, reportes y alertas.
- `domain/`: extraccion de features, scoring, clasificacion y explicacion.
- `infrastructure/`: configuracion, persistencia mock/PostgreSQL, logging, reportes y analisis HTTP estatico.
- `config/`: `empresas.json` y `pesos.json`.
- `tests/`: pruebas unitarias e integracion.
- `main.py`: entrada CLI.
- `web_main.py`: entrada de la UI web.

## Configuracion

Archivos principales:

- `config/empresas.json`: catalogo de marcas y dominios oficiales.
- `config/pesos.json`: reglas, pesos, umbrales y timeouts.
- `.env.example`: variables para Docker y PostgreSQL.

Variables opcionales para el resumen asistido por IA:

- `OPENROUTER_API_KEY`: API key de OpenRouter.
- `OPENROUTER_MODEL`: modelo a utilizar. Si se deja vacio, OpenRouter usa el modelo por defecto configurado para la cuenta.
- `OPENROUTER_TIMEOUT_SECONDS`: timeout de la solicitud al proveedor.
- `OPENROUTER_REFERER`: header opcional `HTTP-Referer`.
- `OPENROUTER_APP_TITLE`: header opcional `X-OpenRouter-Title`.

Backends de persistencia:

- `RESULT_BACKEND=mock`: guarda resultados en `output/results.json`.
- `RESULT_BACKEND=postgresql`: usa `DATABASE_URL` y persiste en PostgreSQL.

Si PostgreSQL no esta disponible o la configuracion es invalida, el sistema vuelve de forma controlada a persistencia mock.

Si existe un archivo `.env` en la raiz del proyecto, la aplicacion lo carga automaticamente al iniciar los servicios.

## Ejecucion local

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Opcional: copiar `.env.example` a `.env` y configurar OpenRouter si quieres habilitar el resumen asistido por IA:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

4. Ejecutar analisis manual por CLI:

```bash
python main.py banc0lombia-verificacion.xyz
```

5. Ejecutar monitoreo batch por CLI:

```bash
python main.py --batch listas/2026-01-31.txt --output-dir output
```

6. Ejecutar la interfaz web:

```bash
python web_main.py
```

7. Abrir en el navegador:

```text
http://127.0.0.1:8000
```

Desde la UI se puede:

- analizar una URL o dominio individual
- generar un resumen narrativo asistido por IA para una consulta manual
- cargar archivos `.txt` o `.zip` para monitoreo batch
- pegar listas de dominios para procesamiento batch
- consultar resumen de resultados, alertas y reportes generados

## Resumen asistido por IA

La integracion con OpenRouter recibe el resultado estructurado del analisis y lo convierte en lenguaje humano para facilitar la lectura por parte del usuario final.

La UI manual puede mostrar:

- resumen narrativo
- pasos sugeridos
- disclaimer explicito sobre uso de inteligencia artificial

Importante:

- la IA no modifica el `score`
- la IA no modifica la `risk_level`
- la IA solo reexpresa el resultado deterministico producido por PhishingCol

Activacion:

1. Configura `OPENROUTER_API_KEY` en `.env` o como variable de entorno.
2. Opcionalmente configura `OPENROUTER_MODEL`.
3. Inicia la UI con `python web_main.py`.
4. Marca la opcion `Generar resumen asistido por IA con OpenRouter`.

## Pruebas y cobertura

Ejecutar la suite:

```bash
python -m pytest
```

Ejecutar con detalle de cobertura:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

Nota:

- en Windows conviene usar `python -m pytest` en lugar de `pytest` para evitar problemas de `PATH`

La estrategia de pruebas esta documentada en [tests/TEST_STRATEGY.md](tests/TEST_STRATEGY.md).

Cobertura esperada del proyecto:

- minima objetivo: 70%+

Niveles cubiertos:

- unitarias: validacion de entrada, extraccion de features, reglas, scoring y clasificacion
- integracion: pipeline completo de analisis y persistencia
- web: consulta manual, resumen asistido por IA y batch desde la UI

## Docker y contenedores

Copiar variables base:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Levantar PostgreSQL y la UI web:

```bash
docker compose up -d --build
```

Abrir la interfaz:

```text
http://127.0.0.1:8000
```

Importante:

- `postgres` y `web` se levantan con `docker compose up`.
- `app` es un contenedor CLI y no queda corriendo en segundo plano.
- Para usar la CLI en Docker se ejecuta con `run --rm`.

Analisis manual por CLI dentro del contenedor:

```bash
docker compose --profile cli run --rm app banc0lombia-verificacion.xyz
```

Monitoreo batch por CLI dentro del contenedor:

```bash
docker compose --profile cli run --rm app --batch listas/2026-01-31.txt --output-dir output
```

Pruebas dentro del contenedor:

```bash
docker compose --profile cli run --rm app python -m pytest
```

Consultar logs de la UI:

```bash
docker compose logs -f web
```

Verificar persistencia en PostgreSQL:

```bash
docker compose exec postgres psql -U phishingcol -d phishingcol -c "SELECT normalized_domain, risk_level, score FROM analysis_results ORDER BY id DESC LIMIT 10;"
```

Detener servicios:

```bash
docker compose down
```

## CI minimo

Se incluye el workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) para ejecutar controles automaticos en `push` y `pull_request`.

Checks actuales del pipeline:

- `ruff` para linting
- `bandit` para analisis SAST
- `pytest` para pruebas automatizadas

Documentacion oficial usada para la integracion OpenRouter:

- Quickstart: https://openrouter.ai/docs
- Chat Completions API: https://openrouter.ai/docs/api-reference/chat-completion
- Authentication y API keys: https://openrouter.ai/docs/api-keys

## Validacion de la Entrega 3

Para cumplir y sustentar la rubrica de la Entrega 3, conviene presentar estas evidencias:

### 1. Calidad de codigo

- Arquitectura por capas coherente con la Entrega 2.
- Modulos separados por responsabilidad.
- Tipado explicito y funciones pequenas.
- Configuracion externa en `config/empresas.json` y `config/pesos.json`.

### 2. Coherencia con el diseno

Mencionar que el sistema implementa los modulos definidos en la arquitectura:

- `InputHandler`
- `AnalysisService`
- `URLDomainAnalyzer`
- `FeatureExtractor`
- `ScoringEngine`
- `RiskClassifier`
- `ExplanationBuilder`
- `BrandCatalogService`
- `BatchMonitorService`
- `ReportService`
- `AlertService`
- `ResultRepository`
- `ConfigProvider`
- `LoggingMonitoring`

### 3. Pruebas completas

Adjuntar o citar:

- [tests/TEST_STRATEGY.md](tests/TEST_STRATEGY.md)
- salida de `python -m pytest`
- salida de `python -m pytest --cov=. --cov-report=term-missing`

Casos minimos que debes mencionar en el informe:

- URL legitima
- typosquatting
- phishing con keywords
- dominio largo sospechoso
- error HTTP o timeout simulado con resultado parcial
- resumen asistido por IA generado a partir de un resultado deterministico

### 4. Validacion de requisitos

Conviene evidenciar, con capturas o salidas JSON, que el sistema:

- valida y normaliza entrada
- extrae features de dominio, TLD, longitud, subdominios, keywords y typosquatting
- aplica reglas configuradas externamente
- calcula score con desglose por regla
- clasifica riesgo por umbrales configurables
- genera explicacion trazable con score, evidencia, reglas y limitaciones
- persiste resultados
- soporta consulta manual y monitoreo batch

### 5. Evidencia recomendada para el informe

Puedes generar evidencia con estos comandos:

Analisis manual:

```bash
python main.py banc0lombia-verificacion.xyz
```

Batch local:

```bash
python main.py --batch listas/2026-01-31.txt --output-dir output
```

Pruebas y cobertura:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

Despliegue con Docker:

```bash
docker compose up -d --build
```

Si vas a mencionar despliegue, aclara que el proyecto ya incluye:

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- workflow de CI
- persistencia PostgreSQL opcional

### 6. Control de versiones, configuracion e IA

Para cubrir los puntos restantes de la rubrica, adjunta tambien:

- evidencia de historial de commits con `git log --oneline --decorate -n 10`
- `requirements.txt` como evidencia de gestion de dependencias
- `.env.example`, `config/empresas.json` y `config/pesos.json` como evidencia de configuracion externa
- una nota breve indicando que el core analitico no usa IA para scoring ni clasificacion
- una nota breve indicando que cualquier uso de IA generativa fue asistencial y que el codigo y las pruebas fueron verificados manualmente

### Uso responsable de IA generativa

En este proyecto, cualquier uso de IA generativa debe presentarse como apoyo asistencial y no como mecanismo de decision del producto.

Puntos que conviene declarar en la entrega:

- la IA no participa en el scoring ni en la clasificacion de riesgo
- el motor analitico es deterministico y basado en reglas configurables
- las decisiones tecnicas, pruebas y validaciones finales fueron revisadas manualmente
- la IA se uso, en caso de mencionarse, para apoyo en redaccion, refactorizacion o generacion asistida de codigo bajo supervision

### 7. Defectos y correcciones

Si el profesor pide gestion de defectos, incluye una tabla corta con:

- defecto identificado
- impacto
- correccion aplicada
- evidencia de validacion

Ejemplos validos de este proyecto:

- correccion de serializacion JSONB para persistencia en PostgreSQL
- ajuste del flujo Docker separando `web` persistente y `app` CLI efimera
- ampliacion de la UI para soportar batch sin duplicar la logica del core

Tambien puedes mencionar como correccion reciente de aseguramiento de calidad:

- incorporacion de lint con `ruff` y SAST con `bandit` en el workflow de CI

## Restricciones implementadas

- Solo analiza URLs y dominios.
- No usa ML o IA en el scoring.
- Motor deterministico basado en reglas configurables.
- Analisis de contenido opcional, con timeout de 2 segundos y sin JavaScript.
- Manejo de errores con resultados parciales y mensajes controlados.
- Trazabilidad completa: score, reglas activadas, evidencia y limitaciones.
