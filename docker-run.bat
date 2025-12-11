@echo off
REM Script de ayuda para ejecutar el transcriptor con Docker en Windows
REM Uso: docker-run.bat "URL_DEL_VIDEO" [opciones]

if "%~1"=="" (
    echo Error: Debes proporcionar una URL de YouTube
    echo.
    echo Uso: docker-run.bat "URL_DEL_VIDEO" [opciones]
    echo.
    echo Ejemplos:
    echo   docker-run.bat "https://www.youtube.com/watch?v=VIDEO_ID"
    echo   docker-run.bat "https://www.youtube.com/watch?v=VIDEO_ID" --keep-files
    echo   docker-run.bat "https://www.youtube.com/watch?v=VIDEO_ID" -l en-US --verbose
    exit /b 1
)

REM Construir la imagen si no existe
docker images | findstr youtube-transcriber >nul 2>&1
if errorlevel 1 (
    echo Construyendo imagen Docker...
    docker-compose build
)

REM Ejecutar el transcriptor
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py %* --verbose

