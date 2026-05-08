import os
import cv2  # OpenCV
import yt_dlp
import time
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import pytz

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=R2iMq5LKXco"

def get_live_stream_url(youtube_url):
    """使用 yt-dlp 獲取 m3u8 串流網址"""
    ydl_opts = {'format': 'best', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']

def send_to_tg_sync(text=None, photo_path=None):
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
    except Exception as e:
        print(f"❌ TG 發送失敗: {e}")

def run_monitor():
    tz = pytz.timezone('Asia/Taipei')
    send_to_tg_sync(text="🚀 模式切換：串流解析監控啟動！不再使用瀏覽器，直接分析影像流。")
    
    while True:
        try:
            # 1. 獲取串流網址
            stream_url = get_live_stream_url(YT_URL)
            
            # 2. 使用 OpenCV 開啟影像流
            cap = cv2.VideoCapture(stream_url)
            success, frame = cap.read()
            
            if success:
                img_path = "stream_snap.png"
                cv2.imwrite(img_path, frame) # 儲存當前畫面
                
                # 3. OCR 辨識
                text_found = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                now_str = datetime.now(tz).strftime("%H:%M")
                print(f"[{now_str}] 影像抓取成功，字數: {len(text_found)}")

                # 偵測邏輯
                if "最新" in text_found or "獨家" in text_found:
                    send_to_tg_sync(text=f"🚩 偵測到重大消息 ({now_str})", photo_path=img_path)
                
                # 每 10 分鐘傳一張確認畫面
                if datetime.now(tz).minute % 10 == 0:
                    send_to_tg_sync(text=f"📊 串流解析正常執行中...", photo_path=img_path)

            cap.release()
        except Exception as e:
            print(f"⚠️ 監控異常: {e}")
            time.sleep(10)
        
        time.sleep(60) # 每分鐘執行一次

if __name__ == "__main__":
    run_monitor()
