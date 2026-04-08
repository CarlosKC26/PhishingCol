import json
import re
from rapidfuzz import fuzz
import sys
from datetime import datetime

# ------------------ Carga de Configuraciones ------------------

def cargar_configuracion_empresas(path="empresas.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_pesos(path="pesos.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------------ Funciones de Análisis ------------------

def calcular_similitud_fuzzy(dominio, urls_oficiales, pesos):
    max_score = 0
    dominio_normalizado = normalizar_leet(dominio)

    for oficial in urls_oficiales:
        oficial_normalizado = normalizar_leet(oficial)

        score = fuzz.ratio(dominio_normalizado, oficial_normalizado)
        if score > max_score:
            max_score = score

    return (max_score / 100) * pesos["peso_maximo"]

def normalizar_leet(texto):
    texto = texto.lower()
    reemplazos = {
        '1': 'i', '¡': 'i', '!': 'i', '|': 'i', 'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ı': 'i',
        '0': 'o', 'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ø': 'o',
        '@': 'a', '4': 'a', 'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ã': 'a',
        '3': 'e', 'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
        '7': 't', '+': 't',
        '$': 's', '5': 's', '§': 's',
        '2': 'z',
        '8': 'b',
        '9': 'g',
        '6': 'g',
        'ß': 'b',
        '?': 'y',
        'ñ': 'n',
        'ç': 'c',
        'æ': 'ae',
        'œ': 'oe',
        'Þ': 'p',
        'µ': 'u',
        '∂': 'd',
        '∑': 'e',
        'ƒ': 'f',
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.lower()

def buscar_palabras(dominio, lista_palabras, peso_unitario, umbral=75):
    score = 0
    count = 0
    dominio_normalizado = normalizar_leet(dominio)

    for palabra in lista_palabras:
        palabra_normalizada = normalizar_leet(palabra)
        # Fuzzy match: compara la palabra con el dominio
        similitud = fuzz.partial_ratio(palabra_normalizada, dominio_normalizado)
        if similitud >= umbral:
            score += similitud/100 * peso_unitario * (0.9**count)
            count += 1
            if count >= 5:  # Limita a 5 coincidencias
                return score
    return score

def evaluar_regex(dominio, expresion, peso):
    try:
        if expresion and re.search(expresion, dominio):
            return peso
    except re.error:
        # Si la expresión regular es inválida, ignora y retorna 0
        return 0
    return 0

def print_phase_progress_bar(phase, iteration, total, length=30):
    percent = 100 * (iteration / float(total))
    filled_length = int(length * iteration // total)
    bar = '#' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{phase}: |{bar}| {percent:.1f}% ({iteration}/{total})')
    sys.stdout.flush()
    if iteration == total:
        print()

# ------------------ Función principal ------------------

def analizar_dominio(dominio, config_empresas, pesos):
    resultados = []
    total_empresas = len(config_empresas)
    empresa_count = 0

    dominio_normalizado = normalizar_leet(dominio)

    fase_inicio = datetime.now()
    print(f"\n[ANÁLISIS] Dominio: {dominio}")
    print(f"Inicio de análisis: {fase_inicio.strftime('%Y-%m-%d %H:%M:%S')}")

    for empresa_id, datos in config_empresas.items():
        empresa_count += 1
        print_phase_progress_bar("Empresas", empresa_count, total_empresas)

        score_total = 0
        score_fuzzy = score_regex = score_claves = score_secundarias = score_relacionadas = 0

        # --- Fase 1: Fuzzy ---
        fuzzy_inicio = datetime.now()
        print(f"\n  [Fase 1] Fuzzy - {empresa_id} - Inicio: {fuzzy_inicio.strftime('%H:%M:%S')}")
        score_fuzzy = calcular_similitud_fuzzy(
            dominio_normalizado,
            [normalizar_leet(url) for url in datos.get("urls_oficiales", [])],
            pesos.get("fuzzy_score", {})
        )
        fuzzy_fin = datetime.now()
        print(f"  [Fase 1] Fuzzy - Fin: {fuzzy_fin.strftime('%H:%M:%S')} - Duración: {fuzzy_fin - fuzzy_inicio}")

        if score_fuzzy < pesos["total"]["minimo_fuzzy"]:
            continue

        score_total += score_fuzzy
        if score_total > pesos["total"]["techo"]:
            resultados.append(_crear_resultado(empresa_id, dominio, score_total, score_fuzzy, score_regex, score_claves, score_secundarias, score_relacionadas))
            continue

        # --- Fase 2: Regex ---
        regex_inicio = datetime.now()
        print(f"  [Fase 2] Regex - Inicio: {regex_inicio.strftime('%H:%M:%S')}")
        score_regex = evaluar_regex(dominio_normalizado, datos.get("expresion_regular"), pesos["regex"]["peso_unitario"])
        regex_fin = datetime.now()
        print(f"  [Fase 2] Regex - Fin: {regex_fin.strftime('%H:%M:%S')} - Duración: {regex_fin - regex_inicio}")

        score_total += score_fuzzy * (score_regex / 100)
        if score_total > pesos["total"]["techo"]:
            resultados.append(_crear_resultado(empresa_id, dominio, score_total, score_fuzzy, score_regex, score_claves, score_secundarias, score_relacionadas))
            continue

        # --- Fase 3: Palabras clave ---
        clave_inicio = datetime.now()
        print(f"  [Fase 3] Palabras clave - Inicio: {clave_inicio.strftime('%H:%M:%S')}")
        score_claves = buscar_palabras(dominio_normalizado, datos.get("palabras_clave", []), pesos["palabras"]["clave"]["peso_unitario"])
        clave_fin = datetime.now()
        print(f"  [Fase 3] Palabras clave - Fin: {clave_fin.strftime('%H:%M:%S')} - Duración: {clave_fin - clave_inicio}")

        score_total += score_fuzzy * (score_claves / 100)
        if score_total > pesos["total"]["techo"]:
            resultados.append(_crear_resultado(empresa_id, dominio, score_total, score_fuzzy, score_regex, score_claves, score_secundarias, score_relacionadas))
            continue

        # --- Fase 4: Palabras secundarias ---
        secundaria_inicio = datetime.now()
        print(f"  [Fase 4] Palabras secundarias - Inicio: {secundaria_inicio.strftime('%H:%M:%S')}")
        score_secundarias = buscar_palabras(dominio_normalizado, datos.get("palabras_secundarias", []), pesos["palabras"]["secundaria"]["peso_unitario"], umbral=77)
        secundaria_fin = datetime.now()
        print(f"  [Fase 4] Palabras secundarias - Fin: {secundaria_fin.strftime('%H:%M:%S')} - Duración: {secundaria_fin - secundaria_inicio}")

        score_total += score_fuzzy * (score_secundarias / 100)
        if score_total > pesos["total"]["techo"]:
            resultados.append(_crear_resultado(empresa_id, dominio, score_total, score_fuzzy, score_regex, score_claves, score_secundarias, score_relacionadas))
            continue

        # --- Fase 5: Palabras relacionadas ---
        relacionada_inicio = datetime.now()
        print(f"  [Fase 5] Palabras relacionadas - Inicio: {relacionada_inicio.strftime('%H:%M:%S')}")
        score_relacionadas = buscar_palabras(dominio_normalizado, datos.get("palabras_relacionadas", []), pesos["palabras"]["relacionada"]["peso_unitario"], umbral=80)
        relacionada_fin = datetime.now()
        print(f"  [Fase 5] Palabras relacionadas - Fin: {relacionada_fin.strftime('%H:%M:%S')} - Duración: {relacionada_fin - relacionada_inicio}")

        score_total += score_fuzzy * (score_relacionadas / 100)

        if score_total > pesos["total"]["piso"]:
            resultados.append(_crear_resultado(empresa_id, dominio, score_total, score_fuzzy, score_regex, score_claves, score_secundarias, score_relacionadas))

    fase_fin = datetime.now()
    print(f"Fin de análisis: {fase_fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duración total del análisis para el dominio: {fase_fin - fase_inicio}\n")

    return resultados


def _crear_resultado(empresa_id, dominio, total, fuzzy, regex, claves, secundarias, relacionadas):
    return {
        "empresa": empresa_id,
        "dominio": dominio,
        "score_total": total,
        "score_fuzzy": fuzzy,
        "score_regex": regex,
        "score_claves": claves,
        "score_secundarias": secundarias,
        "score_relacionadas": relacionadas
    }