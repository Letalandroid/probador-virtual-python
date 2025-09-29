import os
import mimetypes
import time
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types

from models import MixImagesResponse, HealthResponse, ErrorResponse

# Initialize FastAPI app
app = FastAPI(
    title="Image Mixer API",
    description="API para mezclar imágenes usando Google Generative AI",
    version="1.0.0"
)

MODEL_NAME = "gemini-2.5-flash-image-preview"


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Image Mixer API is running"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
