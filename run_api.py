#!/home/lta/projects/probador_virtual/python/env/bin/python3

"""
Script para iniciar la API de mezcla de imágenes.
"""

import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar el directorio src al path para importar los módulos
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Verificar que la API key esté configurada
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GEMINI_API_KEY o GOOGLE_API_KEY debe estar configurada")
        print("Opción 1: Crea un archivo .env con tu API key:")
        print("  GEMINI_API_KEY=tu_api_key_aqui")
        print("Opción 2: Exporta la variable de entorno:")
        print("  export GEMINI_API_KEY='tu_api_key'")
        print("Opción 3: Copia env.example a .env y configura tu API key")
        sys.exit(1)
    
    # Configuración del servidor
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "true").lower() == "true"
    
    print(f"Iniciando servidor en http://{host}:{port}")
    print(f"Documentación de la API disponible en http://{host}:{port}/docs")
    
    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
