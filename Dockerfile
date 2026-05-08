FROM python:3.10-slim

# 安裝 Tesseract, Node.js (破解 YouTube 加密用) 和 OpenCV 函式庫
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1 \
    libglib2.0-0 \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
# 強制更新 yt-dlp 到最新版
RUN pip install --no-cache-dir -r requirements.txt && pip install -U yt-dlp

CMD ["python", "main.py"]
