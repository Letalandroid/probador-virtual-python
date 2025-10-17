# Python AI API - Probador Virtual

Servicio de IA para probador virtual usando Google Gemini API.

## Características

- **Detección de torso**: Análisis de pose humana en imágenes
- **Superposición de prendas**: Aplicación virtual de ropa sobre personas
- **Mezcla de imágenes**: Generación de imágenes combinadas
- **Análisis de ajuste**: Evaluación de cómo se ve la ropa
- **Múltiples ángulos**: Generación de vistas desde diferentes perspectivas
- **Mejora de imágenes**: Optimización de calidad de imágenes

## Configuración Rápida

### 1. Instalar dependencias

```bash
# Con uv (recomendado)
uv sync

# O con pip
pip install -e .
```

### 2. Configurar variables de entorno

```bash
# Opción 1: Script automático
./setup-env.sh

# Opción 2: Manual
cp env.example .env
# Edita .env y agrega tu GEMINI_API_KEY
```

### 3. Obtener API key de Gemini

1. Visita: https://makersuite.google.com/app/apikey
2. Crea una nueva API key
3. Cópiala en el archivo `.env`:

```env
GEMINI_API_KEY=tu_api_key_aqui
```

### 4. Ejecutar el servidor

```bash
python3 run_api.py
```

El servidor estará disponible en: http://localhost:8000

## Uso con Docker

### Construir imagen

```bash
docker build -t probador-python-api .
```

### Ejecutar contenedor

```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=tu_api_key_aqui \
  probador-python-api
```

### Con Docker Compose

```bash
# Desde la raíz del proyecto
docker-compose up python-api
```

## API Endpoints

### Health Check
- **GET** `/health` - Estado del servicio

### Detección de Torso
- **POST** `/detect-torso` - Detectar torso en imagen

### Probador Virtual
- **POST** `/virtual-try-on` - Aplicar prenda virtualmente

### Análisis de Ajuste
- **POST** `/analyze-clothing-fit` - Analizar cómo se ve la ropa

### Múltiples Ángulos
- **POST** `/generate-multiple-angles` - Generar vistas desde diferentes ángulos

### Mejora de Imagen
- **POST** `/enhance-image` - Mejorar calidad de imagen

### Mezcla de Imágenes
- **POST** `/mix-images` - Combinar múltiples imágenes

## Documentación Interactiva

Una vez que el servidor esté ejecutándose, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Variables de Entorno

| Variable | Descripción | Requerida | Default |
|----------|-------------|-----------|---------|
| `GEMINI_API_KEY` | API key de Google Gemini | ✅ | - |
| `HOST` | Host del servidor | ❌ | 0.0.0.0 |
| `PORT` | Puerto del servidor | ❌ | 8000 |
| `RELOAD` | Recarga automática | ❌ | true |

## Estructura del Proyecto

```
python/
├── src/
│   ├── api.py              # API principal de FastAPI
│   ├── models.py           # Modelos de datos Pydantic
│   ├── torso_detection.py  # Detección de torso humano
│   ├── clothing_overlay.py # Superposición de prendas
│   └── mix_images.py       # Mezcla de imágenes
├── images/                 # Imágenes de ejemplo
├── generated_images/       # Imágenes generadas
├── output/                 # Imágenes de salida
├── tests/                  # Tests unitarios
├── Dockerfile             # Configuración Docker
├── pyproject.toml         # Dependencias Python
├── env.example            # Variables de entorno ejemplo
└── run_api.py            # Script de inicio
```

## Desarrollo

### Ejecutar tests

```bash
# Con uv
uv run pytest

# Con pip
pytest
```

### Modo desarrollo

```bash
# Con recarga automática
uv run uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Linting

```bash
# Verificar código
uv run ruff check src/

# Formatear código
uv run ruff format src/
```

## Troubleshooting

### Error: "GEMINI_API_KEY no está configurada"

1. Verifica que el archivo `.env` existe
2. Confirma que contiene `GEMINI_API_KEY=tu_api_key`
3. Reinicia el servidor

### Error de conexión a Gemini

1. Verifica que tu API key es válida
2. Confirma que tienes cuota disponible
3. Revisa la conectividad a internet

### Problemas con imágenes

1. Verifica que las imágenes están en formato soportado (JPEG, PNG)
2. Confirma que el tamaño no excede los límites
3. Revisa los permisos de escritura en directorios de salida

## Logs

Los logs se muestran en la consola. Para producción, considera usar un sistema de logging más robusto.

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Haz commit de tus cambios
4. Push a la rama
5. Abre un Pull Request

## Licencia

Ver archivo LICENSE para más detalles.