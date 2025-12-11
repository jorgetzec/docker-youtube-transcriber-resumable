import os
import argparse
import sys
import logging
import yt_dlp
import speech_recognition as sr
from moviepy.editor import AudioFileClip
from pydub import AudioSegment
import shutil
import json
from datetime import datetime
import glob
import signal

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Variable global para controlar si el proceso se completó exitosamente
proceso_completado_exitosamente = False

def signal_handler(signum, frame):
    """Manejador de señales para detectar interrupciones."""
    global proceso_completado_exitosamente
    logger.warning("⚠️ Proceso interrumpido por el usuario")
    proceso_completado_exitosamente = False
    sys.exit(1)

# Registrar manejador de señales
signal.signal(signal.SIGINT, signal_handler)

def limpiar_titulo(titulo):
    """Limpia el título para usarlo como nombre de archivo."""
    caracteres_invalidos = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    titulo_limpio = titulo
    for char in caracteres_invalidos:
        titulo_limpio = titulo_limpio.replace(char, '')
    
    if len(titulo_limpio) > 100:
        titulo_limpio = titulo_limpio[:100]
    
    return titulo_limpio.strip()

def obtener_ruta_ffmpeg():
    """Obtiene la ruta de FFmpeg desde imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"FFmpeg encontrado en: {ffmpeg_path}")
        return ffmpeg_path
    except Exception as e:
        logger.warning(f"No se pudo obtener la ruta de FFmpeg: {e}")
        return None

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas correctamente."""
    try:
        import yt_dlp
        import speech_recognition
        import moviepy
        import pydub
        import imageio_ffmpeg
        logger.info("✓ Todas las dependencias están instaladas correctamente")
        return True
    except ImportError as e:
        logger.error(f"✗ Error: Falta la dependencia {e}")
        logger.error("Ejecuta: pip install -r requirements.txt")
        return False

def obtener_directorio_video(titulo_video, ruta_salida):
    """Obtiene el directorio único para un video específico."""
    titulo_limpio = limpiar_titulo(titulo_video)
    directorio_video = os.path.join(ruta_salida, titulo_limpio)
    return directorio_video

