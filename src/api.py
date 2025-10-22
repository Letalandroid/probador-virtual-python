import os
import mimetypes
import time
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from .models import (
    MixImagesResponse, 
    HealthResponse, 
    ErrorResponse,
    TorsoDetectionResponse,
    VirtualTryOnResponse,
    ClothingFitAnalysisResponse,
    MultipleAnglesResponse,
    ImageEnhancementResponse
)
from .torso_detection import create_torso_detector
from .clothing_overlay import create_clothing_overlay

# Initialize FastAPI app
app = FastAPI(
    title="Virtual Try-On AI API",
    description="API para probador virtual con IA usando Google Gemini",
    version="2.0.0"
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "gemini-2.5-flash-image-preview"


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Image Mixer API is running"
    )


@app.get("/generated_images/{filename}")
async def get_generated_image(filename: str):
    """Serve generated images."""
    try:
        # Usar ruta relativa al directorio del proyecto
        project_dir = Path(__file__).parent.parent
        image_path = project_dir / "generated_images" / filename
        
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Determine content type based on file extension
        content_type = "image/jpeg"  # default
        if filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        # Read and return the image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        return Response(
            content=image_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving image: {str(e)}"
        )


@app.post("/mix-images", response_model=MixImagesResponse)
async def mix_images(
    images: List[UploadFile] = File(..., description="Lista de imágenes a mezclar (1-5 imágenes)"),
    prompt: Optional[str] = Form(None, description="Prompt personalizado para la mezcla"),
    output_dir: str = Form("output", description="Directorio de salida para las imágenes generadas")
):
    """
    Mezcla de 1 a 5 imágenes usando Google Generative AI.
    
    - **images**: Lista de archivos de imagen (1-5 imágenes)
    - **prompt**: Prompt opcional para la mezcla. Si no se proporciona, se usará un prompt por defecto
    - **output_dir**: Directorio donde guardar las imágenes generadas
    """
    try:
        # Validar número de imágenes
        if not (1 <= len(images) <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar entre 1 y 5 imágenes"
            )
        
        # Validar tipos de archivo
        for image in images:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo {image.filename} no es una imagen válida"
                )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Determinar el prompt
        final_prompt = prompt
        if final_prompt is None:
            if len(images) == 1:
                final_prompt = "Turn this image into a professional quality studio shoot with better lighting and depth of field."
            else:
                final_prompt = "Combine the subjects of these images in a natural way, producing a new image."
        
        # Procesar imágenes
        result = await process_images(images, final_prompt, output_dir, api_key)
        
        return MixImagesResponse(
            success=True,
            message=f"Imágenes procesadas exitosamente. {len(result['files'])} archivo(s) generado(s).",
            generated_files=result['files'],
            text_output=result.get('text', '')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


async def process_images(
    images: List[UploadFile], 
    prompt: str, 
    output_dir: str, 
    api_key: str
) -> dict:
    """Procesa las imágenes usando Google Generative AI."""
    
    client = genai.Client(api_key=api_key)
    
    # Cargar imágenes
    contents = []
    for image in images:
        image_data = await image.read()
        contents.append(
            types.Part(
                inline_data=types.Blob(
                    data=image_data, 
                    mime_type=image.content_type
                )
            )
        )
    
    # Agregar prompt
    contents.append(types.Part.from_text(text=prompt))
    
    # Configurar generación
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )
    
    # Generar contenido
    stream = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=contents,
        config=generate_content_config,
    )
    
    # Procesar respuesta
    return await process_api_stream_response(stream, output_dir)


async def process_api_stream_response(stream, output_dir: str) -> dict:
    """Procesa la respuesta del stream de la API, guardando imágenes y texto."""
    files = []
    text_output = ""
    file_index = 0
    
    for chunk in stream:
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue

        for part in chunk.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                timestamp = int(time.time())
                file_extension = mimetypes.guess_extension(part.inline_data.mime_type)
                file_name = os.path.join(
                    output_dir,
                    f"remixed_image_{timestamp}_{file_index}{file_extension}",
                )
                await save_binary_file(file_name, part.inline_data.data)
                files.append(file_name)
                file_index += 1
            elif part.text:
                text_output += part.text
    
    return {
        "files": files,
        "text": text_output
    }


