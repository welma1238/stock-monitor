# 使用 Python 3.10 輕量版
FROM python:3.10-slim

# 1. 安裝系統依賴：Tesseract OCR、繁體中文包、以及 OpenCV 所需的影像庫
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 設定工作目錄
WORKDIR /app

# 3. 安裝 Python 套件
# 確保妳的 requirements.txt 包含: yt-dlp, opencv-python-headless, pytesseract, requests, Pillow, pytz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼
COPY . .

# 5. 啟動程式
CMD ["python", "main.py"]
