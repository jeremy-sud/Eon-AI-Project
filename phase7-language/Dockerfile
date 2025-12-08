# TinyLM v2 Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias
RUN pip install flask numpy

# Copiar estructura necesaria (Fundamentos + Fase 7)
COPY phase1-foundations /app/phase1-foundations
COPY phase7-language /app/phase7-language

# Variables de entorno
ENV PYTHONPATH=/app/phase1-foundations/python
ENV PYTHONUNBUFFERED=1

# Puerto
EXPOSE 5001

# Ejecutar servidor
CMD ["python", "phase7-language/server.py"]
