#!/usr/bin/env python3
"""
Script para limpiar archivos temporales del transcriptor de YouTube.
Útil cuando se quiere liberar espacio después de completar transcripciones.
"""

import os
import sys
import glob
import argparse
import json
from pathlib import Path

def limpiar_titulo(titulo):
    """Limpia el título para usarlo como nombre de archivo."""
    caracteres_invalidos = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    titulo_limpio = titulo
    for char in caracteres_invalidos:
        titulo_limpio = titulo_limpio.replace(char, '')
    
    if len(titulo_limpio) > 100:
        titulo_limpio = titulo_limpio[:100]
    
    return titulo_limpio.strip()

def encontrar_archivos_temporales(directorio):
    """Encuentra todos los archivos temporales en el directorio."""
    archivos_temporales = []
    
    # Buscar archivos .wav (archivos de audio)
    archivos_wav = glob.glob(os.path.join(directorio, "*.wav"))
    archivos_temporales.extend(archivos_wav)
    
    # Buscar directorios temp_audio
    directorios_temp = glob.glob(os.path.join(directorio, "temp_audio"))
    archivos_temporales.extend(directorios_temp)
    
    # Buscar archivos .part (descargas incompletas)
    archivos_part = glob.glob(os.path.join(directorio, "*.part"))
    archivos_temporales.extend(archivos_part)
    
    # Buscar archivos de estado de procesamiento
    archivos_estado = glob.glob(os.path.join(directorio, "estado_procesamiento_*.json"))
    archivos_temporales.extend(archivos_estado)
    
    return archivos_temporales

def limpiar_archivos_completados(directorio, titulo_video=None):
    """Limpia archivos temporales solo de videos completados."""
    archivos_eliminados = []
    archivos_conservados = []
    
    # Buscar archivos de estado
    archivos_estado = glob.glob(os.path.join(directorio, "estado_procesamiento_*.json"))
    
    for archivo_estado in archivos_estado:
        try:
            with open(archivo_estado, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            
            # Verificar si el proceso está completado
            if estado.get('etapa') == 'completado':
                titulo = estado.get('archivo_audio', '')
                if titulo:
                    # Extraer título del archivo de audio
                    titulo_limpio = os.path.splitext(os.path.basename(titulo))[0]
                    
                    # Si se especifica un título, solo limpiar ese
                    if titulo_video and titulo_limpio != limpiar_titulo(titulo_video):
                        continue
                    
                    # Buscar archivos relacionados
                    archivos_relacionados = []
                    
                    # Archivo de audio
                    if os.path.exists(titulo):
                        archivos_relacionados.append(titulo)
                    
                    # Directorio temp_audio
                    temp_dir = os.path.join(os.path.dirname(titulo), "temp_audio")
                    if os.path.exists(temp_dir):
                        archivos_relacionados.append(temp_dir)
                    
                    # Archivos .part
                    archivos_part = glob.glob(os.path.join(directorio, f"{titulo_limpio}*.part"))
                    archivos_relacionados.extend(archivos_part)
                    
                    # Eliminar archivos
                    for archivo in archivos_relacionados:
                        try:
                            if os.path.isfile(archivo):
                                os.remove(archivo)
                                archivos_eliminados.append(archivo)
                                print(f"✓ Eliminado: {os.path.basename(archivo)}")
                            elif os.path.isdir(archivo):
                                import shutil
                                shutil.rmtree(archivo, ignore_errors=True)
                                archivos_eliminados.append(archivo)
                                print(f"✓ Eliminado: {os.path.basename(archivo)}/")
                        except Exception as e:
                            print(f"⚠️ Error al eliminar {archivo}: {e}")
                    
                    # Eliminar archivo de estado
                    try:
                        os.remove(archivo_estado)
                        archivos_eliminados.append(archivo_estado)
                        print(f"✓ Eliminado: {os.path.basename(archivo_estado)}")
                    except Exception as e:
                        print(f"⚠️ Error al eliminar {archivo_estado}: {e}")
                        
            else:
                # Proceso no completado, conservar archivos
                archivos_conservados.append(archivo_estado)
                
        except Exception as e:
            print(f"⚠️ Error al procesar {archivo_estado}: {e}")
    
    return archivos_eliminados, archivos_conservados

def mostrar_estado_archivos(directorio):
    """Muestra el estado de todos los archivos temporales."""
    print(f"\n📁 Analizando directorio: {directorio}")
    print("=" * 60)
    
    # Buscar archivos de estado
    archivos_estado = glob.glob(os.path.join(directorio, "estado_procesamiento_*.json"))
    
    if not archivos_estado:
        print("No se encontraron archivos de estado de procesamiento.")
        return
    
    print(f"Encontrados {len(archivos_estado)} archivos de estado:")
    print()
    
    for archivo_estado in archivos_estado:
        try:
            with open(archivo_estado, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            
            titulo = estado.get('archivo_audio', '')
            titulo_limpio = os.path.splitext(os.path.basename(titulo))[0] if titulo else 'Desconocido'
            etapa = estado.get('etapa', 'Desconocida')
            
            if etapa == 'completado':
                print(f"✅ {titulo_limpio} - COMPLETADO")
            else:
                segmento_actual = estado.get('segmento_actual', 0)
                total_segmentos = estado.get('total_segmentos', 0)
                print(f"🔄 {titulo_limpio} - EN PROGRESO (segmento {segmento_actual}/{total_segmentos})")
                
        except Exception as e:
            print(f"❌ Error al leer {archivo_estado}: {e}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Limpia archivos temporales del transcriptor de YouTube.",
        epilog="Ejemplo: python limpiar_archivos_temporales.py --directorio ./clase6 --limpiar"
    )
    
    parser.add_argument(
        "-d", "--directorio",
        default=".",
        help="Directorio donde buscar archivos temporales (default: directorio actual)"
    )
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Eliminar archivos temporales de procesos completados"
    )
    parser.add_argument(
        "--titulo",
        help="Limpiar solo archivos de un video específico"
    )
    parser.add_argument(
        "--mostrar",
        action="store_true",
        help="Mostrar estado de archivos sin eliminar"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directorio):
        print(f"❌ Error: El directorio {args.directorio} no existe")
        sys.exit(1)
    
    if args.mostrar:
        mostrar_estado_archivos(args.directorio)
        return
    
    if args.limpiar:
        print("🧹 LIMPIANDO ARCHIVOS TEMPORALES")
        print("=" * 60)
        
        archivos_eliminados, archivos_conservados = limpiar_archivos_completados(
            args.directorio, args.titulo
        )
        
        print(f"\n📊 RESUMEN:")
        print(f"Archivos eliminados: {len(archivos_eliminados)}")
        print(f"Archivos conservados: {len(archivos_conservados)}")
        
        if archivos_conservados:
            print(f"\n⚠️ Archivos conservados (procesos no completados):")
            for archivo in archivos_conservados:
                print(f"  - {os.path.basename(archivo)}")
        
        if archivos_eliminados:
            print(f"\n✅ Limpieza completada exitosamente")
        else:
            print(f"\nℹ️ No se encontraron archivos para limpiar")
    
    else:
        print("ℹ️ Usa --mostrar para ver el estado de archivos")
        print("ℹ️ Usa --limpiar para eliminar archivos temporales")
        print("ℹ️ Usa --titulo 'TITULO' para limpiar solo un video específico")

if __name__ == "__main__":
    main()
