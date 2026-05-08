import os
import cv2
import yt_dlp
import time
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import pytz # 處理日誌顯示缺失此套件的問題

# --- 設定區 ---
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew"

def get_live_stream_url(youtube_url):
    """
    修正 format 設定以解決 'Requested format is not available' 報錯
    並確保 cookies.txt 正常運作
    """
    ydl_opts = {
        # 修改這裡：使用更寬鬆的格式選擇，自動抓取最高畫質
        'format': 'best', 
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    # 自動偵測 cookies.txt
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("ℹ️ 成功載入 cookies.txt")
    else:
        print("⚠️ 提醒：未偵測到 cookies.txt，可能會遇到機器人驗證問題")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 取得串流失敗: {e}")
            return None

def process_and_ocr(frame):
    """
    精準對齊 Welma 的 1080p 裁剪參數 (y=1020)
    """
    h, w = frame.shape[:2]
    
    # 根據 613006060378128522.jpg 版面設定裁剪範圍
    y_start = int(h * 0.93) 
    y_end = int(h * 0.98)
    x_start = int(w * 0.05) 
    x_end = int(w * 0.95)

    crop_img = frame[y_start:y_end, x_start:x_end]
    
    # 影像增強提升 OCR 準確度
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY_INV)
    
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def send_to_tg_photo(text, photo_path):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            payload = {"chat_id": TG_CHAT_ID, "caption": text}
            files = {"photo": photo}
            requests.post(url, data=payload, files=files, timeout=20)
    except Exception as e:
        print(f"❌ TG 圖片傳送失敗: {e}")

def send_to_tg_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        payload = {"chat_id": TG_CHAT_ID, "text": text}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 啟動訊息失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    start_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    send_to_tg_msg(f"🚀 股市監控機器人(最終優化版)已上線！\n時間
