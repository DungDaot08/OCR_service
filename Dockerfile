# Base image
FROM python:3.11-slim

# Cài Tesseract OCR + poppler-utils (cho pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Set Tesseract data path nếu cần
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Chạy FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
