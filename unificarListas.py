import os
import zipfile
from datetime import datetime

def descomprimir_zips(carpeta_listas):
    inicio = datetime.now()
    print(f"[{inicio.strftime('%H:%M:%S')}] Iniciando descompresión de archivos ZIP...")

    # Buscar todos los zip primero para poder calcular porcentaje
    zips_encontrados = []
    for carpeta_raiz, _, archivos in os.walk(carpeta_listas):
        for archivo in archivos:
            if archivo.lower().endswith(".zip"):
                zips_encontrados.append(os.path.join(carpeta_raiz, archivo))

    total_zips = len(zips_encontrados)
    if total_zips == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No se encontraron archivos ZIP.")
        return

    for i, ruta_zip in enumerate(zips_encontrados, start=1):
        try:
            # Crear carpeta con el nombre del ZIP (sin extensión)
            nombre_carpeta = os.path.splitext(os.path.basename(ruta_zip))[0]
            carpeta_destino = os.path.join(os.path.dirname(ruta_zip), nombre_carpeta)
            os.makedirs(carpeta_destino, exist_ok=True)

            # Descomprimir en la carpeta creada
            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                zip_ref.extractall(carpeta_destino)

            porcentaje = (i / total_zips) * 100
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ({porcentaje:.2f}%) Descomprimido en: {carpeta_destino}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] No se pudo descomprimir {ruta_zip}: {e}")

    fin = datetime.now()
    print(f"[{fin.strftime('%H:%M:%S')}] Descompresión completada. Tiempo total: {fin - inicio}")


def unificar_txt(carpeta_listas, archivo_salida):
    inicio = datetime.now()
    print(f"[{inicio.strftime('%H:%M:%S')}] Iniciando unificación de archivos TXT...")

    # Buscar todos los txt para el cálculo de porcentaje
    txt_encontrados = []
    for carpeta_raiz, _, archivos in os.walk(carpeta_listas):
        for archivo in archivos:
            if archivo.lower().endswith(".txt"):
                txt_encontrados.append(os.path.join(carpeta_raiz, archivo))

    total_txt = len(txt_encontrados)
    if total_txt == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No se encontraron archivos TXT.")
        return

    lineas_unicas = set()

    for i, ruta_txt in enumerate(txt_encontrados, start=1):
        try:
            with open(ruta_txt, "r", encoding="utf-8", errors="ignore") as f:
                for linea in f:
                    linea_limpia = linea.strip().lower()
                    if linea_limpia:
                        lineas_unicas.add(linea_limpia)
            porcentaje = (i / total_txt) * 100
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ({porcentaje:.2f}%) Procesado: {ruta_txt}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] No se pudo leer {ruta_txt}: {e}")

    # Ordenar y escribir el archivo unificado
    with open(archivo_salida, "w", encoding="utf-8") as f:
        for linea in sorted(lineas_unicas):
            f.write(linea + "\n")

    fin = datetime.now()
    print(f"[{fin.strftime('%H:%M:%S')}] Archivo unificado generado: {archivo_salida}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Total de líneas únicas: {len(lineas_unicas)}")
    print(f"[{fin.strftime('%H:%M:%S')}] Unificación completada. Tiempo total: {fin - inicio}")