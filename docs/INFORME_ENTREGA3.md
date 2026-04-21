# Informe de Entrega 3

## Construccion, Codificacion, Pruebas y Aseguramiento de Calidad

### Datos del proyecto

- Proyecto: `PhishingCol`
- Tipo de solucion: sistema deterministico y explicable de deteccion de phishing
- Dominio del problema: analisis de URLs y dominios con enfoque en marcas usadas en Colombia
- Repositorio fuente: repositorio Git del proyecto
- Fecha de entrega: `[Completar]`
- Integrantes: `[Completar]`

## 1. Resumen ejecutivo

`PhishingCol` es una solucion construida para identificar URLs y dominios sospechosos mediante un pipeline deterministico basado en reglas configurables, catalogo de marcas, scoring trazable y explicaciones legibles para el usuario. El sistema no depende de modelos predictivos para detectar phishing: la evaluacion principal se hace con reglas, pesos y umbrales definidos externamente.

Durante la Entrega 3 se consolidaron los siguientes avances:

- construccion coherente con la arquitectura aprobada en la Entrega 2
- integracion de interfaz web, ejecucion manual por CLI y procesamiento batch
- ampliacion del catalogo de empresas colombianas objetivo de phishing
- incorporacion de controles de calidad en CI con linting y SAST
- documentacion formal de estrategia de pruebas
- integracion opcional con OpenRouter para transformar el resultado tecnico en lenguaje humano
- mejora de la UI para hacer mas visible el resultado del analisis

Sugerencia de evidencia visual:

- Figura 1. Vista general de la interfaz principal.
- Figura 2. Resultado de un analisis con riesgo `HIGH`.

## 2. Descripcion general de la solucion

El sistema analiza una entrada individual o un conjunto de dominios y produce:

- dominio normalizado
- score total
- nivel de riesgo
- reglas activadas
- evidencia observada
- limitaciones del analisis
- persistencia del resultado
- alertas y reportes para ejecuciones batch

Adicionalmente, para la UI manual, se agrego una capa opcional de asistencia con IA que recibe el resultado estructurado y lo convierte en:

- resumen narrativo
- pasos sugeridos
- disclaimer explicito de uso de inteligencia artificial

Importante:

- la IA no modifica el `score`
- la IA no modifica la `risk_level`
- la IA no reemplaza las reglas del sistema
- la IA solo reexpresa en lenguaje humano un resultado ya calculado por el motor deterministico

Sugerencia de evidencia visual:

- Figura 3. Seccion de resumen asistido por IA visible en la UI.

## 3. Construccion y codificacion

### 3.1 Calidad del codigo y coherencia con el diseno

La implementacion mantiene separacion por capas y responsabilidades:

- `presentation/`: controladores CLI y web, manejo de formularios y template HTML
- `application/`: orquestacion de casos de uso y servicios
- `domain/`: extraccion de features, scoring, clasificacion y explicaciones
- `infrastructure/`: configuracion, persistencia, logging, reportes y fetch HTTP estatico
- `config/`: catalogo de empresas y reglas/pesos del motor
- `tests/`: pruebas unitarias, de integracion y funcionales

Esta organizacion es coherente con la arquitectura aprobada y facilita:

- legibilidad
- mantenibilidad
- pruebas por componente
- desacoplamiento entre reglas, datos y presentacion

Los componentes clave implementados en el proyecto son:

- `InputHandler`
- `AnalysisService`
- `URLDomainAnalyzer`
- `FeatureExtractor`
- `ScoringEngine`
- `RiskClassifier`
- `ExplanationBuilder`
- `BatchMonitorService`
- `ReportService`
- `AlertService`
- `ResultRepository`
- `ConfigProvider`

Sugerencia de evidencia visual:

- Figura 4. Arbol del proyecto o captura del repositorio con sus capas.

### 3.2 Gestion de dependencias y configuraciones

El proyecto usa un conjunto pequeno y controlado de dependencias, definidas en `requirements.txt`:

- `Flask==3.1.0`
- `psycopg[binary]==3.2.6`
- `pytest==8.3.5`
- `pytest-cov==6.0.0`

La configuracion se mantiene fuera del codigo fuente:

- `config/empresas.json`: marcas, dominios oficiales y palabras clave
- `config/pesos.json`: reglas, pesos, umbrales y timeouts
- `.env.example`: variables para persistencia, despliegue y OpenRouter

Esto permite ajustar el comportamiento del sistema sin modificar el core analitico.

