# 使用 Python 作為基底
FROM python:3.10-slim

# 安裝系統依賴項目：包括 Tesseract 主程式與繁體中文包
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 接著才是安裝妳的 requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
