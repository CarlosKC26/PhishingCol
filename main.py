from core import cargar_configuracion_empresas, cargar_pesos, analizar_dominio
import pandas as pd # type: ignore
from concurrent.futures import ProcessPoolExecutor
import sys
from datetime import datetime
import os
from unificarListas import descomprimir_zips, unificar_txt

def leer_dominios(path_txt):
    try:
        with open(path_txt, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo: {path_txt}")
    except PermissionError:
        print(f"[ERROR] Permiso denegado al intentar leer el archivo: {path_txt}")
    except Exception as e:
        print(f"[ERROR] Ocurrió un problema al leer el archivo '{path_txt}': {e}")
    return []


def calcular_porcentaje(score_total, techo=280):
    try:
        if score_total >= techo:
            return 100.0
        else:
            return round(((score_total / techo) * 60) + 40, 2)
    except ZeroDivisionError:
        print("[ERROR] El valor de 'techo' no puede ser cero.")
        return 0.0
    except Exception as e:
        print(f"[ERROR] No se pudo calcular el porcentaje: {e}")
        return 0.0


def print_progress_bar(iteration, total, length=40):
    try:
        percent = 100 * (iteration / float(total))
        filled_length = int(length * iteration // total)
        bar = '=' * filled_length + '-' * (length - filled_length)
        sys.stdout.write(f'\rProgreso: |{bar}| {percent:.1f}% ({iteration}/{total})')
        sys.stdout.flush()
        if iteration == total:
            print()
    except Exception as e:
        print(f"[ERROR] No se pudo actualizar la barra de progreso: {e}")


def ejecutar_analisis(path_txt="dominios_sospechosos.txt", salida_excel="resultados_fraude.xlsx"):
    try:
        inicio = datetime.now()
        print(f"Inicio de ejecución: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")

        config_empresas = cargar_configuracion_empresas()
        pesos = cargar_pesos()
        dominios = leer_dominios(path_txt)

        if not dominios:
            print("[ADVERTENCIA] No se encontraron dominios para analizar.")
            return

        resultados_por_empresa = {empresa: [] for empresa in config_empresas.keys()}
        total = len(dominios)
        processed = 0

        for dominio in dominios:
            try:
                resultados = analizar_dominio(dominio, config_empresas, pesos)
                processed += 1
                print_progress_bar(processed, total)

                for r in resultados:
                    if r["score_total"] > pesos["total"]["piso"]:
                        r["porcentaje"] = calcular_porcentaje(r["score_total"])
                        resultados_por_empresa[r["empresa"]].append(r)
            except Exception as e:
                print(f"[ERROR] No se pudo procesar el dominio '{dominio}': {e}")

        try:
            with pd.ExcelWriter(salida_excel, engine="openpyxl") as writer:
                for empresa, resultados in resultados_por_empresa.items():
                    if resultados:
                        for r in resultados:
                            r["porcentaje"] = round(r["porcentaje"], 2)
                            r["score_total"] = round(r["score_total"], 2)
                            r["score_fuzzy"] = round(r["score_fuzzy"], 2)
                            r["score_claves"] = round(r["score_claves"], 2)
                            r["score_secundarias"] = round(r["score_secundarias"], 2)
                            r["score_relacionadas"] = round(r["score_relacionadas"], 2)
                            r["score_regex"] = round(r["score_regex"], 2)
                        df = pd.DataFrame(resultados)
                        df = df[[
                            "dominio",
                            "porcentaje",
                            "score_total",
                            "score_fuzzy",
                            "score_claves",
                            "score_secundarias",
                            "score_relacionadas",
                            "score_regex"
                        ]]
                        df = df.sort_values(by="porcentaje", ascending=False)
                        df.to_excel(writer, sheet_name=empresa, index=False)
        except PermissionError:
            print(f"[ERROR] No se pudo escribir el archivo Excel. Verifique permisos: {salida_excel}")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar el archivo Excel '{salida_excel}': {e}")

        fin = datetime.now()
        print(f"\nFin de ejecución: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tiempo total transcurrido: {str(fin - inicio)}")

    except Exception as e:
        print(f"[ERROR] Error inesperado durante la ejecución del análisis: {e}")


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta_salida = os.path.join(os.getcwd(), "dominiosSospechosos")
    os.makedirs(carpeta_salida, exist_ok=True)
    
    # Nombres de archivos con timestamp
    nombreListaDominiosUnificados = f"dominios_sospechosos_{timestamp}.txt"
    nombreExcel = f"excelDominiosSospechosos_{timestamp}.xlsx"
    
    # Rutas completas dentro de la carpeta de salida
    archivo_salida = os.path.join(carpeta_salida, nombreListaDominiosUnificados)
    ruta_excel = os.path.join(carpeta_salida, nombreExcel)
    
    sys.stdout.reconfigure(encoding='utf-8')
    carpeta_listas = os.path.join(os.getcwd(), "listas")
    
    descomprimir_zips(carpeta_listas)
    unificar_txt(carpeta_listas, archivo_salida)
    ejecutar_analisis(path_txt=archivo_salida, salida_excel=ruta_excel)