# Informe de Entrega 3

## Construccion, Codificacion y Pruebas

### 1. Datos generales del proyecto

- Nombre del proyecto: `PhishingCol`
- Tipo de solucion: sistema deterministico de deteccion de phishing basado en URLs y dominios
- Contexto: deteccion orientada al entorno colombiano
- Repositorio fuente: repositorio Git del proyecto

## 2. Resumen ejecutivo

`PhishingCol` implementa un pipeline modular para analizar URLs y dominios sospechosos mediante reglas configurables, catalogo de marcas y scoring explicable. El sistema incluye ejecucion manual por CLI, interfaz web, procesamiento batch, persistencia mock o PostgreSQL, reportes, alertas y pruebas automatizadas.

La construccion de la Entrega 3 se enfoco en:

- codificacion coherente con la arquitectura aprobada
- configuracion externa del comportamiento analitico
- pruebas automatizadas unitarias, de integracion y funcionales
- aseguramiento de calidad con linting y analisis SAST

## 3. Construccion y codificacion

### 3.1 Calidad del codigo

El proyecto mantiene separacion por capas y responsabilidades:

- `presentation/`: controladores CLI y web, validacion de entrada y templates
- `application/`: orquestacion de servicios y casos de uso
- `domain/`: extraccion de features, scoring, clasificacion y explicaciones
- `infrastructure/`: configuracion, persistencia, logging, fetch de contenido estatico y reportes
- `config/`: catalogo de marcas y reglas/pesos

Buenas practicas presentes:

- tipado explicito en los modulos principales
- clases y funciones pequenas por responsabilidad
- configuracion externa en JSON
- pruebas automatizadas integradas al repositorio
- pipeline CI con controles de calidad

### 3.2 Coherencia con el diseno aprobado

La implementacion mantiene coherencia con la arquitectura modular definida en la etapa de diseno. Se identifican y utilizan los siguientes componentes principales:

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

### 3.3 Control de versiones

El proyecto usa Git como mecanismo de trazabilidad de cambios. El historial reciente evidencia evolucion del sistema, ajustes de configuracion y mejoras de calidad.

Ultimos commits observados:

```text
1b766aa (HEAD -> empresas, origin/empresas) Agregar nuevas empresas al catalogo
70c14af (origin/main, origin/HEAD, main) Merge pull request #3 from CarlosKC26/linters
f78bf60 (origin/linters, linters) Se eliminan archivos externos al repo
2c2b647 Merge pull request #2 from CarlosKC26/linters
2c7c1e0 Se eliminaron archivos .json que no se usan y se amplió el pipeline ci para usar linters y sast
13b6195 Merge pull request #1 from CarlosKC26/inicial
b5532e0 (origin/inicial) Actualización de readme
431205a Corrección docker-compose
e6da0bf se dejan de seguir archivos agragados al .gitignore
a77e60f se añade el monitoreo batch a la ui
```

### 3.4 Gestion de dependencias y configuraciones

Dependencias principales del proyecto:

- `Flask==3.1.0`
- `psycopg[binary]==3.2.6`
- `pytest==8.3.5`
- `pytest-cov==6.0.0`

Controles de configuracion presentes:

- `config/empresas.json`: catalogo de marcas, dominios oficiales y palabras clave
- `config/pesos.json`: reglas, umbrales, timeouts y pesos del scoring
- `.env.example`: variables de entorno para despliegue y persistencia

Esto permite modificar el comportamiento del sistema sin alterar el core analitico.

### 3.5 Uso responsable de IA generativa

El uso de IA generativa en este proyecto se limita a apoyo asistencial durante tareas de implementacion y documentacion. La IA no participa en el funcionamiento del motor de deteccion.

Declaraciones clave:

- el scoring no utiliza IA ni aprendizaje automatico
- la clasificacion de riesgo es deterministica y basada en reglas
- las decisiones tecnicas y validaciones finales fueron revisadas manualmente
- cualquier apoyo de IA generativa fue supervisado y verificado antes de integrarse

## 4. Pruebas y aseguramiento de calidad

### 4.1 Estrategia de pruebas

La estrategia formal se documenta en `tests/TEST_STRATEGY.md` y cubre:

- objetivo y alcance
- ambiente de pruebas
- pruebas unitarias, de integracion y funcionales
- criterios de entrada y salida
- trazabilidad entre requisitos y pruebas
- cobertura objetivo
- gestion de defectos y riesgos residuales

### 4.2 Conjunto de pruebas implementadas

La suite automatizada incluye:

- `test_input_handler.py`
- `test_feature_extractor.py`
- `test_scoring_engine.py`
- `test_risk_classifier.py`
- `test_repository_factory.py`
- `test_result_repository_postgresql.py`
- `test_analysis_pipeline.py`
- `test_web_controller.py`

Estas pruebas cubren:

- validacion y normalizacion de entradas
- extraccion de señales estructurales
- activacion de reglas de negocio
- scoring y clasificacion
- persistencia
- flujo end-to-end
- procesamiento batch
- interfaz web

### 4.3 Evidencia de ejecucion de pruebas

Ejecucion local mas reciente:

```text
collected 23 items
23 passed
coverage total: 81%
```

Resumen de ejecucion:

```text
tests\test_analysis_pipeline.py ...... 
tests\test_feature_extractor.py ...
tests\test_input_handler.py ....
tests\test_repository_factory.py ..
tests\test_result_repository_postgresql.py .
tests\test_risk_classifier.py ..
tests\test_scoring_engine.py ..
tests\test_web_controller.py ...
```

Cobertura total observada:

```text
TOTAL 1341 255 81%
```

### 4.4 Validacion de requisitos y casos de negocio

Casos de negocio cubiertos por la suite:

- URL legitima de marca oficial
- typosquatting con keywords y TLD sospechoso
- phishing con ingenieria social
- dominio anormalmente largo
- timeout o error HTTP con resultado parcial
- procesamiento batch con alertas y reportes
- uso del sistema desde la interfaz web

La trazabilidad detallada entre requisitos y pruebas se encuentra en `tests/TEST_STRATEGY.md`.

### 4.5 Aseguramiento adicional de calidad

Ademas de las pruebas automatizadas, se integraron controles de calidad en CI:

- linting con `ruff`
- analisis SAST con `bandit`
- ejecucion automatica de `pytest`

Para reproducir localmente esos controles se recomienda ejecutar:

```powershell
python -m ruff check .
python -m bandit -r application domain infrastructure presentation main.py web_main.py core.py
python -m pytest --cov=. --cov-report=term-missing
```

Resultado local mas reciente de lint:

```text
All checks passed!
```

Resultado local mas reciente de SAST:

```text
No issues identified.
Total issues (by severity): 0
```

## 5. Defectos identificados y gestion

Durante la construccion se identificaron y corrigieron defectos o mejoras relevantes:

| Defecto o ajuste | Impacto | Correccion aplicada | Evidencia |
| --- | --- | --- | --- |
| Serializacion JSONB en PostgreSQL | Riesgo de persistencia incorrecta | Ajuste del repositorio PostgreSQL | pruebas de repositorio |
| Flujo Docker mezclando CLI y web | Complejidad de despliegue y uso | Separacion entre contenedor `web` y contenedor `app` | `docker-compose.yml`, README |
| Falta de batch en UI | Cobertura funcional incompleta | Se agrego soporte batch en interfaz web | `test_web_controller.py` |
| CI basico sin controles estaticos | Menor aseguramiento de calidad | Se integraron `ruff` y `bandit` al workflow | `.github/workflows/ci.yml` |

## 6. Evidencias del repositorio

El repositorio cumple con los entregables esperados:

- codigo fuente accesible y versionado
- instrucciones de compilacion y ejecucion en `README.md`
- historial de commits trazable con Git
- conjunto de pruebas implementadas en `tests/`
- documento de estrategia de pruebas en `tests/TEST_STRATEGY.md`
- configuracion externa en `config/`
- pipeline CI en `.github/workflows/ci.yml`

## 7. Conclusion

La Entrega 3 evidencia que el sistema fue construido con una arquitectura consistente, configuracion externa, pruebas automatizadas y controles de calidad adicionales. El proyecto cumple con los criterios de construccion, codificacion, pruebas y aseguramiento de calidad solicitados para la entrega, manteniendo un comportamiento deterministico, explicable y alineado con el contexto del problema.

## 8. Como regenerar la evidencia

Si se requiere actualizar este informe antes de entregar, se pueden ejecutar los siguientes comandos desde la raiz del proyecto:

### Historial de commits

```powershell
git log --oneline --decorate -n 10
```

### Pruebas y cobertura

```powershell
python -m pytest
python -m pytest --cov=. --cov-report=term-missing
```

### Lint

```powershell
python -m ruff check .
```

### SAST

```powershell
python -m bandit -r application domain infrastructure presentation main.py web_main.py core.py
```

### Ejecucion manual de ejemplo

```powershell
python main.py banc0lombia-verificacion.xyz
```

### Ejecucion batch de ejemplo

```powershell
python main.py --batch listas/2026-01-31.txt --output-dir output
```
