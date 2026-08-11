FROM python:3.11-slim

# Dependências de sistema para OCR (Tesseract em português + Poppler para
# converter páginas de PDF em imagem antes do OCR).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Diretórios de dados (podem virar um disco persistente no Render)
RUN mkdir -p uploads/rubricas uploads/fichas_modelo uploads/fichas_alunos exports

EXPOSE 8000

# O Render injeta a variável $PORT; localmente cai em 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
