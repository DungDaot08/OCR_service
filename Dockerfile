FROM python:3.11-slim

# 1. Cài thư viện hệ thống
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set workdir
WORKDIR /app

# 3. Copy requirements và cài
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy toàn bộ source code
COPY . .

# 5. Chạy server FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