async def save_binary_file(file_name: str, data: bytes):
    """Guarda datos binarios en un archivo especificado."""
    with open(file_name, "wb") as f:
        f.write(data)


# ==================== VIRTUAL TRY-ON ENDPOINTS ====================

@app.post("/detect-torso", response_model=TorsoDetectionResponse)
async def detect_torso(
    person_image: UploadFile = File(..., description="Imagen de la persona para detectar el torso")
):
    """
    Detecta y analiza el torso humano en una imagen.
    
    - **person_image**: Imagen de la persona para análisis
    """
    try:
        # Validar tipo de archivo
        if not person_image.content_type or not person_image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen válida"
            )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Leer imagen
        image_data = await person_image.read()
        
        # Crear detector de torso
        torso_detector = await create_torso_detector()
        
        # Detectar torso
        analysis = await torso_detector.detect_torso(
            image_data, 
            person_image.content_type
        )
        
        return TorsoDetectionResponse(
            success=True,
            message="Análisis de torso completado exitosamente",
            analysis=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en detección de torso: {str(e)}"
        )


@app.post("/virtual-try-on", response_model=VirtualTryOnResponse)
async def virtual_try_on(
    person_image: UploadFile = File(..., description="Imagen de la persona"),
    clothing_image: UploadFile = File(..., description="Imagen de la prenda"),
    clothing_type: str = Form("shirt", description="Tipo de prenda (shirt, dress, jacket, etc.)"),
    style_preferences: Optional[str] = Form(None, description="Preferencias de estilo en JSON")
):
    """
    Crea una imagen de la persona con la prenda superpuesta.
    
    - **person_image**: Imagen de la persona
    - **clothing_image**: Imagen de la prenda
    - **clothing_type**: Tipo de prenda
    - **style_preferences**: Preferencias de estilo opcionales
    """
    try:
        # Validar tipos de archivo
        for image, name in [(person_image, "person"), (clothing_image, "clothing")]:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo {name} debe ser una imagen válida"
                )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Leer imágenes
        person_data = await person_image.read()
        clothing_data = await clothing_image.read()
        
        # Parsear preferencias de estilo
        style_prefs = None
        if style_preferences:
            try:
                import json
                style_prefs = json.loads(style_preferences)
            except json.JSONDecodeError:
                pass
        
        # Crear generador de superposición
        overlay_generator = await create_clothing_overlay()
        
        # Generar try-on
        result = await overlay_generator.create_virtual_try_on(
            person_data,
            clothing_data,
            person_image.content_type,
            clothing_image.content_type,
            clothing_type,
            style_prefs
        )
        
        if result["success"]:
            # Guardar imágenes localmente y devolver URLs
            generated_images = []
            # Usar ruta relativa al directorio del proyecto
            project_dir = Path(__file__).parent.parent
            output_dir = project_dir / "generated_images"
            
            for i, img in enumerate(result["generated_images"]):
                # Generar nombre único para la imagen
                timestamp = int(time.time())
                filename = f"virtual_try_on_{timestamp}_{i}.{img['mime_type'].split('/')[-1]}"
                filepath = os.path.join(output_dir, filename)
                
                # Guardar imagen localmente
                await save_binary_file(filepath, img["data"])
                
                # Crear URL para acceder a la imagen
                base_url = os.environ.get("BASE_URL", "http://localhost:8000")
                image_url = f"{base_url}/generated_images/{filename}"
                
                generated_images.append({
                    "url": image_url,
                    "filename": filename,
                    "mime_type": img["mime_type"],
                    "local_path": filepath
                })
            
            return VirtualTryOnResponse(
                success=True,
                message="Try-on virtual completado exitosamente",
                generated_images=generated_images,
                metadata=result.get("metadata", {})
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error desconocido en try-on virtual")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en try-on virtual: {str(e)}"
        )


