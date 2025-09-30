#!/usr/bin/env python3
"""
Script de ejemplo para probar la API de mezcla de imágenes.
"""

import requests
import os
from pathlib import Path

def test_health():
    """Prueba el endpoint de health check."""
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        print("✅ Health check exitoso:")
        print(f"   Status: {response.json()['status']}")
        print(f"   Message: {response.json()['message']}")
        return True
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_mix_images():
    """Prueba el endpoint de mezcla de imágenes."""
    try:
        # Buscar imágenes en el directorio images
        images_dir = Path("images")
        image_files = list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        
        if not image_files:
            print("❌ No se encontraron imágenes en el directorio 'images'")
            return False
        
        # Usar las primeras 2 imágenes disponibles
        files_to_upload = image_files[:2]
        
        files = []
        for img_path in files_to_upload:
            files.append(('images', open(img_path, 'rb')))
        
        data = {
            'prompt': 'Create a professional product advertisement',
            'output_dir': 'test_output'
        }
        
        print(f"🔄 Enviando {len(files)} imágenes para mezclar...")
        response = requests.post("http://localhost:8000/mix-images", files=files, data=data)
        
        # Cerrar archivos
        for _, file_obj in files:
            file_obj.close()
        
        response.raise_for_status()
        result = response.json()
        
        print("✅ Mezcla de imágenes exitosa:")
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print(f"   Archivos generados: {len(result['generated_files'])}")
        for file_path in result['generated_files']:
            print(f"     - {file_path}")
        
        if result.get('text_output'):
            print(f"   Texto generado: {result['text_output']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en mezcla de imágenes: {e}")
        return False

def main():
    """Función principal para ejecutar las pruebas."""
    print("🚀 Iniciando pruebas de la API...")
    print()
    
    # Verificar que el servidor esté ejecutándose
    print("1. Probando health check...")
    if not test_health():
        print("\n❌ El servidor no está ejecutándose. Inicia la API con:")
        print("   python run_api.py")
        return
    
    print()
    print("2. Probando mezcla de imágenes...")
    test_mix_images()
    
    print()
    print("✨ Pruebas completadas!")

if __name__ == "__main__":
    main()
