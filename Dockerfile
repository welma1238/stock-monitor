# 使用 Python 3.10 輕量版
FROM python:3.10-slim

# 1. 安裝系統依賴
# 修正 libgl1-mesa-glx 缺失問題，改用 libgl1 並加入 nodejs 提供 yt-dlp 所需環境
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    libgl1 \
    libglib2.0-0 \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 設定工作目錄
WORKDIR /app

# 3. 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有程式碼
COPY . .

# 5. 啟動程式
CMD ["python", "main.py"]
