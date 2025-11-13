import os
import subprocess
from pathlib import Path


def test_mix_images_cli_integration(tmp_path):
    # Define paths to actual image files
    image1_path = Path(__file__).parent.parent / "images" / "man.jpeg"
    image2_path = Path(__file__).parent.parent / "images" / "cap.jpeg"

    # Ensure the image files exist
    assert image1_path.exists()
    assert image2_path.exists()

    output_dir = tmp_path / "output"

    # Set the API key from the environment variable
    # This will cause the API call to succeed if the key is valid.
    # We are testing the script's end-to-end functionality.
    env = os.environ.copy()
    # No need to set GEMINI_API_KEY here, it should be present in the environment

    command = [
        "uv",
        "run",
        "python",
        "src/mix_images.py",
        "-i",
        str(image1_path),
        "-i",
        str(image2_path),
        # The prompt is now dynamically determined by the script based on the number of images.
        # This integration test primarily verifies successful execution and output file creation.
        # Direct assertion of the prompt sent to the GenAI model would require mocking the GenAI client.
        "--output-dir",
        str(output_dir),
    ]

    # Expect the command to succeed with a valid API key
    result = subprocess.run(
        command, capture_output=True, text=True, check=True, env=env
    )

    # Assert that the command succeeded (zero exit code)
    assert result.returncode == 0

    # Assert that the output directory was created by the script
    assert output_dir.is_dir()

    # Assert that at least one remixed image file was created
    assert any(f.name.startswith("remixed_image_") for f in output_dir.iterdir())
