# YouTube Transcriber - Herramienta de Transcripción con Docker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-required-blue.svg)](https://www.docker.com/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

Herramienta profesional para descargar el audio de videos de YouTube y transcribirlos a texto utilizando reconocimiento de voz de Google, con sistema completo de recuperación y reanudación.

## Características Principales

- **Descarga automática** de audio de videos de YouTube
- **Conversión automática** a formato WAV
- **Transcripción inteligente** con reconocimiento de voz de Google
- **Sistema de recuperación completo** - Reanuda desde donde se quedó
- **Detección automática** de segmentos ya transcritos
- **Soporte multi-idioma** (español, inglés, francés, alemán, italiano, portugués)
- **División automática** de archivos grandes en segmentos
- **Guardado incremental** de segmentos individuales
- **Manejo robusto de interrupciones** - Conserva archivos en caso de error
- **Containerizado con Docker** - Fácil instalación y uso

## Requisitos

- **Docker** y **Docker Compose** instalados
- Conexión a Internet estable
- Mínimo 100MB de espacio libre en disco

## Instalación con Docker

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/jorgetzec/docker-youtube-transcriber-resumable.git
cd docker-youtube-transcriber-resumable
```

### 2. Construir la imagen Docker

```bash
docker-compose build
```

### 3. Verificar la instalación (opcional)

```bash
docker-compose run --rm transcriptor python test_transcriptor_cli_resumable.py
```

## Uso

### Uso Básico

#### Opción 1: Usando docker-compose directamente
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL_DEL_VIDEO" --verbose
```

**Nota importante sobre archivos de salida:**
- Por defecto, los archivos se guardan en el directorio actual del contenedor (`/app/workspace`), que está montado en el directorio del proyecto donde está el `docker-compose.yml`
- Esto significa que **los archivos de transcripción aparecerán directamente en tu directorio del proyecto**
- Si prefieres guardarlos en una carpeta específica, usa la opción `-o`:
  ```bash
  docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" -o /app/output --verbose
  ```
  Esto guardará los archivos en la carpeta `./output` de tu proyecto

#### Opción 2: Usando scripts de ayuda (más fácil)
```bash
# Linux/Mac
./docker-run.sh "URL_DEL_VIDEO"

# Windows
docker-run.bat "URL_DEL_VIDEO"
```

### Ejemplos de Uso

#### Transcripción básica (español por defecto):
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

#### Transcripción en inglés:
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "https://www.youtube.com/watch?v=VIDEO_ID" -l en-US --verbose
```

#### Conservar archivos temporales:
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "https://www.youtube.com/watch?v=VIDEO_ID" --keep-files --verbose
```

#### Directorio de salida específico:
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "https://www.youtube.com/watch?v=VIDEO_ID" -o ./mis_transcripciones --verbose
```

#### Forzar reinicio completo (ignorar estado guardado):
```bash
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "https://www.youtube.com/watch?v=VIDEO_ID" --force-restart --verbose
```

### Usar con volumen persistente

Para mantener los archivos generados entre ejecuciones, monta un volumen:

```bash
docker-compose run --rm -v $(pwd)/transcripciones:/app/output transcriptor python transcriptor_cli_resumable.py "URL" -o /app/output --verbose
```

En Windows PowerShell:
```powershell
docker-compose run --rm -v ${PWD}/transcripciones:/app/output transcriptor python transcriptor_cli_resumable.py "URL" -o /app/output --verbose
```

## Archivos Generados

### Estructura de Archivos

Cada video se organiza en su propio directorio para evitar conflictos al procesar múltiples videos simultáneamente:

```
Directorio de salida/
└── [TITULO_VIDEO]/                       # Directorio único por video
    ├── Transcripcion - [TITULO].txt      # Transcripción completa
    ├── estado_procesamiento_[TITULO].json # Estado del procesamiento
    ├── [TITULO].wav                      # Archivo de audio (con --keep-files)
    ├── info_transcripcion_[TITULO].json  # Información completa (con --keep-files)
    ├── segmentos_transcripcion/          # Segmentos individuales
    │   ├── Segmento_001_de_137_[TITULO].txt
    │   ├── Segmento_002_de_137_[TITULO].txt
    │   └── ...
    └── temp_audio/                       # Segmentos de audio (con --keep-files)
        ├── [TITULO]_parte1.wav
        └── ...
