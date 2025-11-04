# ---- Etapa base ----
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Instalar uv (gestor de dependencias rápido)
RUN pip install uv

# Copiar archivos de dependencias primero (para aprovechar la caché de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias (usa el lock si existe)
RUN uv sync --frozen || true

# 👇 Instalar manualmente librerías que tu código usa directamente
RUN pip install fastapi uvicorn python-dotenv google-genai python-multipart pydantic

# Copiar todo el código fuente
COPY . .

# Copiar archivo .env si existe
COPY env.example .env

# Crear usuario no root
RUN groupadd --gid 1001 pythonuser && \
    useradd --uid 1001 --gid pythonuser --shell /bin/bash --create-home pythonuser

# Crear carpeta de imágenes y dar permisos
RUN mkdir -p /app/generated_images && chown -R pythonuser:pythonuser /app/generated_images
RUN chmod 777 /app/generated_images

USER pythonuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de ejecución
CMD ["python3", "run_api.py"]