def cargar_estado_procesamiento(titulo_video, ruta_salida):
    """Carga el estado de procesamiento desde archivo JSON."""
    directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
    titulo_limpio = limpiar_titulo(titulo_video)
    estado_file = os.path.join(directorio_video, f"estado_procesamiento_{titulo_limpio}.json")
    
    if os.path.exists(estado_file):
        try:
            with open(estado_file, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            logger.info(f"✓ Estado de procesamiento cargado: {estado_file}")
            return estado
        except Exception as e:
            logger.warning(f"No se pudo cargar el estado: {e}")
    
    return None

def guardar_estado_procesamiento(estado, titulo_video, ruta_salida):
    """Guarda el estado de procesamiento en archivo JSON."""
    directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
    os.makedirs(directorio_video, exist_ok=True)
    titulo_limpio = limpiar_titulo(titulo_video)
    estado_file = os.path.join(directorio_video, f"estado_procesamiento_{titulo_limpio}.json")
    
    try:
        with open(estado_file, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Estado guardado: {estado_file}")
    except Exception as e:
        logger.error(f"Error al guardar estado: {e}")

def verificar_segmentos_existentes(titulo_video, ruta_salida):
    """Verifica qué segmentos ya han sido transcritos."""
    directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
    titulo_limpio = limpiar_titulo(titulo_video)
    segmentos_dir = os.path.join(directorio_video, "segmentos_transcripcion")
    
    if not os.path.exists(segmentos_dir):
        return []
    
    # Buscar archivos de segmentos existentes
    patron = os.path.join(segmentos_dir, f"Segmento_*_de_*_{titulo_limpio}.txt")
    archivos_existentes = glob.glob(patron)
    
    segmentos_completados = []
    for archivo in archivos_existentes:
        try:
            # Extraer número de segmento del nombre del archivo
            nombre = os.path.basename(archivo)
            partes = nombre.split('_')
            if len(partes) >= 3:
                numero_segmento = int(partes[1])
                segmentos_completados.append(numero_segmento)
        except:
            continue
    
    return sorted(segmentos_completados)

def descargar_video_youtube(url, ruta_salida='.', titulo_video=None):
    """Descarga el audio de un video de YouTube usando yt-dlp y lo convierte a WAV."""
    try:
        logger.info(f"Iniciando proceso para URL: {url}")
        
        # Obtener ruta de FFmpeg
        ffmpeg_path = obtener_ruta_ffmpeg()
        
        # Configuración para obtener solo la información del video
        ydl_info_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            # Obtener información del video sin descargar
            logger.info("Obteniendo información del video...")
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'video')
            
            # Limpiar título para nombre de archivo
            titulo_limpio = limpiar_titulo(video_title)
            # Guardar el audio en el directorio específico del video
            directorio_video = obtener_directorio_video(video_title, ruta_salida)
            os.makedirs(directorio_video, exist_ok=True)
            audio_file = os.path.join(directorio_video, f"{titulo_limpio}.wav")
            
            # Verificar si el archivo WAV ya existe
            if os.path.exists(audio_file):
                logger.info(f"✓ El archivo de audio ya existe en: {audio_file}")
                logger.info("✓ Usando archivo existente en lugar de descargar nuevamente.")
                return audio_file, video_title
        
        # Si llegamos aquí, necesitamos descargar el video
        logger.info(f"Iniciando descarga del video...")
        logger.info(f"Título: {video_title}")
        duration = info_dict.get('duration', 0)
        if duration:
            logger.info(f"Duración: {duration // 60}:{duration % 60:02d} minutos")
        
        # Configuración para la descarga
        ydl_download_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(directorio_video, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
            # Descargar el audio
            logger.info("Descargando audio...")
            result = ydl.extract_info(url, download=True)
            
            # Obtener la ruta del archivo descargado
            video_file = ydl.prepare_filename(result)
            
            # Verificar que el archivo existe
            if not os.path.exists(video_file):
                logger.error(f"✗ No se encontró el archivo descargado: {video_file}")
                return None, None
            
            # Convertir a WAV usando moviepy
            logger.info("Convirtiendo a WAV...")
            try:
                audio_clip = AudioFileClip(video_file)
                audio_clip.write_audiofile(audio_file, verbose=False, logger=None)
                audio_clip.close()
                
                # Eliminar el archivo de video original
                if os.path.exists(video_file):
                    os.remove(video_file)
                    logger.info("Archivo temporal eliminado")
                
                if os.path.exists(audio_file):
                    logger.info(f"✓ Conversión completada exitosamente!")
                    logger.info(f"Ubicación: {audio_file}")
                    return audio_file, video_title
                else:
                    logger.error("✗ Error al convertir el archivo de audio.")
                    return None, None
                    
            except Exception as e:
                logger.error(f"Error durante la conversión: {e}")
                return None, None
                
    except Exception as e:
        logger.error(f"✗ Error durante la descarga:")
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.error(f"Mensaje: {str(e)}")
        return None, None

def dividir_audio(ruta_audio, titulo_video, ruta_salida, duracion_segmento=60):
    """Divide el audio en segmentos más pequeños."""
    try:
        logger.info(f"Dividiendo audio: {ruta_audio}")
        
        # Cargar el archivo de audio
        audio = AudioSegment.from_file(ruta_audio)
        duracion_total = len(audio) / 1000  # Convertir a segundos
        
        logger.info(f"Duración total: {duracion_total:.2f} segundos")
        
        # Crear directorio temporal específico para este video
        directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
        temp_dir = os.path.join(directorio_video, "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Dividir el audio
        segmentos = []
        for i in range(0, int(duracion_total), duracion_segmento):
            # Calcular el tiempo de inicio y fin del segmento
            inicio = i * 1000  # Convertir a milisegundos
            fin = min((i + duracion_segmento) * 1000, len(audio))
            
            # Extraer segmento
            segmento = audio[inicio:fin]
            
            # Guardar segmento
            nombre_archivo = f"{os.path.splitext(os.path.basename(ruta_audio))[0]}_parte{i//60 + 1}.wav"
            ruta_segmento = os.path.join(temp_dir, nombre_archivo)
            segmento.export(ruta_segmento, format="wav")
            segmentos.append(ruta_segmento)
        
        logger.info(f"✓ Audio dividido en {len(segmentos)} segmentos")
        return segmentos, temp_dir
        
    except Exception as e:
        logger.error(f"Error al dividir el audio: {e}")
        return None, None

def guardar_segmento_transcrito(texto, numero_segmento, total_segmentos, titulo_video, ruta_salida='.'):
    """Guarda la transcripción de un segmento individual."""
    try:
        directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
        titulo_limpio = limpiar_titulo(titulo_video)
        nombre_archivo = f"Segmento_{numero_segmento:03d}_de_{total_segmentos:03d}_{titulo_limpio}.txt"
        segmentos_dir = os.path.join(directorio_video, "segmentos_transcripcion")
        ruta_archivo = os.path.join(segmentos_dir, nombre_archivo)
        
        # Crear directorio si no existe
        os.makedirs(segmentos_dir, exist_ok=True)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(f"Segmento {numero_segmento} de {total_segmentos}\n")
            f.write(f"Tiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n")
            f.write(texto)
            f.write("\n" + "-" * 50 + "\n")
        
        return ruta_archivo
    except Exception as e:
        logger.error(f"Error al guardar segmento {numero_segmento}: {e}")
        return None

def transcribir_audio_resumable(ruta_audio, idioma='es-ES', titulo_video='', ruta_salida='.', keep_files=False):
    """Transcribe el audio con capacidad de reanudación."""
    global proceso_completado_exitosamente
    r = sr.Recognizer()
    texto_completo = []
    temp_dir = None
    archivos_segmentos = []
    
    # Cargar estado de procesamiento
    estado = cargar_estado_procesamiento(titulo_video, ruta_salida)
    if estado and estado.get('etapa') == 'completado':
        logger.info("✓ Procesamiento ya completado anteriormente")
        return "Procesamiento ya completado"
    
    try:
        logger.info(f"Iniciando transcripción del audio: {ruta_audio}")
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_audio):
            logger.error(f"El archivo de audio no existe: {ruta_audio}")
            return "Error: El archivo de audio no existe."
        
        # Obtener información del archivo
        file_size = os.path.getsize(ruta_audio) / (1024 * 1024)  # MB
        logger.info(f"Tamaño del archivo: {file_size:.2f} MB")
        
        # Si el archivo es muy pequeño, no dividir
        if file_size < 10:  # Menos de 10 MB
            logger.info("Archivo pequeño, procesando sin dividir...")
            try:
                with sr.AudioFile(ruta_audio) as fuente:
                    audio = r.record(fuente)
                    logger.info("Transcribiendo audio completo...")
                    texto = r.recognize_google(audio, language=idioma)
                    logger.info("✓ Transcripción completada")
                    
                    # Guardar estado como completado
                    estado_final = {
                        'etapa': 'completado',
                        'archivo_audio': ruta_audio,
                        'fecha_completado': datetime.now().isoformat(),
                        'tamaño_archivo_mb': file_size
                    }
                    guardar_estado_procesamiento(estado_final, titulo_video, ruta_salida)
                    
                    # Marcar como completado exitosamente
                    proceso_completado_exitosamente = True
                    
                    return texto
            except sr.UnknownValueError:
                logger.error("No se pudo entender el audio")
                return "Error: No se pudo entender el audio."
            except sr.RequestError as e:
                logger.error(f"Error en la solicitud: {e}")
                return f"Error en la solicitud: {e}"
        
        # Verificar segmentos ya transcritos
        segmentos_completados = verificar_segmentos_existentes(titulo_video, ruta_salida)
        if segmentos_completados:
            logger.info(f"✓ Encontrados {len(segmentos_completados)} segmentos ya transcritos")
            logger.info(f"Segmentos completados: {segmentos_completados}")
        
        # Dividir el audio en segmentos
        logger.info("Archivo grande, dividiendo en segmentos...")
        resultado = dividir_audio(ruta_audio, titulo_video, ruta_salida)
        
        if not resultado or not resultado[0]:
            return "Error: No se pudieron crear segmentos de audio."
            
        segmentos, temp_dir = resultado
        total_segmentos = len(segmentos)
        
        logger.info(f"Procesando {total_segmentos} segmentos de audio...")
        logger.info("✓ Los segmentos transcritos se guardarán individualmente")
        
        # Cargar segmentos ya transcritos
        directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
        for num_segmento in segmentos_completados:
            if num_segmento <= total_segmentos:
                archivo_segmento = os.path.join(
                    directorio_video, "segmentos_transcripcion",
                    f"Segmento_{num_segmento:03d}_de_{total_segmentos:03d}_{limpiar_titulo(titulo_video)}.txt"
                )
                if os.path.exists(archivo_segmento):
                    try:
                        with open(archivo_segmento, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                            # Extraer solo el texto (sin metadatos)
                            lineas = contenido.split('\n')
                            texto_segmento = '\n'.join(lineas[3:-2])  # Saltar metadatos
                            texto_completo.append(texto_segmento)
                            archivos_segmentos.append(archivo_segmento)
                        logger.info(f"✓ Segmento {num_segmento} cargado desde archivo existente")
                    except Exception as e:
                        logger.warning(f"Error al cargar segmento {num_segmento}: {e}")
        
        # Procesar segmentos faltantes
        for i, segmento in enumerate(segmentos, 1):
            if i in segmentos_completados:
                logger.info(f"⏭️ Saltando segmento {i} (ya completado)")
                continue
                
            logger.info(f"Procesando segmento {i} de {total_segmentos}...")
            
            # Actualizar estado de procesamiento
            estado_actual = {
                'etapa': 'transcribiendo',
                'segmento_actual': i,
                'total_segmentos': total_segmentos,
                'segmentos_completados': len(texto_completo),
                'archivo_audio': ruta_audio,
                'ultima_actualizacion': datetime.now().isoformat()
            }
            guardar_estado_procesamiento(estado_actual, titulo_video, ruta_salida)
            
            try:
                with sr.AudioFile(segmento) as fuente:
                    audio = r.record(fuente)
                    logger.info(f"Transcribiendo segmento {i}...")
                    texto = r.recognize_google(audio, language=idioma)
                    texto_completo.append(texto)
                    
                    # Guardar segmento individual
                    archivo_segmento = guardar_segmento_transcrito(
                        texto, i, total_segmentos, titulo_video, ruta_salida
                    )
                    if archivo_segmento:
                        archivos_segmentos.append(archivo_segmento)
                        logger.info(f"✓ Segmento {i} transcrito y guardado: {os.path.basename(archivo_segmento)}")
                    else:
                        logger.warning(f"⚠ No se pudo guardar el segmento {i}")
                        
            except sr.UnknownValueError:
                logger.warning(f"No se pudo entender el segmento {i}")
                # Guardar segmento vacío
                archivo_segmento = guardar_segmento_transcrito(
                    "[AUDIO NO RECONOCIDO]", i, total_segmentos, titulo_video, ruta_salida
                )
                if archivo_segmento:
                    archivos_segmentos.append(archivo_segmento)
                continue
            except sr.RequestError as e:
                logger.error(f"Error en la solicitud para el segmento {i}: {e}")
                # Guardar segmento con error
                archivo_segmento = guardar_segmento_transcrito(
                    f"[ERROR: {str(e)}]", i, total_segmentos, titulo_video, ruta_salida
                )
                if archivo_segmento:
                    archivos_segmentos.append(archivo_segmento)
                continue
        
        if not texto_completo:
            return "No se pudo transcribir ningún segmento del audio."
            
        texto_final = " ".join(texto_completo)
        logger.info(f"✓ Transcripción completada. Longitud: {len(texto_final)} caracteres")
        
        # Guardar estado como completado
        estado_final = {
            'etapa': 'completado',
            'archivo_audio': ruta_audio,
            'total_segmentos': total_segmentos,
            'segmentos_exitosos': len(texto_completo),
            'fecha_completado': datetime.now().isoformat(),
            'tamaño_archivo_mb': file_size
        }
        guardar_estado_procesamiento(estado_final, titulo_video, ruta_salida)
        
        # Marcar como completado exitosamente
        proceso_completado_exitosamente = True
        
        # Guardar información de archivos generados
        if keep_files:
            info_archivos = {
                'archivo_audio_original': ruta_audio,
                'segmentos_transcripcion': archivos_segmentos,
                'directorio_temp_audio': temp_dir,
                'total_segmentos': total_segmentos,
                'segmentos_exitosos': len(texto_completo),
                'fecha_procesamiento': datetime.now().isoformat()
            }
            
            directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
            info_file = os.path.join(directorio_video, f"info_transcripcion_{limpiar_titulo(titulo_video)}.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info_archivos, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Información de archivos guardada en: {info_file}")
        
        return texto_final
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return f"Error al procesar el audio: {e}"
    finally:
        # Limpiar archivos temporales solo si se completó exitosamente Y no se quiere conservar
        if proceso_completado_exitosamente and not keep_files and temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info("Archivos temporales eliminados")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el directorio temporal: {e}")
        elif not proceso_completado_exitosamente:
            logger.info("⚠️ Proceso interrumpido - archivos temporales conservados para reanudación")

def guardar_transcripcion(texto, titulo_video, ruta_salida='.'):
    """Guarda la transcripción en un archivo de texto."""
    try:
        directorio_video = obtener_directorio_video(titulo_video, ruta_salida)
        os.makedirs(directorio_video, exist_ok=True)
        titulo_limpio = limpiar_titulo(titulo_video)
        nombre_archivo = f"Transcripcion - {titulo_limpio}.txt"
        ruta_archivo = os.path.join(directorio_video, nombre_archivo)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(f"TRANSCRIPCIÓN COMPLETA\n")
            f.write(f"Título: {titulo_video}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(texto)
        
        logger.info(f"✓ Transcripción guardada en '{ruta_archivo}'")
        return ruta_archivo
    except Exception as e:
        logger.error(f"Error al guardar la transcripción: {e}")
        return None

def main():
    """Función principal que procesa los argumentos y orquesta el proceso."""
    global proceso_completado_exitosamente
    
    parser = argparse.ArgumentParser(
        description="Descarga el audio de un video de YouTube y lo transcribe a texto con capacidad de reanudación.",
        epilog="Ejemplo de uso: python transcriptor_cli_resumable.py \"URL_DEL_VIDEO\" -l en-US"
    )
    
    parser.add_argument(
        "url", 
        help="La URL completa del video de YouTube a transcribir."
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Directorio donde se guardarán los archivos (default: directorio actual)."
    )
    parser.add_argument(
        "-l", "--language",
        default="es-ES",
        choices=['es-ES', 'en-US', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR'],
        help="Idioma del audio para la transcripción (default: es-ES)."
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Conserva los archivos de audio (.wav), segmentos y archivos temporales."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada del proceso."
    )
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="Forzar reinicio completo del proceso (ignorar estado guardado)."
    )
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=== INICIANDO TRANSCRIPTOR DE YOUTUBE (CON REANUDACIÓN) ===")
    
    # Verificar dependencias
    if not verificar_dependencias():
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        logger.info(f"Directorio creado: {args.output}")
    
    # Descargar video
    ruta_audio, titulo_video = descargar_video_youtube(args.url, args.output)
    
    if not ruta_audio:
        logger.error("No se pudo descargar el video. Saliendo...")
        sys.exit(1)
    
    # Verificar si ya está completado (a menos que se fuerce reinicio)
    if not args.force_restart:
        estado = cargar_estado_procesamiento(titulo_video, args.output)
        if estado and estado.get('etapa') == 'completado':
            logger.info("✓ Procesamiento ya completado anteriormente")
            logger.info("Usa --force-restart para reiniciar completamente")
            
            # Verificar si existe el archivo de transcripción
            directorio_video = obtener_directorio_video(titulo_video, args.output)
            titulo_limpio = limpiar_titulo(titulo_video)
            transcripcion_file = os.path.join(directorio_video, f"Transcripcion - {titulo_limpio}.txt")
            if os.path.exists(transcripcion_file):
                logger.info(f"✓ Archivo de transcripción encontrado: {transcripcion_file}")
                sys.exit(0)
    
    # Transcribir audio
    logger.info("Iniciando transcripción...")
    texto_transcrito = transcribir_audio_resumable(
        ruta_audio, 
        idioma=args.language, 
        titulo_video=titulo_video,
        ruta_salida=args.output,
        keep_files=args.keep_files
    )
    
    if texto_transcrito and not texto_transcrito.startswith("Error") and texto_transcrito != "Procesamiento ya completado":
        # Guardar transcripción completa
        archivo_guardado = guardar_transcripcion(texto_transcrito, titulo_video, args.output)
        if archivo_guardado:
            logger.info("=== TRANSCRIPCIÓN COMPLETADA EXITOSAMENTE ===")
            logger.info(f"Archivo guardado: {archivo_guardado}")
            
            if args.keep_files:
                logger.info("✓ Archivos temporales conservados (--keep-files activado)")
                logger.info("  - Archivo de audio original")
                logger.info("  - Segmentos de transcripción individuales")
                logger.info("  - Información de procesamiento (JSON)")
                logger.info("  - Estado de procesamiento (JSON)")
        else:
            logger.error("Error al guardar la transcripción")
    else:
        logger.info(f"Proceso completado: {texto_transcrito}")
    
    # Limpiar archivo de audio solo si se completó exitosamente Y no se quiere conservar
    if proceso_completado_exitosamente and not args.keep_files and os.path.exists(ruta_audio):
        logger.info("Eliminando archivos temporales...")
        try:
            os.remove(ruta_audio)
            logger.info("✓ Archivos temporales eliminados")
        except OSError as e:
            logger.warning(f"Error al eliminar archivos temporales: {e}")
    elif not proceso_completado_exitosamente:
        logger.info("⚠️ Proceso interrumpido - archivo de audio conservado para reanudación")

if __name__ == "__main__":
    main()