```

**Ventajas de esta estructura:**
- **Aislamiento por video**: Cada video tiene su propio directorio
- **Procesamiento simultáneo seguro**: Múltiples videos pueden procesarse sin conflictos
- **Limpieza independiente**: Al eliminar archivos temporales, solo afecta al video correspondiente
- **Organización clara**: Fácil encontrar todos los archivos relacionados con un video específico

## Opciones Disponibles

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `URL` | URL del video (requerido) | `"https://youtu.be/VIDEO_ID"` |
| `-o, --output` | Directorio de salida | `-o ./mis_transcripciones` |
| `-l, --language` | Idioma del audio | `-l en-US` |
| `--keep-files` | Conservar archivos temporales | `--keep-files` |
| `--verbose, -v` | Información detallada | `--verbose` |
| `--force-restart` | Reinicio completo | `--force-restart` |

### Idiomas Soportados

- `es-ES` - Español (predeterminado)
- `en-US` - Inglés
- `fr-FR` - Francés
- `de-DE` - Alemán
- `it-IT` - Italiano
- `pt-BR` - Portugués

## Sistema de Recuperación

### ¿Cómo Funciona?

El script `transcriptor_cli_resumable.py` incluye un sistema completo de recuperación:

1. **Detección Automática**: Detecta si el video ya fue procesado
2. **Segmentos Existentes**: Identifica qué segmentos ya están transcritos
3. **Reanudación Inteligente**: Continúa desde donde se quedó
4. **Estado Transparente**: Archivos JSON legibles con el progreso
5. **Manejo de Interrupciones**: Conserva archivos en caso de error

### Ejemplo de Recuperación

```bash
# Primera ejecución (se interrumpe en segmento 45)
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" --verbose

# Segunda ejecución (reanuda automáticamente desde segmento 45)
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" --verbose
```

**Salida esperada:**
```
Estado de procesamiento cargado: estado_procesamiento_Titulo.json
Encontrados 44 segmentos ya transcritos
Saltando segmento 1 (ya completado)
Saltando segmento 2 (ya completado)
...
Procesando segmento 45 de 137...
```

### Archivo de Estado

El script mantiene un archivo `estado_procesamiento_[TITULO].json` que registra:

```json
{
  "etapa": "transcribiendo",
  "segmento_actual": 45,
  "total_segmentos": 137,
  "segmentos_completados": 44,
  "archivo_audio": "ruta/al/audio.wav",
  "ultima_actualizacion": "2025-08-17T21:48:14"
}
```

## Scripts Disponibles

### Scripts Principales

#### `transcriptor_cli_resumable.py` (RECOMENDADO)
- **Descripción**: Script principal con sistema completo de recuperación
- **Características**:
  - Recuperación automática de interrupciones
  - Detección de segmentos ya transcritos
  - Reanudación desde donde se quedó
  - Archivos de estado para monitoreo
  - Opción `--force-restart` para reinicio completo
  - Manejo inteligente de archivos temporales


#### `limpiar_archivos_temporales.py`
- **Descripción**: Utilidad para limpiar archivos temporales de procesos completados
- **Uso**:
  ```bash
  docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --mostrar
  docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --limpiar
  ```

### Scripts de Prueba

#### `test_transcriptor_cli_resumable.py`
- **Descripción**: Pruebas de instalación y verificación de dependencias
- **Uso**:
  ```bash
  docker-compose run --rm transcriptor python test_transcriptor_cli_resumable.py
  ```

## Solución de Problemas

### Error de dependencias

```bash
# Reconstruir la imagen Docker
docker-compose build --no-cache
```

### Error de conexión

- Verifica tu conexión a Internet
- Asegúrate de que la URL del video sea correcta
- Intenta con otro video

### Error de transcripción

- El audio debe ser claro y sin mucho ruido de fondo
- Verifica que el idioma seleccionado sea correcto
- Para videos largos, el proceso puede tomar varios minutos

### Proceso interrumpido

- **Simplemente ejecuta el mismo comando nuevamente**
- El script detectará automáticamente dónde se quedó
- Continuará desde el último segmento procesado

### Error de FFmpeg

```bash
# Reconstruir la imagen
docker-compose build --no-cache
```

## Casos de Uso

### Caso 1: Interrupción por error de red
```bash
# Se interrumpe en segmento 67 de 137
# Al reanudar, continúa desde segmento 68
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" --verbose
```

### Caso 2: Proceso ya completado
```bash
# Detecta que ya está terminado
# No hace nada, muestra archivo existente
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" --verbose
```

### Caso 3: Reinicio forzado
```bash
# --force-restart ignora estado guardado
# Comienza desde cero
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" --force-restart --verbose
```

### Caso 4: Cambio de idioma
```bash
# Cambia idioma en nueva ejecución
# Procesa solo segmentos faltantes con nuevo idioma
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "URL" -l en-US --verbose
```

## Notas Importantes

1. **Los segmentos se guardan automáticamente** en la carpeta `segmentos_transcripcion/`
2. **El argumento `--keep-files`** conserva todos los archivos temporales
3. **Los nombres de archivo usan el título real** del video
4. **Se genera información JSON** para automatización y análisis
5. **El proceso es robusto** ante interrupciones
6. **Los archivos temporales se conservan** en caso de interrupción
7. **La calidad de la transcripción** depende de la claridad del audio

## Monitoreo del Progreso

### Durante la Transcripción:
```
Estado guardado: estado_procesamiento_Titulo.json
Procesando segmento 45 de 137...
Segmento 45 transcrito y guardado: Segmento_045_de_137_Titulo.txt
Estado guardado: estado_procesamiento_Titulo.json
```

### Al Completar:
```
Transcripción completada. Longitud: 15420 caracteres
Estado guardado: estado_procesamiento_Titulo.json
Archivos temporales eliminados
```

### En Interrupción:
```
Proceso interrumpido por el usuario
Proceso interrumpido - archivos temporales conservados para reanudación
```

## Limpieza de Archivos Temporales

### Usar el script de limpieza:

```bash
# Mostrar estado de archivos
docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --mostrar

