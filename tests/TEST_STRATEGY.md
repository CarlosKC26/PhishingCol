# Estrategia de Pruebas

## Objetivo

Validar que la Entrega 3 implementa el diseño aprobado, mantiene el análisis determinístico y evidencia cumplimiento de reglas, restricciones y casos de negocio.

## Niveles cubiertos

- Unitarias:
  validación de entrada, extracción de features, reglas individuales, scoring y clasificación.
- Integración:
  flujo completo `entrada -> análisis -> scoring -> clasificación -> explicación -> persistencia`.
- Integración batch:
  consolidación de listas, ejecución masiva, generación de reportes y alertas.

## Casos de negocio cubiertos

- URL legítima de marca oficial.
- Typosquatting con keywords y TLD sospechoso.
- Phishing con keywords de ingeniería social.
- Dominio anómalamente largo.
- Error HTTP/timeout simulado con resultado parcial.

## Evidencia de requisitos

- RN-01/RNF1: rechazo de entradas inválidas.
- RN-04 a RN-10: reglas activadas y validadas con pruebas positivas.
- RN-11/RNF11/RNF12: análisis de contenido opcional, timeout simulado y continuidad ante fallos.
- RN-12/RN-13/RNF28: scoring y clasificación determinísticos.
- RN-16/RN-17/RNF19: explicación con score, reglas, evidencia y limitaciones.
- RN-18: generación de alertas para riesgo alto en batch.

## Criterio de cobertura

La suite está diseñada para superar el 70% de cobertura mediante `pytest --cov`.
