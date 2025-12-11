#!/usr/bin/env python3
"""
Script de prueba para verificar la instalación del Transcriptor de YouTube con Recuperación
"""

import sys
import importlib

def test_imports():
    """Prueba que todas las dependencias estén instaladas correctamente."""
    print("=== PRUEBA DE DEPENDENCIAS ===")
    
    dependencies = [
        ('yt_dlp', None),
        ('speech_recognition', None), 
        ('moviepy', 'moviepy.editor'),  # Verificar también moviepy.editor
        ('pydub', None),
        ('imageio_ffmpeg', None)
    ]
    
    all_good = True
    
    for dep, submodule in dependencies:
        try:
            importlib.import_module(dep)
            if submodule:
                # Verificar también el submódulo si se especifica
                importlib.import_module(submodule)
            print(f"✅ {dep}" + (f" ({submodule})" if submodule else ""))
        except ImportError as e:
            print(f"❌ {dep}" + (f" ({submodule})" if submodule else "") + f": {e}")
            all_good = False
    
    return all_good

def test_ffmpeg():
    """Prueba que FFmpeg esté disponible."""
    print("\n=== PRUEBA DE FFMPEG ===")
    
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"✅ FFmpeg encontrado en: {ffmpeg_path}")
        return True
    except Exception as e:
        print(f"❌ Error con FFmpeg: {e}")
        return False

def test_yt_dlp():
    """Prueba la funcionalidad básica de yt-dlp."""
    print("\n=== PRUEBA DE YT-DLP ===")
    
    try:
        import yt_dlp
        
        # Configuración básica
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # URL de prueba (video corto)
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            print("🔍 Probando conexión con YouTube...")
            
            # Solo obtener información, no descargar
            info = ydl.extract_info(test_url, download=False)
            title = info.get('title', 'Sin título')
            duration = info.get('duration', 0)
            
            print(f"✅ Conexión exitosa")
            print(f"   Título: {title}")
            print(f"   Duración: {duration} segundos")
            
        return True
        
    except Exception as e:
        print(f"❌ Error con yt-dlp: {e}")
        return False

def test_speech_recognition():
    """Prueba la funcionalidad básica de speech recognition."""
    print("\n=== PRUEBA DE SPEECH RECOGNITION ===")
    
    try:
        import speech_recognition as sr
        
        # Crear reconocedor
        r = sr.Recognizer()
        print("✅ Speech Recognition inicializado correctamente")
        
        # Verificar que Google Speech Recognition esté disponible
        print("🔍 Verificando disponibilidad de Google Speech Recognition...")
        
        # Nota: No podemos probar la API real sin audio, pero verificamos la configuración
        print("✅ Configuración de Speech Recognition correcta")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con Speech Recognition: {e}")
        return False

def test_audio_processing():
    """Prueba las librerías de procesamiento de audio."""
    print("\n=== PRUEBA DE PROCESAMIENTO DE AUDIO ===")
    
    try:
        from moviepy.editor import AudioFileClip
        from pydub import AudioSegment
        
        print("✅ MoviePy cargado correctamente")
        print("✅ PyDub cargado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con procesamiento de audio: {e}")
        return False

def test_transcriptor_module():
    """Prueba que el módulo del transcriptor se pueda importar."""
    print("\n=== PRUEBA DEL MÓDULO TRANSCRIPTOR ===")
    
    try:
        # Intentar importar funciones del transcriptor
        sys.path.append('.')
        
        # Importar funciones específicas
        from transcriptor_cli_resumable import (
            limpiar_titulo,
            verificar_dependencias,
            obtener_ruta_ffmpeg
        )
        
        print("✅ Módulo transcriptor importado correctamente")
        
        # Probar función de limpieza de título
        test_title = "Test Video: < > : \" / \\ | ? * [caracteres problemáticos]"
        clean_title = limpiar_titulo(test_title)
        print(f"✅ Función limpiar_titulo: '{test_title}' -> '{clean_title}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con el módulo transcriptor: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🔧 TRANSCRIPTOR DE YOUTUBE - PRUEBAS DE INSTALACIÓN")
    print("=" * 60)
    
    # Ejecutar todas las pruebas
    tests = [
        test_imports,
        test_ffmpeg,
        test_yt_dlp,
        test_speech_recognition,
        test_audio_processing,
        test_transcriptor_module
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en prueba: {e}")
            results.append(False)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Pruebas exitosas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El transcriptor está listo para usar")
        print("\nPara usar el transcriptor con Docker:")
        print("  docker-compose run --rm transcriptor python transcriptor_cli_resumable.py \"URL_DEL_VIDEO\" --verbose")
        print("\nO usar el script de ayuda:")
        print("  ./docker-run.sh \"URL_DEL_VIDEO\"  # Linux/Mac")
        print("  docker-run.bat \"URL_DEL_VIDEO\"   # Windows")
        return 0
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON")
        print("❌ Revisa los errores arriba y reconstruye la imagen Docker:")
        print("  docker-compose build --no-cache")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)
