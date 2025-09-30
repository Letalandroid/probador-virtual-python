import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.clothing_overlay import ClothingOverlay


class TestClothingOverlay:
    @pytest.fixture
    def overlay_generator(self):
        return ClothingOverlay("mock-api-key")

    @pytest.fixture
    def mock_image_data(self):
        return b"fake-image-data"

    @pytest.fixture
    def mock_mime_type(self):
        return "image/jpeg"

    @pytest.mark.asyncio
    async def test_create_virtual_try_on_success(self, overlay_generator, mock_image_data, mock_mime_type):
        """Test successful virtual try-on generation"""
        mock_response = {
            "success": True,
            "generated_images": [
                {
                    "data": b"fake-generated-image",
                    "mime_type": "image/png"
                }
            ],
            "metadata": {
                "processing_time": "2.5s",
                "quality": "high"
            }
        }

        with patch.object(overlay_generator.client.models, 'generate_content_stream') as mock_stream:
            # Mock the stream response
            mock_chunk = Mock()
            mock_chunk.candidates = [Mock()]
            mock_chunk.candidates[0].content = Mock()
            mock_chunk.candidates[0].content.parts = [Mock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = Mock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = b"fake-generated-image"
            mock_chunk.candidates[0].content.parts[0].inline_data.mime_type = "image/png"
            
            mock_stream.return_value = [mock_chunk]

            result = await overlay_generator.create_virtual_try_on(
                mock_image_data, mock_image_data, mock_mime_type, mock_mime_type, "shirt"
            )

            assert result["success"] is True
            assert len(result["generated_images"]) == 1
            assert result["generated_images"][0]["data"] == b"fake-generated-image"
            assert result["generated_images"][0]["mime_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_create_virtual_try_on_error(self, overlay_generator, mock_image_data, mock_mime_type):
        """Test error handling in virtual try-on"""
        with patch.object(overlay_generator.client.models, 'generate_content_stream') as mock_stream:
            mock_stream.side_effect = Exception("API Error")

            result = await overlay_generator.create_virtual_try_on(
                mock_image_data, mock_image_data, mock_mime_type, mock_mime_type, "shirt"
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_create_multiple_angles_success(self, overlay_generator, mock_image_data, mock_mime_type):
        """Test successful multiple angles generation"""
        angles = ["front", "side", "back"]
        
        with patch.object(overlay_generator.client.models, 'generate_content_stream') as mock_stream:
            # Mock different responses for different angles
            mock_chunk = Mock()
            mock_chunk.candidates = [Mock()]
            mock_chunk.candidates[0].content = Mock()
            mock_chunk.candidates[0].content.parts = [Mock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = Mock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = b"fake-angle-image"
            mock_chunk.candidates[0].content.parts[0].inline_data.mime_type = "image/png"
            
            mock_stream.return_value = [mock_chunk]

            result = await overlay_generator.create_multiple_angles(
                mock_image_data, mock_image_data, mock_mime_type, mock_mime_type, angles
            )

            assert result["success"] is True
            assert "angles" in result
            assert len(result["angles"]) == 3
            assert all(angle in result["angles"] for angle in angles)

    @pytest.mark.asyncio
    async def test_enhance_try_on_result_success(self, overlay_generator, mock_image_data, mock_mime_type):
        """Test successful image enhancement"""
        with patch.object(overlay_generator.client.models, 'generate_content_stream') as mock_stream:
            mock_chunk = Mock()
            mock_chunk.candidates = [Mock()]
            mock_chunk.candidates[0].content = Mock()
            mock_chunk.candidates[0].content.parts = [Mock()]
            mock_chunk.candidates[0].content.parts[0].inline_data = Mock()
            mock_chunk.candidates[0].content.parts[0].inline_data.data = b"fake-enhanced-image"
            mock_chunk.candidates[0].content.parts[0].inline_data.mime_type = "image/png"
            
            mock_stream.return_value = [mock_chunk]

            result = await overlay_generator.enhance_try_on_result(
                mock_image_data, mock_mime_type, "realistic"
            )

            assert result["success"] is True
            assert len(result["enhanced_images"]) == 1
            assert result["enhancement_type"] == "realistic"

    def test_create_try_on_prompt(self, overlay_generator):
        """Test prompt creation for different clothing types"""
        # Test shirt prompt
        prompt = overlay_generator._create_try_on_prompt("shirt", None)
        assert "camisa" in prompt.lower() or "shirt" in prompt.lower()
        assert "ajuste" in prompt.lower() or "fit" in prompt.lower()

        # Test dress prompt
        prompt = overlay_generator._create_try_on_prompt("dress", None)
        assert "vestido" in prompt.lower() or "dress" in prompt.lower()

        # Test jacket prompt
        prompt = overlay_generator._create_try_on_prompt("jacket", None)
        assert "chaqueta" in prompt.lower() or "jacket" in prompt.lower()

        # Test with style preferences
        style_prefs = {
            "fit": "slim",
            "occasion": "formal",
            "mood": "elegant"
        }
        prompt = overlay_generator._create_try_on_prompt("shirt", style_prefs)
        assert "slim" in prompt.lower()
        assert "formal" in prompt.lower()
        assert "elegant" in prompt.lower()


