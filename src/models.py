from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class MixImagesResponse(BaseModel):
    """Response model for image mixing operation."""
    success: bool
    message: str
    generated_files: List[str] = Field(default_factory=list)
    text_output: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class TorsoDetectionResponse(BaseModel):
    """Response model for torso detection."""
    success: bool
    message: str
    analysis: Optional[Dict[str, Any]] = None


class VirtualTryOnResponse(BaseModel):
    """Response model for virtual try-on."""
    success: bool
    message: str
    generated_images: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ClothingFitAnalysisResponse(BaseModel):
    """Response model for clothing fit analysis."""
    success: bool
    message: str
    analysis: Optional[Dict[str, Any]] = None


class MultipleAnglesResponse(BaseModel):
    """Response model for multiple angles generation."""
    success: bool
    message: str
    angles: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    total_images: int = 0


class ImageEnhancementResponse(BaseModel):
    """Response model for image enhancement."""
    success: bool
    message: str
    enhanced_images: List[Dict[str, Any]] = Field(default_factory=list)
    enhancement_type: str = "realistic"
