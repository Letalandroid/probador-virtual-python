FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar archivos de configuración
COPY pyproject.toml uv.lock ./

# Instalar dependencias
RUN uv sync --frozen

# Copiar código fuente
COPY src/ ./src/
COPY images/ ./images/
COPY run_api.py ./

# Crear directorio de salida
RUN mkdir -p output

# Exponer puerto
EXPOSE 8000

# Variables de entorno por defecto
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RELOAD=false

# Comando por defecto
CMD ["python", "run_api.py"]
