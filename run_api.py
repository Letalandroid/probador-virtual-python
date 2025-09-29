#!/usr/bin/env python3
"""
Script para iniciar la API de mezcla de imágenes.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Agregar el directorio src al path para importar los módulos
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Verificar que la API key esté configurada
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GEMINI_API_KEY o GOOGLE_API_KEY debe estar configurada")
        print("Ejecuta: export GEMINI_API_KEY='tu_api_key'")
        sys.exit(1)
    
    # Configuración del servidor
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "true").lower() == "true"
    
    print(f"Iniciando servidor en http://{host}:{port}")
    print("Documentación de la API disponible en http://localhost:8000/docs")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