# Limpiar archivos de procesos completados
docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --limpiar

# Limpiar archivos de un video específico
docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --titulo "TITULO_DEL_VIDEO" --limpiar

# Limpiar archivos en directorio específico
docker-compose run --rm transcriptor python limpiar_archivos_temporales.py --directorio ./clase6 --limpiar
```

## Estructura del Proyecto

```
docker-youtube-transcriber-resumable/
├── README.md                          # Esta documentación
├── requirements.txt                   # Dependencias de Python
├── Dockerfile                         # Configuración de Docker
├── docker-compose.yml                 # Configuración de Docker Compose
├── .dockerignore                      # Archivos ignorados por Docker
├── docker-run.sh                      # Script de ayuda (Linux/Mac)
├── docker-run.bat                     # Script de ayuda (Windows)
├── transcriptor_cli_resumable.py      # Script principal
├── limpiar_archivos_temporales.py     # Utilidad de limpieza
└── test_transcriptor_cli_resumable.py # Script de pruebas
```

## Ventajas del Sistema de Recuperación

### 1. Ahorro de Tiempo
- **No repite trabajo**: Salta segmentos ya transcritos
- **Reanudación instantánea**: Detecta estado automáticamente
- **Progreso preservado**: No pierde trabajo realizado
- **No redescarga**: Conserva archivos de audio en interrupciones

### 2. Robustez
- **Interrupciones seguras**: Puede interrumpirse en cualquier momento
- **Errores de red**: Reanuda después de errores de conexión
- **Fallos del sistema**: Continúa después de reinicios
- **Archivos preservados**: No elimina archivos en interrupciones

### 3. Flexibilidad
- **Reinicio opcional**: `--force-restart` para empezar de nuevo
- **Verificación automática**: Detecta si ya está completado
- **Estado transparente**: Archivos JSON legibles
- **Limpieza manual**: Script para limpiar archivos cuando sea necesario

## Licencia

Este proyecto está bajo la Licencia MIT.

---

**Versión:** 2.0 (Con Recuperación y Docker)  
**Fecha:** Agosto 2025  
**Script Principal Recomendado:** `transcriptor_cli_resumable.py`