Variables nuevas agregadas para la integracion con OpenRouter:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_TIMEOUT_SECONDS`
- `OPENROUTER_REFERER`
- `OPENROUTER_APP_TITLE`

### 3.3 Uso responsable de IA generativa

El uso de IA en este proyecto fue incorporado de forma controlada y responsable.

Su alcance funcional real es el siguiente:

- recibe el resultado deterministico ya calculado por el sistema
- genera un resumen narrativo entendible para el usuario
- propone pasos sugeridos
- muestra un disclaimer visible dentro de la interfaz

Restricciones explicitas:

- no participa en el scoring
- no cambia la clasificacion de riesgo
- no altera las reglas configuradas
- no reemplaza las validaciones ni las pruebas del proyecto

Esto permite sustentar que la IA es una capa asistencial y no un mecanismo de decision del producto.

### 3.4 Control de versiones

El proyecto utiliza Git como mecanismo de trazabilidad. El historial reciente evidencia evolucion funcional, mejoras de calidad y fortalecimiento documental.

Historial reciente observado:

```text
ff2e89b (HEAD -> feature, origin/feature) Foco en el analisis cuando se ha generado para guiar la lectura por parte del usuario
70402ae Resumen generado por IA para el score del analisis de dominio
a603899 Actualizacion de Documentacion
1b766aa (origin/empresas, empresas) Agregar nuevas empresas al catalogo
70c14af (origin/main, origin/HEAD, main) Merge pull request #3 from CarlosKC26/linters
f78bf60 (origin/linters, linters) Se eliminan archivos externos al repo
2c2b647 Merge pull request #2 from CarlosKC26/linters
2c7c1e0 Se eliminaron archivos .json que no se usan y se amplio el pipeline ci para usar linters y sast
13b6195 Merge pull request #1 from CarlosKC26/inicial
b5532e0 (origin/inicial) Actualizacion de readme
431205a Correccion docker-compose
e6da0bf se dejan de seguir archivos agragados al .gitignore
```

Sugerencia de evidencia visual:

- Figura 5. Captura del historial de commits o de la rama del feature.

## 4. Pruebas y aseguramiento de calidad

### 4.1 Estrategia de pruebas

La estrategia formal se documenta en [tests/TEST_STRATEGY.md](../tests/TEST_STRATEGY.md). El enfoque cubre:

- pruebas unitarias
- pruebas de integracion
- pruebas funcionales de la interfaz web
- validacion del flujo batch
- validacion de la capa opcional de resumen asistido por IA

El alcance actual contempla:

- validacion y normalizacion de entrada
- extraccion de features de dominio y contenido estatico
- scoring por reglas
- clasificacion por umbrales
- generacion de explicaciones
- persistencia de resultados
- batch con alertas y reportes
- comportamiento observable desde la UI

### 4.2 Suite de pruebas implementada

La suite automatizada actual incluye, entre otros, los siguientes archivos:

- `tests/test_input_handler.py`
- `tests/test_feature_extractor.py`
- `tests/test_scoring_engine.py`
- `tests/test_risk_classifier.py`
- `tests/test_repository_factory.py`
- `tests/test_result_repository_postgresql.py`
- `tests/test_analysis_pipeline.py`
- `tests/test_web_controller.py`
- `tests/test_ai_summary_integration.py`

Estos archivos cubren:

- reglas del core analitico
- integracion del pipeline completo
- persistencia mock y PostgreSQL
- UI web
- resumen narrativo por IA sin impacto sobre score ni riesgo

### 4.3 Evidencia de ejecucion y resultados

Ultima validacion local registrada durante el desarrollo de esta entrega:

- pruebas ejecutadas: `30`
- resultado: `30 passed`
- cobertura total: `81%`
- lint: `OK`
- SAST: `OK`

Resumen de salida de pruebas:

```text
collected 30 items
30 passed
```

Resumen de cobertura:

```text
TOTAL 1621 307 81%
```

Resultado de lint:

```text
All checks passed!
```

Resultado de SAST:

```text
No issues identified.
Total issues (by severity): 0
```

Sugerencia de evidencia visual:

- Figura 6. Captura de `python -m pytest`
- Figura 7. Captura de `python -m pytest --cov=. --cov-report=term-missing`
- Figura 8. Captura de `python -m ruff check .`
- Figura 9. Captura de `python -m bandit -r ...`

### 4.4 Comandos usados para sustentar la entrega

Los siguientes comandos quedaron documentados y fueron los usados como referencia de validacion en el proyecto:

```powershell
python -m pip install -r requirements.txt
python -m pytest
python -m pytest --cov=. --cov-report=term-missing
python -m ruff check .
python -m bandit -r application domain infrastructure presentation main.py web_main.py core.py
```

Comandos funcionales recomendados para evidencia manual:

```powershell
python main.py banc0lombia-verificacion.xyz
python main.py --batch listas/2026-01-31.txt --output-dir output
python web_main.py
```

### 4.5 Validacion de requisitos y casos de negocio

Los requisitos funcionales y de negocio quedan evidenciados en estos escenarios:

- analisis de una URL legitima de marca oficial
- deteccion de typosquatting
- deteccion de phishing con keywords de ingenieria social
- evaluacion de dominios anormalmente largos
- manejo controlado de timeout o error HTTP
- generacion de explicacion trazable con reglas, score, evidencia y limitaciones
- ejecucion batch con alertas y reportes
- resumen asistido por IA para lectura humana del resultado

Trazabilidad resumida entre requisito y evidencia:

| Requisito o capacidad | Evidencia principal |
| --- | --- |
| Validacion y normalizacion de entrada | `tests/test_input_handler.py` |
| Extraccion de features y reglas de dominio | `tests/test_feature_extractor.py`, `tests/test_scoring_engine.py` |
| Clasificacion deterministica por score | `tests/test_risk_classifier.py` |
| Pipeline end-to-end | `tests/test_analysis_pipeline.py` |
| Persistencia | `tests/test_repository_factory.py`, `tests/test_result_repository_postgresql.py` |
| UI manual y batch | `tests/test_web_controller.py` |
| Capa asistida por IA | `tests/test_ai_summary_integration.py`, `tests/test_web_controller.py` |

## 5. Mejoras y defectos gestionados durante la construccion

Durante el desarrollo de la Entrega 3 se identificaron y atendieron mejoras relevantes:

| Ajuste o defecto | Impacto | Accion aplicada |
| --- | --- | --- |
| CI inicial solo con `pytest` | Aseguramiento insuficiente | Se agregaron `ruff` y `bandit` al workflow |
| Archivos externos dentro del repositorio | Ruido y riesgo de contaminar la entrega | Se retiraron archivos ajenos al codigo fuente |
| Catalogo limitado de marcas | Menor cobertura del contexto colombiano | Se ampliaron empresas y palabras clave en `config/empresas.json` |
| Salida tecnica poco amigable | Dificultad para usuarios no tecnicos | Se agrego resumen narrativo con OpenRouter |
| Resultado poco visible en la UI | Mala experiencia de uso | Se compacto el hero y se hizo mas visible el bloque de resultado |

Sugerencia de evidencia visual:

- Figura 10. Captura del workflow de CI con checks exitosos.
- Figura 11. Captura de la UI mostrando el nuevo resumen visible del analisis.

## 6. Entregables incluidos en el repositorio

El repositorio ya contiene los elementos esperados por la rubrica:

- codigo fuente versionado y accesible
- instrucciones de compilacion y ejecucion en [README.md](../README.md)
- evidencia de control de versiones con Git
- conjunto de pruebas automatizadas en `tests/`
- documento de estrategia de pruebas en [tests/TEST_STRATEGY.md](../tests/TEST_STRATEGY.md)
- informe de entrega en este archivo
- workflow de CI en [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- configuracion externa en `config/`
- variables de entorno de ejemplo en `.env.example`

## 7. Guia para insertar imagenes en este informe

Se recomienda guardar las capturas dentro de `docs/capturas/`.

Ejemplo de insercion en Markdown:

```md
![Figura 1 - Interfaz principal](capturas/figura-01-ui-principal.png)
```

Imagenes sugeridas para complementar la entrega:

- `capturas/figura-01-ui-principal.png`
- `capturas/figura-02-resultado-high.png`
- `capturas/figura-03-resumen-ia.png`
- `capturas/figura-04-arquitectura-o-arbol.png`
- `capturas/figura-05-git-log-o-rama.png`
- `capturas/figura-06-pytest.png`
- `capturas/figura-07-cobertura.png`
- `capturas/figura-08-ruff.png`
- `capturas/figura-09-bandit.png`
- `capturas/figura-10-ci-github-actions.png`
- `capturas/figura-11-ui-resultado-visible.png`

## 8. Conclusiones

La Entrega 3 evidencia una construccion consistente con la arquitectura aprobada, una implementacion modular y configurable, una estrategia de pruebas formalizada y controles adicionales de aseguramiento de calidad.

El proyecto cumple con los criterios de la rubrica porque:

- mantiene calidad de codigo y separacion clara de responsabilidades
- usa control de versiones de forma trazable
- gestiona dependencias y configuracion de manera externa y controlada
- incorpora un uso responsable de IA generativa
- documenta y ejecuta pruebas unitarias, de integracion y funcionales
- presenta evidencia objetiva de cobertura, lint y SAST

En conjunto, `PhishingCol` queda presentado como una solucion funcional, explicable, comprobable y preparada para una sustentacion academica solida.

## 9. Anexo de reproduccion

Si se necesita regenerar la evidencia antes de entregar, estos son los comandos base:

### Instalacion

```powershell
python -m pip install -r requirements.txt
```

### Pruebas

```powershell
python -m pytest
python -m pytest --cov=. --cov-report=term-missing
```

### Calidad estatica

```powershell
python -m ruff check .
python -m bandit -r application domain infrastructure presentation main.py web_main.py core.py
```

### Ejecucion manual

```powershell
python main.py banc0lombia-verificacion.xyz
python web_main.py
```

### Batch

```powershell
python main.py --batch listas/2026-01-31.txt --output-dir output
```
