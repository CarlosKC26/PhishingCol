# Estrategia de Pruebas

## 1. Objetivo

Definir la estrategia de aseguramiento de calidad de la Entrega 3 para demostrar que la implementacion:

- conserva la arquitectura aprobada en la Entrega 2
- mantiene un comportamiento deterministico y explicable
- valida requisitos funcionales, reglas de negocio y restricciones tecnicas
- evidencia pruebas unitarias, de integracion y funcionales

## 2. Alcance

Esta estrategia cubre el flujo principal del sistema de deteccion de phishing basado en URLs y dominios:

- validacion y normalizacion de entrada
- extraccion de features de dominio y contenido estatico
- scoring por reglas configurables
- clasificacion de riesgo
- construccion de explicaciones
- persistencia de resultados
- monitoreo batch y generacion de alertas/reportes
- interfaz web para consulta manual y procesamiento batch

Fuera de alcance:

- renderizado con JavaScript
- analisis de logos, OCR o imagenes
- analisis de archivos adjuntos distintos de `.txt` y `.zip`

## 3. Ambiente de Pruebas

- Lenguaje: Python 3.11
- Framework principal de pruebas: `pytest`
- Cobertura: `pytest-cov`
- Configuracion base: `pytest.ini`
- CI: workflow en `.github/workflows/ci.yml`

La ejecucion local y en CI utiliza el mismo comando base:

```bash
python -m pytest --cov=. --cov-report=term-missing
```

## 4. Enfoque de Calidad

La calidad del proyecto se asegura mediante varias capas complementarias:

- pruebas automatizadas para el core de negocio
- validacion de integracion del pipeline end-to-end
- pruebas funcionales de la UI web
- cobertura automatizada
- linting con `ruff`
- analisis SAST con `bandit`

## 5. Niveles de Prueba

### 5.1 Pruebas unitarias

Validan componentes individuales y reglas aisladas.

Cobertura principal:

- `test_input_handler.py`: validacion y normalizacion de entradas
- `test_feature_extractor.py`: extraccion de señales estructurales
- `test_scoring_engine.py`: activacion y desglose de reglas
- `test_risk_classifier.py`: clasificacion por umbrales
- `test_repository_factory.py`: seleccion del backend de persistencia
- `test_result_repository_postgresql.py`: serializacion de datos para PostgreSQL

### 5.2 Pruebas de integracion

Validan el flujo completo entre modulos.

Cobertura principal:

- `test_analysis_pipeline.py`: flujo `entrada -> analisis -> scoring -> clasificacion -> explicacion -> persistencia`
- validacion del batch con reportes y alertas
- manejo de timeout o errores parciales durante analisis de contenido

### 5.3 Pruebas funcionales/web

Validan el comportamiento observable desde la interfaz.

Cobertura principal:

- `test_web_controller.py`: carga de la pagina principal
- analisis manual desde formulario web
- procesamiento batch desde UI

## 6. Criterios de Entrada y Salida

### 6.1 Criterios de entrada

Antes de ejecutar la suite se espera:

- dependencias instaladas desde `requirements.txt`
- archivos de configuracion presentes en `config/`
- entorno local o CI con Python 3.11

### 6.2 Criterios de salida

La validacion se considera satisfactoria cuando:

- la suite automatizada finaliza sin fallos
- la cobertura total supera el minimo objetivo del 70%
- los casos criticos de negocio quedan evidenciados
- no existen hallazgos bloqueantes en lint o SAST

## 7. Casos de Negocio Cubiertos

Los casos minimos cubiertos por la suite son:

- URL legitima de marca oficial
- typosquatting con keywords y TLD sospechoso
- phishing con keywords de ingenieria social
- dominio anormalmente largo
- error HTTP o timeout simulado con resultado parcial
- batch con multiples dominios, reportes y alertas
- consulta desde interfaz web

## 8. Datos y Oraculos de Prueba

Los datos de prueba fueron seleccionados para ejercer rutas legitimas, sospechosas y de error:

- dominios oficiales para validar falsos positivos bajos
- dominios con typosquatting para validar reglas de similitud
- keywords de marca y de ingenieria social para validar scoring
- timeouts y snapshots simulados para validar resiliencia
- archivos batch para validar consolidacion y procesamiento masivo

El oraculo principal de validacion es deterministico y se basa en:

- score esperado
- reglas activadas
- nivel de riesgo esperado
- evidencia y limitaciones reportadas

## 9. Trazabilidad entre Requisitos y Pruebas

### 9.1 Requisitos funcionales y no funcionales

- RN-01 / RNF1: rechazo de entradas invalidas.
  Evidencia: `test_input_handler.py`
- RN-04 a RN-10: reglas de negocio estructurales y de scoring.
  Evidencia: `test_feature_extractor.py`, `test_scoring_engine.py`, `test_analysis_pipeline.py`
- RN-11 / RNF11 / RNF12: analisis de contenido opcional y tolerancia a fallos.
  Evidencia: `test_analysis_pipeline.py`
- RN-12 / RN-13 / RNF28: scoring y clasificacion deterministica.
  Evidencia: `test_scoring_engine.py`, `test_risk_classifier.py`
- RN-16 / RN-17 / RNF19: explicacion con score, evidencia, reglas y limitaciones.
  Evidencia: `test_analysis_pipeline.py`
- RN-18: alertas de alto riesgo en batch.
  Evidencia: `test_analysis_pipeline.py`
- Persistencia mock y PostgreSQL.
  Evidencia: `test_repository_factory.py`, `test_result_repository_postgresql.py`
- Interfaz web para consulta manual y batch.
  Evidencia: `test_web_controller.py`

## 10. Cobertura Objetivo

El proyecto define una cobertura minima objetivo de 70% o superior.

En la verificacion local mas reciente usada para esta entrega:

- pruebas ejecutadas: 23
- resultado: 23 exitosas
- cobertura total: 81%

## 11. Evidencia de Ejecucion

Para la entrega se debe adjuntar o citar:

- salida de `python -m pytest`
- salida de `python -m pytest --cov=. --cov-report=term-missing`
- capturas o fragmentos JSON de ejecuciones manuales y batch
- evidencia del workflow de CI ejecutando lint, SAST y pruebas

## 12. Gestion de Defectos

Los defectos encontrados durante la construccion se gestionan con este criterio:

1. Identificar el defecto y su impacto.
2. Corregir en una rama de trabajo con commit trazable.
3. Validar mediante pruebas automatizadas o evidencia manual controlada.
4. Documentar la correccion en el informe final o en el historial del repositorio.

Ejemplos de defectos ya tratados en el proyecto:

- ajuste de serializacion JSONB para persistencia en PostgreSQL
- separacion de contenedores `web` y `app` para el flujo Docker
- ampliacion de la UI para soportar procesamiento batch
- incorporacion de lint y SAST en el pipeline CI

## 13. Riesgos Residuales

Aunque la cobertura es adecuada para la Entrega 3, permanecen riesgos razonables:

- dependencias de red al activar analisis de contenido real
- cobertura parcial de componentes de infraestructura no simulados
- ausencia de analisis dinamico de contenido con JavaScript

Estos riesgos son aceptables para el alcance definido del proyecto y se comunican explicitamente en la documentacion.
