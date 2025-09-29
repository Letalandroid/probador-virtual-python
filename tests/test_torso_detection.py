import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.torso_detection import TorsoDetection


class TestTorsoDetection:
    @pytest.fixture
    def torso_detector(self):
        return TorsoDetection("mock-api-key")

    @pytest.fixture
    def mock_image_data(self):
        return b"fake-image-data"

    @pytest.fixture
    def mock_mime_type(self):
        return "image/jpeg"

    @pytest.mark.asyncio
    async def test_detect_torso_success(self, torso_detector, mock_image_data, mock_mime_type):
        """Test successful torso detection"""
        mock_response = {
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
                "color": "blue",
                "fit": "fitted",
                "style": "casual"
            },
            "recommendations": {
                "suitable_clothing_types": ["shirt", "jacket"],
                "size_guidance": "m",
                "style_suggestions": ["casual", "formal"]
            }
        }

        with patch.object(torso_detector.client.models, 'generate_content_stream') as mock_stream:
            # Mock the stream response
            mock_chunk = Mock()
            mock_chunk.candidates = [Mock()]
            mock_chunk.candidates[0].content = Mock()
            mock_chunk.candidates[0].content.parts = [Mock()]
            mock_chunk.candidates[0].content.parts[0].text = f'{{"torso_detected": true, "torso_bbox": {{"x": 100, "y": 100, "width": 200, "height": 300}}, "pose_analysis": {{"facing_direction": "front", "shoulder_width": "medium", "torso_angle": "straight", "arms_position": "down"}}, "clothing_analysis": {{"current_clothing": "shirt", "color": "blue", "fit": "fitted", "style": "casual"}}, "recommendations": {{"suitable_clothing_types": ["shirt", "jacket"], "size_guidance": "m", "style_suggestions": ["casual", "formal"]}}}}'
            
            mock_stream.return_value = [mock_chunk]

            result = await torso_detector.detect_torso(mock_image_data, mock_mime_type)

            assert result["torso_detected"] is True
            assert "torso_bbox" in result
            assert "pose_analysis" in result
            assert "clothing_analysis" in result
            assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_detect_torso_fallback(self, torso_detector, mock_image_data, mock_mime_type):
        """Test fallback when API fails"""
        with patch.object(torso_detector.client.models, 'generate_content_stream') as mock_stream:
            mock_stream.side_effect = Exception("API Error")

            result = await torso_detector.detect_torso(mock_image_data, mock_mime_type)

            assert result["torso_detected"] is True  # Fallback should return True
            assert "torso_bbox" in result
            assert "pose_analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_clothing_fit_success(self, torso_detector, mock_image_data, mock_mime_type):
        """Test successful clothing fit analysis"""
        mock_response = {
            "compatibility_score": 85.0,
            "size_match": "good",
            "style_match": "excellent",
            "color_harmony": "good",
            "recommendations": {
                "size_adjustment": "perfect",
                "style_notes": "Great match",
                "color_notes": "Colors complement well",
                "overall_verdict": "highly_recommended"
            },
            "visual_notes": "The clothing fits well"
        }

        with patch.object(torso_detector.client.models, 'generate_content_stream') as mock_stream:
            mock_chunk = Mock()
            mock_chunk.candidates = [Mock()]
            mock_chunk.candidates[0].content = Mock()
            mock_chunk.candidates[0].content.parts = [Mock()]
            mock_chunk.candidates[0].content.parts[0].text = '{"compatibility_score": 85.0, "size_match": "good", "style_match": "excellent", "color_harmony": "good", "recommendations": {"size_adjustment": "perfect", "style_notes": "Great match", "color_notes": "Colors complement well", "overall_verdict": "highly_recommended"}, "visual_notes": "The clothing fits well"}'
            
            mock_stream.return_value = [mock_chunk]

            result = await torso_detector.analyze_clothing_fit(
                mock_image_data, mock_image_data, mock_mime_type, mock_mime_type
            )

            assert result["compatibility_score"] == 85.0
            assert result["size_match"] == "good"
            assert result["style_match"] == "excellent"
            assert result["recommendations"]["overall_verdict"] == "highly_recommended"

    @pytest.mark.asyncio
    async def test_analyze_clothing_fit_fallback(self, torso_detector, mock_image_data, mock_mime_type):
        """Test fallback when clothing fit analysis fails"""
        with patch.object(torso_detector.client.models, 'generate_content_stream') as mock_stream:
            mock_stream.side_effect = Exception("API Error")

            result = await torso_detector.analyze_clothing_fit(
                mock_image_data, mock_image_data, mock_mime_type, mock_mime_type
            )

            assert result["compatibility_score"] == 75.0  # Fallback value
            assert result["size_match"] == "good"
            assert result["recommendations"]["overall_verdict"] == "recommended"
