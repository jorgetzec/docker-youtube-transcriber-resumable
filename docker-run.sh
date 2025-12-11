#!/bin/bash
# Script de ayuda para ejecutar el transcriptor con Docker
# Uso: ./docker-run.sh "URL_DEL_VIDEO" [opciones]

if [ -z "$1" ]; then
    echo "Error: Debes proporcionar una URL de YouTube"
    echo ""
    echo "Uso: ./docker-run.sh \"URL_DEL_VIDEO\" [opciones]"
    echo ""
    echo "Ejemplos:"
    echo "  ./docker-run.sh \"https://www.youtube.com/watch?v=VIDEO_ID\""
    echo "  ./docker-run.sh \"https://www.youtube.com/watch?v=VIDEO_ID\" --keep-files"
    echo "  ./docker-run.sh \"https://www.youtube.com/watch?v=VIDEO_ID\" -l en-US --verbose"
    exit 1
fi

# Construir la imagen si no existe
if ! docker images | grep -q youtube-transcriber; then
    echo "Construyendo imagen Docker..."
    docker-compose build
fi

# Ejecutar el transcriptor
docker-compose run --rm transcriptor python transcriptor_cli_resumable.py "$@" --verbose

