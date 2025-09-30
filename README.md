# Nano Banana Python - Image Mixer API

Este proyecto demuestra cómo mezclar de 1 a 5 imágenes usando Google Generative AI a través de una API REST con FastAPI.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd nano-banana-python
    ```

2.  **Install dependencies using `uv`:**

    ```bash
    uv sync
    ```

3.  **Set your Google Gemini API Key:**
    Ensure you have your `GEMINI_API_KEY` or `GOOGLE_API_KEY` set as an environment variable.

    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    # OR
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```

## Uso de la API

### Iniciar el servidor

```bash
# Opción 1: Usar el script de inicio
python run_api.py

# Opción 2: Usar uvicorn directamente
uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# Opción 3: Usar Docker
docker build -t image-mixer-api .
docker run -p 8000:8000 -e GEMINI_API_KEY=tu_api_key image-mixer-api
```

El servidor estará disponible en `http://localhost:8000`

### Variables de entorno

- `GEMINI_API_KEY` o `GOOGLE_API_KEY`: Tu clave de API de Google Gemini (requerida)
- `HOST`: Host del servidor (por defecto: 0.0.0.0)
- `PORT`: Puerto del servidor (por defecto: 8000)
- `RELOAD`: Recargar automáticamente en desarrollo (por defecto: true)

### Documentación de la API

Una vez que el servidor esté ejecutándose, puedes acceder a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints disponibles

#### 1. Health Check
```bash
GET /health
```

#### 2. Mezclar imágenes
```bash
POST /mix-images
```

**Parámetros:**
- `images`: Lista de archivos de imagen (1-5 imágenes) - **requerido**
- `prompt`: Prompt personalizado para la mezcla - **opcional**
- `output_dir`: Directorio de salida - **opcional** (por defecto: "output")

### Ejemplos de uso

#### Ejemplo 1: Mejorar una imagen (prompt por defecto)

```bash
curl -X POST "http://localhost:8000/mix-images" \
  -F "images=@images/man.jpeg"
```

#### Ejemplo 2: Combinar dos imágenes (prompt por defecto)

```bash
curl -X POST "http://localhost:8000/mix-images" \
  -F "images=@images/man.jpeg" \
  -F "images=@images/cap.jpeg"
```

#### Ejemplo 3: Combinar múltiples imágenes con prompt personalizado

```bash
curl -X POST "http://localhost:8000/mix-images" \
  -F "images=@images/man.jpeg" \
  -F "images=@images/cap.jpeg" \
  -F "images=@images/soda.jpeg" \
  -F "prompt=Create a product advertisement with the man, cap, and soda."
```

#### Ejemplo 4: Especificar directorio de salida

```bash
curl -X POST "http://localhost:8000/mix-images" \
  -F "images=@images/man.jpeg" \
  -F "images=@images/cap.jpeg" \
  -F "prompt=Remix these two images." \
  -F "output_dir=my_custom_output"
```

### Uso con Python requests

```python
import requests

# Mezclar imágenes
files = [
    ('images', open('images/man.jpeg', 'rb')),
    ('images', open('images/cap.jpeg', 'rb'))
]
data = {
    'prompt': 'Create a professional product photo',
    'output_dir': 'output'
}

response = requests.post('http://localhost:8000/mix-images', files=files, data=data)
result = response.json()

print(f"Success: {result['success']}")
print(f"Generated files: {result['generated_files']}")
```

### Probar la API

Puedes usar el script de prueba incluido:

```bash
# Asegúrate de que la API esté ejecutándose en otra terminal
python test_api.py
```

## Uso del script original (CLI)

El script original de línea de comandos sigue disponible:

### Example 1: Improve a single image (default prompt)

```bash
uv run python src/mix_images.py -i images/man.jpeg
```

### Example 2: Combine two images (default prompt)

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg
```

### Example 3: Combine multiple images with a custom prompt

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg -i images/soda.jpeg --prompt "Create a product advertisement with the man, cap, and soda."
```

### Example 4: Specify Output Directory

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg --prompt "Remix these two images." --output-dir my_custom_output
```
