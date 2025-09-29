from pydantic import BaseModel, Field
from typing import List, Optional
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
