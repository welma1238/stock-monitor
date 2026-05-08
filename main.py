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
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew"

def get_live_stream_url(youtube_url):
    """
    修正格式要求 (format)，並讀取 cookies.txt 以繞過機器人驗證
    """
    ydl_opts = {
        # 改為更廣泛的格式選擇，避免 'Requested format is not available'
        'format': 'bestvideo+bestaudio/best', 
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("ℹ️ 成功偵測並載入 cookies.txt")
    else:
        print("⚠️ 警告：目錄下找不到 cookies.txt")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 取得串流連結失敗: {e}")
            return None

def process_and_ocr(frame):
    """
    精準對齊 Welma 的 1080p 裁剪參數 (y=1020)
    並優化「黃底藍字」辨識效果
    """
    h, w = frame.shape[:2]
    
    # 針對東森財經新聞版面，精準切出下方黃色跑馬燈
    y_start = int(h * 0.93) 
    y_end = int(h * 0.98)
    x_start = int(w * 0.05) 
    x_end = int(w * 0.95)

    crop_img = frame[y_start:y_end, x_start:x_end]
    
    # 影像增強：轉灰階 -> 提高對比 -> 二值化反轉 (讓藍字變白底黑字)
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)
    
    # OCR 辨識：使用繁體中文 + 單行模式
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
        print(f"❌ TG 圖片發送失敗: {e}")

def send_to_tg_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        payload = {"chat_id": TG_CHAT_ID, "text": text}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 文字發送失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    start_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    send_to_tg_msg(f"🚀 監控機器人已修正格式錯誤，重新上線！\n啟動時間：{start_time}")
    
    while True:
        try:
            stream_url = get_live_stream_url(YT_URL)
            if not stream_url:
                time.sleep(60)
                continue

            cap = cv2.VideoCapture(stream_url)
            success, frame = cap.read()
            
            if success:
                news_img, current_text = process_and_ocr(frame)
                
                # 只有辨識到有意義的文字（>5字）且與上次不同才發送
                if len(current_text) > 5 and current_text != last_news:
                    now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                    img_path = "current_news.png"
                    cv2.imwrite(img_path, news_img)
                    
                    msg = f"🔔 【股市新聞速報】\n時間：{now_str}\n\n📝 解析內容：\n{current_text}"
                    send_to_tg_photo(msg, img_path)
                    
                    last_news = current_text
                    print(f"✅ 成功發送：{current_text}")
                
            cap.release()
        except Exception as e:
            print(f"⚠️ 循環運行異常：{e}")
        
        time.sleep(30) # 保持 30 秒抓取一次的頻率

if __name__ == "__main__":
    run_monitor()
