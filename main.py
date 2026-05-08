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
# 請確保在 Railway 的 Variables 頁面中已設定這兩個環境變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 妳指定的測試直播網址
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew"

def get_live_stream_url(youtube_url):
    """
    透過 yt-dlp 取得直播影像流，避開網頁驗證碼
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
            print(f"❌ 取得串流連結失敗: {e}")
            return None

def process_and_ocr(frame):
    """
    針對 1920x1080 (y=1020) 的版面比例進行精準裁剪
    """
    h, w = frame.shape[:2]
    
    # 裁剪下方黃色標題區塊
    # 使用比例計算以適應雲端不同的解析度抓取
    y_start = int(h * 0.93) 
    y_end = int(h * 0.98)
    x_start = int(w * 0.05) 
    x_end = int(w * 0.95)

    crop_img = frame[y_start:y_end, x_start:x_end]
    
    # 影像增強處理：轉灰階並二值化，將黃底藍字轉為白底黑字
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # OCR 辨識 (繁體中文)
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    
    return crop_img, text.strip()

def send_to_tg_photo(text, photo_path):
    """傳送圖片與文字訊息"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            payload = {"chat_id": TG_CHAT_ID, "caption": text}
            files = {"photo": photo}
            requests.post(url, data=payload, files=files, timeout=15)
    except Exception as e:
        print(f"❌ TG 圖片發送失敗: {e}")

def send_to_tg_msg(text):
    """傳送純文字訊息 (用於啟動宣告)"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        payload = {"chat_id": TG_CHAT_ID, "text": text}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 文字發送失敗: {e}")

def run_monitor():
    # 設定台灣時區
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 1. 啟動宣告：讓妳知道機器人已經成功執行到這一行了
    start_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    send_to_tg_msg(f"🚀 股市新聞監控機器人已成功在 Railway 上線！\n啟動時間：{start_time}\n正在連接直播源...")
    
    print("🚀 啟動監控中...")

    while True:
        try:
            stream_url = get_live_stream_url(YT_URL)
            if not stream_url:
                print("⚠️ 無法取得串流，60 秒後重試...")
                time.sleep(60)
                continue

            cap = cv2.VideoCapture(stream_url)
            success, frame = cap.read()
            
            if success:
                news_img, current_text = process_and_ocr(frame)
                
                # 去重機制：辨識到文字且與上一次不同才發送
                if len(current_text) > 5 and current_text != last_news:
                    now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                    img_path = "current_news.png"
                    cv2.imwrite(img_path, news_img)
                    
                    msg = f"🔔 【股市新聞提醒】\n時間：{now_str}\n\n📝 解析內文：\n{current_text}"
                    send_to_tg_photo(msg, img_path)
                    
                    last_news = current_text
                    print(f"✅ 已發送新聞：{current_text}")
                
            cap.release()
        except Exception as e:
            print(f"⚠️ 運行異常：{e}")
        
        # 每 30 秒執行一次抓取
        time.sleep(30)

if __name__ == "__main__":
    run_monitor()
