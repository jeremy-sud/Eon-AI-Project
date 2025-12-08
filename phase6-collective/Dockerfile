# Collective Mind Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias
RUN pip install numpy

# Copiar estructura necesaria (Fundamentos + Fase 6)
COPY phase1-foundations /app/phase1-foundations
COPY phase6-collective /app/phase6-collective

# Variables de entorno
ENV PYTHONPATH=/app/phase1-foundations/python
ENV PYTHONUNBUFFERED=1

# Ejecutar simulación
CMD ["python", "phase6-collective/collective_mind.py"]
