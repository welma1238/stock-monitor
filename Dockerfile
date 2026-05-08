FROM python:3.9-slim

# 安裝 Tesseract OCR 和 OpenCV 必備的系統函式庫 (修正 libgl1 報錯)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
