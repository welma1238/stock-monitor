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
    優化格式選擇邏輯，解決 'Requested format is not available'
    """
    ydl_opts = {
        # 使用更明確的格式偏好：優先抓取 1080p(95) 或 720p(94)，若無則抓取最佳可用
        'format': '95/94/best', 
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    # 載入妳上傳的 cookies.txt 以跳過機器人檢查
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = 'cookies.txt'
        print("ℹ️ 已成功套用 cookies.txt 憑證")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 串流解析失敗: {e}")
            return None

def process_and_ocr(frame):
    """
    維持妳要求的 1080p 下 y=1020 精準裁剪參數
    """
    h, w = frame.shape[:2]
    
    # 裁剪底部新聞跑馬燈區塊
    y_start = int(h * 0.93) 
    y_end = int(h * 0.98)
    x_start = int(w * 0.05) 
    x_end = int(w * 0.95)

    crop_img = frame[y_start:y_end, x_start:x_end]
    
    # 影像增強：轉灰階 -> 二值化反轉，提升對黃底藍字的辨識力
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY_INV)
    
    # OCR 辨識 (繁體中文)
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    
    return crop_img, text.strip()

def send_to_tg_photo(text, photo_path):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            payload = {"chat_id": TG_CHAT_ID, "caption": text}
            files = {"photo": photo}
            requests.post(url, data=payload, files=files, timeout=25)
    except Exception as e:
        print(f"❌ TG 圖片發送失敗: {e}")

def send_to_tg_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        payload = {"chat_id": TG_CHAT_ID, "text": text}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 啟動宣告發送失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 啟動成功宣告
    start_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    send_to_tg_msg(f"🚀 股市監控機器人已修正串流格式，重新上線！\n時間：{start_time}")
    
    print("🚀 監控流程啟動中...")

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
                
                # 去重機制：文字長度 > 5 且與上次內容不同才推送
                if len(current_text) > 5 and current_text != last_news:
                    now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                    img_path = "current_news.png"
                    cv2.imwrite(img_path, news_img)
                    
                    msg = f"🔔 【股市新聞速報】\n時間：{now_str}\n\n📝 內容解析：\n{current_text}"
                    send_to_tg_photo(msg, img_path)
                    
                    last_news = current_text
                    print(f"✅ 已推送最新新聞：{current_text}")
                
            cap.release()
        except Exception as e:
            print(f"⚠️ 運行中發生錯誤: {e}")
        
        # 每 30 秒執行一次
        time.sleep(30)

if __name__ == "__main__":
    run_monitor()
