# 使用內建 Python 的穩定環境
FROM python:3.10-slim

# 安裝所有 Tesseract 和 影像處理需要的系統工具
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 安裝瀏覽器
RUN pip install playwright && playwright install chromium && playwright install-deps chromium

# 執行你的腳本
CMD ["python", "main.py"]
