#!/bin/bash

# Script para configurar el entorno de Python API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Configurando entorno para Python API..."

# Verificar si ya existe un archivo .env
if [ -f ".env" ]; then
    print_warning "El archivo .env ya existe."
    read -p "¿Deseas sobrescribirlo? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Configuración cancelada."
        exit 0
    fi
fi

# Copiar el archivo de ejemplo
if [ -f "env.example" ]; then
    cp env.example .env
    print_success "Archivo .env creado desde env.example"
else
    print_error "No se encontró el archivo env.example"
    exit 1
fi

# Solicitar la API key de Gemini
print_status "Configuración de la API key de Gemini..."
echo "Necesitas una API key de Google Gemini para usar el servicio de IA."
echo "Puedes obtenerla en: https://makersuite.google.com/app/apikey"
echo ""

read -p "Ingresa tu GEMINI_API_KEY: " gemini_key

if [ -n "$gemini_key" ]; then
    # Actualizar el archivo .env con la API key
    sed -i "s/your_gemini_api_key_here/$gemini_key/" .env
    print_success "API key configurada correctamente"
else
    print_warning "No se proporcionó API key. Deberás configurarla manualmente en el archivo .env"
fi

# Instalar dependencias
print_status "Instalando dependencias..."
if command -v uv &> /dev/null; then
    uv sync
    print_success "Dependencias instaladas con uv"
else
    print_warning "uv no está instalado. Instalando con pip..."
    pip install -e .
    print_success "Dependencias instaladas con pip"
fi

print_success "¡Configuración completada!"
echo ""
print_status "Para iniciar el servidor:"
echo "  python3 run_api.py"
echo ""
print_status "Para usar Docker:"
echo "  docker-compose up python-api"
echo ""
print_status "Archivo .env creado en: $(pwd)/.env"
print_warning "Recuerda no compartir tu archivo .env ya que contiene tu API key"