@app.post("/analyze-clothing-fit", response_model=ClothingFitAnalysisResponse)
async def analyze_clothing_fit(
    person_image: UploadFile = File(..., description="Imagen de la persona"),
    clothing_image: UploadFile = File(..., description="Imagen de la prenda")
):
    """
    Analiza cómo quedaría una prenda en la persona.
    
    - **person_image**: Imagen de la persona
    - **clothing_image**: Imagen de la prenda
    """
    try:
        # Validar tipos de archivo
        for image, name in [(person_image, "person"), (clothing_image, "clothing")]:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo {name} debe ser una imagen válida"
                )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Leer imágenes
        person_data = await person_image.read()
        clothing_data = await clothing_image.read()
        
        # Crear detector de torso
        torso_detector = await create_torso_detector()
        
        # Analizar ajuste
        analysis = await torso_detector.analyze_clothing_fit(
            person_data,
            clothing_data,
            person_image.content_type,
            clothing_image.content_type
        )
        
        return ClothingFitAnalysisResponse(
            success=True,
            message="Análisis de ajuste completado exitosamente",
            analysis=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en análisis de ajuste: {str(e)}"
        )


@app.post("/multiple-angles", response_model=MultipleAnglesResponse)
async def generate_multiple_angles(
    person_image: UploadFile = File(..., description="Imagen de la persona"),
    clothing_image: UploadFile = File(..., description="Imagen de la prenda"),
    angles: str = Form("front,side,back", description="Ángulos deseados separados por comas")
):
    """
    Genera múltiples ángulos de la persona con la prenda.
    
    - **person_image**: Imagen de la persona
    - **clothing_image**: Imagen de la prenda
    - **angles**: Ángulos deseados (front, side, back, etc.)
    """
    try:
        # Validar tipos de archivo
        for image, name in [(person_image, "person"), (clothing_image, "clothing")]:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El archivo {name} debe ser una imagen válida"
                )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Leer imágenes
        person_data = await person_image.read()
        clothing_data = await clothing_image.read()
        
        # Parsear ángulos
        angle_list = [angle.strip() for angle in angles.split(',')]
        
        # Crear generador de superposición
        overlay_generator = await create_clothing_overlay()
        
        # Generar múltiples ángulos
        result = await overlay_generator.create_multiple_angles(
            person_data,
            clothing_data,
            person_image.content_type,
            clothing_image.content_type,
            angle_list
        )
        
        if result["success"]:
            # Convertir imágenes a base64
            processed_angles = {}
            for angle, images in result["angles"].items():
                processed_angles[angle] = []
                for img in images:
                    processed_angles[angle].append({
                        "data": base64.b64encode(img["data"]).decode('utf-8'),
                        "mime_type": img["mime_type"]
                    })
            
            return MultipleAnglesResponse(
                success=True,
                message=f"Generados {result['total_images']} ángulos exitosamente",
                angles=processed_angles,
                total_images=result["total_images"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generando múltiples ángulos"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando múltiples ángulos: {str(e)}"
        )


@app.post("/enhance-image", response_model=ImageEnhancementResponse)
async def enhance_image(
    image: UploadFile = File(..., description="Imagen a mejorar"),
    enhancement_type: str = Form("realistic", description="Tipo de mejora (realistic, professional, natural)")
):
    """
    Mejora una imagen para mayor realismo o calidad.
    
    - **image**: Imagen a mejorar
    - **enhancement_type**: Tipo de mejora deseada
    """
    try:
        # Validar tipo de archivo
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen válida"
            )
        
        # Verificar API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GEMINI_API_KEY o GOOGLE_API_KEY no está configurada"
            )
        
        # Leer imagen
        image_data = await image.read()
        
        # Crear generador de superposición
        overlay_generator = await create_clothing_overlay()
        
        # Mejorar imagen
        result = await overlay_generator.enhance_try_on_result(
            image_data,
            image.content_type,
            enhancement_type
        )
        
        if result["success"]:
            # Convertir imágenes a base64
            enhanced_images = []
            for img in result["enhanced_images"]:
                enhanced_images.append({
                    "data": base64.b64encode(img["data"]).decode('utf-8'),
                    "mime_type": img["mime_type"]
                })
            
            return ImageEnhancementResponse(
                success=True,
                message="Imagen mejorada exitosamente",
                enhanced_images=enhanced_images,
                enhancement_type=enhancement_type
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error mejorando imagen")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error mejorando imagen: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
