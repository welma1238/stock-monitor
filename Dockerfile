# 使用 Python 3.10 輕量版
FROM python:3.10-slim

# 安裝系統依賴
# 1. 將 libgl1-mesa-glx 改為 libgl1 以修正報錯
# 2. 加入 nodejs 解決 yt-dlp 缺失 JavaScript 執行環境的問題
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1 \
    libglib2.0-0 \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 Python 套件 (確保包含 pytz)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
