import os
import cv2
import yt_dlp
import time
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import pytz

# --- 設定區 ---
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 測試網址：東森財經直播回放
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew"

def get_live_stream_url(youtube_url):
    """繞過網頁偵測，直接取得影像流連結"""
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 取得串流失敗: {e}")
            return None

def process_and_ocr(frame):
    """
    影像優化核心：
    1. 裁剪出下方黃色新聞區 (依據 1280x720 比例設定)
    2. 灰階與二值化處理提升 OCR 準確度
    """
    # 裁剪座標：[y1:y2, x1:x2] -> 針對東森財經的黃色標題區
    # 這些數值可以根據實際畫面微調，目標是達到 news_140027.jpg 的純淨感
    h, w = frame.shape[:2]
    crop_img = frame[int(h*0.78):int(h*0.92), int(w*0.05):int(w*0.95)]
    
    # 轉灰階與增強對比 (二值化)
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    
    # 使用 Tesseract 辨識繁體中文
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 6')
    return crop_img, text.strip()

def send_to_tg(text, photo_path):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        payload = {"chat_id": TG_CHAT_ID, "caption": text}
        files = {"photo": photo}
        requests.post(url, data=payload, files=files)

def run_monitor():
    tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    print("🚀 股市監控機器人啟動...")

    while True:
        try:
            stream_url = get_live_stream_url(YT_URL)
            if not stream_url:
                time.sleep(60)
                continue

            cap = cv2.VideoCapture(stream_url)
            success, frame = cap.read()
            
            if success:
                # 處理影像並獲取文字
                news_img, current_text = process_and_ocr(frame)
                
                # 簡單去重：如果文字有變動且長度足夠才發送
                if len(current_text) > 5 and current_text != last_news:
                    now_str = datetime.now(tz).strftime("%H:%M:%S")
                    img_path = "current_news.png"
                    cv2.imwrite(img_path, news_img)
                    
                    msg = f"🔔 【股市新聞提醒】\n時間：{now_str}\n\n📝 解析內容：\n{current_text}"
                    send_to_tg(msg, img_path)
                    
                    last_news = current_text
                    print(f"✅ 已發送新消息: {current_text[:15]}...")
                
            cap.release()
        except Exception as e:
            print(f"⚠️ 運行異常: {e}")
        
        time.sleep(30) # 每 30 秒檢查一次

if __name__ == "__main__":
    run_monitor()
