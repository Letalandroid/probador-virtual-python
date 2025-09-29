"""
Módulo para superposición de prendas sobre imágenes de personas usando Gemini AI.
"""
import os
import base64
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types
import json


class ClothingOverlay:
    """Clase para superponer prendas sobre imágenes de personas."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el generador de superposición de prendas.
        
        Args:
            api_key: Clave API de Google Gemini
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-image-preview"
    
    async def create_virtual_try_on(self, 
                                  person_image: bytes, 
                                  clothing_image: bytes,
                                  person_mime: str,
                                  clothing_mime: str,
                                  clothing_type: str = "shirt",
                                  style_preferences: Optional[Dict] = None) -> Dict:
        """
        Crea una imagen de la persona con la prenda superpuesta.
        
        Args:
            person_image: Imagen de la persona
            clothing_image: Imagen de la prenda
            person_mime: MIME type de la imagen de la persona
            clothing_mime: MIME type de la imagen de la prenda
            clothing_type: Tipo de prenda (shirt, dress, jacket, etc.)
            style_preferences: Preferencias de estilo opcionales
            
        Returns:
            Dict con la imagen resultante y metadatos
        """
        # Crear prompt específico para el tipo de prenda
        prompt = self._create_try_on_prompt(clothing_type, style_preferences)
        
        contents = [
            types.Part(
                inline_data=types.Blob(
                    data=person_image,
                    mime_type=person_mime
                )
            ),
            types.Part(
                inline_data=types.Blob(
                    data=clothing_image,
                    mime_type=clothing_mime
                )
            ),
            types.Part.from_text(text=prompt)
        ]
        
        # Configurar generación
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=0.3,
        )
        
        try:
            # Generar imagen
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            
            # Procesar respuesta
            return await self._process_try_on_response(stream)
            
        except Exception as e:
            print(f"Error en virtual try-on: {e}")
            return {
                "success": False,
                "error": str(e),
                "generated_image": None,
                "metadata": {}
            }
    
    def _create_try_on_prompt(self, clothing_type: str, style_preferences: Optional[Dict]) -> str:
        """Crea un prompt específico para el tipo de prenda."""
        
        base_prompts = {
            "shirt": """
            Superpone esta prenda (camisa/camiseta) sobre la persona de manera realista.
            Asegúrate de que:
            - La prenda se ajuste naturalmente al cuerpo de la persona
            - Los pliegues y sombras se vean realistas
            - El color y textura de la prenda se mantengan
            - La pose y proporciones de la persona se conserven
            - La iluminación sea consistente
            """,
            "dress": """
            Superpone este vestido sobre la persona de manera elegante y realista.
            Asegúrate de que:
            - El vestido se ajuste perfectamente a la silueta de la persona
            - Los pliegues y caída del vestido se vean naturales
            - El color y textura se mantengan fieles al original
            - La pose de la persona sea apropiada para el vestido
            - La iluminación resalte los detalles del vestido
            """,
            "jacket": """
            Superpone esta chaqueta/abrigo sobre la persona de manera realista.
            Asegúrate de que:
            - La chaqueta se ajuste correctamente a los hombros y torso
            - Los botones, cremalleras y detalles se vean claramente
            - El material y textura se mantengan auténticos
            - La pose permita mostrar bien la chaqueta
            - Las sombras y pliegues sean realistas
            """,
            "pants": """
            Superpone estos pantalones sobre la persona de manera natural.
            Asegúrate de que:
            - Los pantalones se ajusten correctamente a la cintura y piernas
            - La caída y pliegues se vean realistas
            - El color y textura se mantengan
            - La pose permita mostrar bien los pantalones
            - Las proporciones sean correctas
            """,
            "sweater": """
            Superpone este suéter sobre la persona de manera cómoda y realista.
            Asegúrate de que:
            - El suéter se ajuste bien al torso y brazos
            - La textura del tejido se vea auténtica
            - Los pliegues y arrugas sean naturales
            - El color se mantenga fiel al original
            - La pose sea relajada y natural
            """
        }
        
        base_prompt = base_prompts.get(clothing_type, base_prompts["shirt"])
        
        # Agregar preferencias de estilo si se proporcionan
        if style_preferences:
            style_additions = []
            
            if style_preferences.get("fit"):
                style_additions.append(f"El ajuste debe ser {style_preferences['fit']}")
            
            if style_preferences.get("occasion"):
                style_additions.append(f"Para ocasión {style_preferences['occasion']}")
            
            if style_preferences.get("mood"):
                style_additions.append(f"Con un estilo {style_preferences['mood']}")
            
            if style_additions:
                base_prompt += "\n\nRequisitos adicionales:\n" + "\n".join(f"- {req}" for req in style_additions)
        
        return base_prompt
    
    async def _process_try_on_response(self, stream) -> Dict:
        """Procesa la respuesta del stream de try-on."""
        generated_images = []
        metadata = {}
        text_output = ""
        
        for chunk in stream:
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            for part in chunk.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    # Guardar imagen generada
                    generated_images.append({
                        "data": part.inline_data.data,
                        "mime_type": part.inline_data.mime_type
                    })
                elif part.text:
                    text_output += part.text
        
        # Procesar metadatos del texto
        try:
            if text_output:
                # Intentar extraer JSON del texto
                json_start = text_output.find('{')
                json_end = text_output.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = text_output[json_start:json_end]
                    metadata = json.loads(json_str)
                else:
                    metadata = {"description": text_output}
        except json.JSONDecodeError:
            metadata = {"description": text_output}
        
        return {
            "success": len(generated_images) > 0,
            "generated_images": generated_images,
            "metadata": metadata,
            "text_output": text_output
        }
    
    async def create_multiple_angles(self, 
                                   person_image: bytes,
                                   clothing_image: bytes,
                                   person_mime: str,
                                   clothing_mime: str,
                                   angles: List[str] = None) -> Dict:
        """
        Crea múltiples ángulos de la persona con la prenda.
        
        Args:
            person_image: Imagen de la persona
            clothing_image: Imagen de la prenda
            person_mime: MIME type de la imagen de la persona
            clothing_mime: MIME type de la imagen de la prenda
            angles: Lista de ángulos deseados (front, side, back, etc.)
            
        Returns:
            Dict con imágenes de múltiples ángulos
        """
        if angles is None:
            angles = ["front", "side", "back"]
        
        results = {}
        
        for angle in angles:
            prompt = f"""
            Crea una vista {angle} de la persona con esta prenda superpuesta.
            Asegúrate de que:
            - La pose sea apropiada para mostrar la prenda desde el ángulo {angle}
            - La prenda se vea natural y bien ajustada
            - Los detalles de la prenda sean visibles desde este ángulo
            - La iluminación sea consistente y realista
            """
            
            contents = [
                types.Part(
                    inline_data=types.Blob(
                        data=person_image,
                        mime_type=person_mime
                    )
                ),
                types.Part(
                    inline_data=types.Blob(
                        data=clothing_image,
                        mime_type=clothing_mime
                    )
                ),
                types.Part.from_text(text=prompt)
            ]
            
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                temperature=0.3,
            )
            
            try:
                stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                
                angle_images = []
                for chunk in stream:
                    if (
                        chunk.candidates is None
                        or chunk.candidates[0].content is None
                        or chunk.candidates[0].content.parts is None
                    ):
                        continue

                    for part in chunk.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            angle_images.append({
                                "data": part.inline_data.data,
                                "mime_type": part.inline_data.mime_type
                            })
                
                results[angle] = angle_images
                
            except Exception as e:
                print(f"Error generando ángulo {angle}: {e}")
                results[angle] = []
        
        return {
            "success": any(results.values()),
            "angles": results,
            "total_images": sum(len(imgs) for imgs in results.values())
        }
    
    async def enhance_try_on_result(self, 
                                  try_on_image: bytes,
                                  mime_type: str,
                                  enhancement_type: str = "realistic") -> Dict:
        """
        Mejora el resultado del try-on para mayor realismo.
        
        Args:
            try_on_image: Imagen resultante del try-on
            mime_type: MIME type de la imagen
            enhancement_type: Tipo de mejora (realistic, professional, etc.)
            
        Returns:
            Dict con la imagen mejorada
        """
        enhancement_prompts = {
            "realistic": """
            Mejora esta imagen para que se vea más realista y profesional.
            Ajusta la iluminación, sombras, texturas y colores para que parezca una foto de estudio.
            """,
            "professional": """
            Convierte esta imagen en una fotografía profesional de moda.
            Mejora la iluminación, composición y calidad general.
            """,
            "natural": """
            Haz que esta imagen se vea más natural y espontánea.
            Ajusta la iluminación y colores para que parezca una foto casual.
            """
        }
        
        prompt = enhancement_prompts.get(enhancement_type, enhancement_prompts["realistic"])
        
        contents = [
            types.Part(
                inline_data=types.Blob(
                    data=try_on_image,
                    mime_type=mime_type
                )
            ),
            types.Part.from_text(text=prompt)
        ]
        
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            temperature=0.2,
        )
        
        try:
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            
            enhanced_images = []
            for chunk in stream:
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                for part in chunk.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        enhanced_images.append({
                            "data": part.inline_data.data,
                            "mime_type": part.inline_data.mime_type
                        })
            
            return {
                "success": len(enhanced_images) > 0,
                "enhanced_images": enhanced_images,
                "enhancement_type": enhancement_type
            }
            
        except Exception as e:
            print(f"Error en mejora de imagen: {e}")
            return {
                "success": False,
                "error": str(e),
                "enhanced_images": []
            }


async def create_clothing_overlay() -> ClothingOverlay:
    """Factory function para crear un generador de superposición de prendas."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY o GOOGLE_API_KEY no está configurada")
    
    return ClothingOverlay(api_key)
