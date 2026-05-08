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
    使用最廣泛的格式請求，解決 Requested format is not available
    """
    ydl_opts = {
        # 改用這種寫法，會自動選擇最好的影片格式
        'format': 'bestvideo/best', 
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("ℹ️ 成功讀取 cookies.txt")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 串流抓取失敗: {e}")
            return None

def process_and_ocr(frame):
    """精準裁剪 1080p 跑馬燈"""
    h, w = frame.shape[:2]
    y_start = int(h * 0.93) 
    y_end = int(h * 0.98)
    x_start = int(w * 0.05) 
    x_end = int(w * 0.95)

    crop_img = frame[y_start:y_end, x_start:x_end]
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
            requests.post(url, data=payload, files=files)
    except Exception as e:
        print(f"❌ TG 傳圖失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    print("🚀 啟動監控...")
    
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
                if len(current_text) > 5 and current_text != last_news:
                    now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                    img_path = "news.png"
                    cv2.imwrite(img_path, news_img)
                    send_to_tg_photo(f"🔔 股市新聞 ({now_str})\n{current_text}", img_path)
                    last_news = current_text
            cap.release()
        except Exception as e:
            print(f"⚠️ 異常: {e}")
        time.sleep(30)

if __name__ == "__main__":
    run_monitor()
