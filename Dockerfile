FROM python:3.10-slim

# 安裝系統必要套件 (修正 libgl1 名稱)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 瀏覽器及其依賴
RUN pip install playwright && playwright install chromium && playwright install-deps chromium

# 啟動指令
CMD ["python", "main.py"]
