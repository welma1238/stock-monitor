import os
import cv2
import yt_dlp
import time
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import pytz  # 確保 requirements.txt 有這項，否則會 ModuleNotFoundError

# --- 設定區 ---
# 請在 Railway 的 Variables 設定這兩個數值
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 妳指定的測試網址
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s"

def get_live_stream_url(youtube_url):
    """
    使用 yt-dlp 繞過網頁偵測，直接取得影像流
    這能解決妳之前遇到的驗證碼問題
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 取得串流失敗 (可能需要 Cookies): {e}")
            return None

def process_and_ocr(frame):
    """
    對應妳提供的單機參數 (y=1020) 進行優化
    """
    h, w = frame.shape[:2]
    
    # 計算裁剪區域：目標是下方的黃色新聞跑馬燈
    #
