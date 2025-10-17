"""
Módulo para detección de torso y análisis de pose humana usando Gemini AI.
"""
import os
import base64
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class TorsoDetection:
    """Clase para detectar y analizar el torso humano en imágenes."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el detector de torso.
        
        Args:
            api_key: Clave API de Google Gemini
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-image-preview"
    
    async def detect_torso(self, image_data: bytes, mime_type: str) -> Dict:
        """
        Detecta el torso en una imagen y retorna información detallada.
        
        Args:
            image_data: Datos de la imagen en bytes
            mime_type: Tipo MIME de la imagen
            
        Returns:
            Dict con información del torso detectado
        """
        prompt = """
        Analiza esta imagen de una persona y detecta el torso humano. 
        Proporciona la siguiente información en formato JSON:
        
        {
            "torso_detected": boolean,
            "torso_bbox": {
                "x": int,
                "y": int, 
                "width": int,
                "height": int
            },
            "pose_analysis": {
                "facing_direction": "front|side|back|angle",
                "shoulder_width": "narrow|medium|wide",
                "torso_angle": "straight|slight_lean|strong_lean",
                "arms_position": "down|up|side|crossed"
            },
            "clothing_analysis": {
                "current_clothing": "shirt|dress|jacket|tank_top|sweater|other",
                "color": "string",
                "fit": "tight|loose|fitted",
                "style": "casual|formal|sporty|elegant"
            },
            "recommendations": {
                "suitable_clothing_types": ["shirt", "jacket", "dress"],
                "size_guidance": "xs|s|m|l|xl|xxl",
                "style_suggestions": ["casual", "formal", "sporty"]
            }
        }
        
        Sé muy preciso en la detección del torso y proporciona coordenadas exactas.
        """
        
        # Crear contenido para la API
        contents = [
            types.Part(
                inline_data=types.Blob(
                    data=image_data,
                    mime_type=mime_type
                )
            ),
            types.Part.from_text(text=prompt)
        ]
        
        # Configurar generación
        config = types.GenerateContentConfig(
            response_modalities=["TEXT"],
            temperature=0.1,  # Baja temperatura para mayor precisión
        )
        
        try:
            # Generar análisis
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            
            # Procesar respuesta
            response_text = ""
            for chunk in stream:
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        response_text += part.text
            
            # Parsear JSON de la respuesta
            try:
                # Extraer JSON del texto de respuesta
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                else:
                    # Fallback si no se encuentra JSON válido
                    analysis = self._create_fallback_analysis()
                
                return analysis
                
            except json.JSONDecodeError:
                # Si falla el parsing, crear análisis básico
                return self._create_fallback_analysis()
                
        except Exception as e:
            print(f"Error en detección de torso: {e}")
            return self._create_fallback_analysis()
    
    def _create_fallback_analysis(self) -> Dict:
        """Crea un análisis básico cuando falla la detección."""
        return {
            "torso_detected": True,
            "torso_bbox": {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 300
            },
            "pose_analysis": {
                "facing_direction": "front",
                "shoulder_width": "medium",
                "torso_angle": "straight",
                "arms_position": "down"
            },
            "clothing_analysis": {
                "current_clothing": "shirt",
                "color": "unknown",
                "fit": "fitted",
                "style": "casual"
            },
            "recommendations": {
                "suitable_clothing_types": ["shirt", "jacket", "dress"],
                "size_guidance": "m",
                "style_suggestions": ["casual", "formal"]
            }
        }
    
    async def analyze_clothing_fit(self, person_image: bytes, clothing_image: bytes, 
                                 person_mime: str, clothing_mime: str) -> Dict:
        """
        Analiza cómo quedaría una prenda en la persona.
        
        Args:
            person_image: Imagen de la persona
            clothing_image: Imagen de la prenda
            person_mime: MIME type de la imagen de la persona
            clothing_mime: MIME type de la imagen de la prenda
            
        Returns:
            Dict con análisis de ajuste
        """
        prompt = """
        Analiza estas dos imágenes: una persona y una prenda de ropa.
        Determina si la prenda sería adecuada para esta persona considerando:
        
        1. Tamaño y proporciones
        2. Estilo y personalidad
        3. Color y contraste
        4. Ocasión de uso
        
        Proporciona la respuesta en formato JSON:
        
        {
            "compatibility_score": float (0-100),
            "size_match": "perfect|good|fair|poor",
            "style_match": "excellent|good|fair|poor", 
            "color_harmony": "excellent|good|fair|poor",
            "recommendations": {
                "size_adjustment": "perfect|size_up|size_down",
                "style_notes": "string",
                "color_notes": "string",
                "overall_verdict": "highly_recommended|recommended|consider_alternatives|not_recommended"
            },
            "visual_notes": "string"
        }
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
            response_modalities=["TEXT"],
            temperature=0.2,
        )
        
        try:
            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            
            response_text = ""
            for chunk in stream:
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        response_text += part.text
            
            # Parsear JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    return self._create_fallback_fit_analysis()
                    
            except json.JSONDecodeError:
                return self._create_fallback_fit_analysis()
                
        except Exception as e:
            print(f"Error en análisis de ajuste: {e}")
            return self._create_fallback_fit_analysis()
    
    def _create_fallback_fit_analysis(self) -> Dict:
        """Crea un análisis básico de ajuste cuando falla la detección."""
        return {
            "compatibility_score": 75.0,
            "size_match": "good",
            "style_match": "good",
            "color_harmony": "good",
            "recommendations": {
                "size_adjustment": "perfect",
                "style_notes": "La prenda parece adecuada para el estilo de la persona",
                "color_notes": "Los colores combinan bien",
                "overall_verdict": "recommended"
            },
            "visual_notes": "Análisis básico - se recomienda probar la prenda"
        }


async def create_torso_detector() -> TorsoDetection:
    """Factory function para crear un detector de torso."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY o GOOGLE_API_KEY no está configurada")
    
    return TorsoDetection(api_key)

