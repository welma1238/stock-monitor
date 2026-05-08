import os
import cv2
import time
import requests
import pytesseract
from datetime import datetime
import pytz
from vidgear.gears import CamGear

# --- 設定區 ---
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew"

def process_and_ocr(frame):
    """裁剪底部跑馬燈新聞區塊"""
    h, w = frame.shape[:2]
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    
    crop_img = frame[y_start:y_end, x_start:x_end]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY_INV)
    
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def send_to_tg_photo(text, photo_path):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo}, timeout=20)
    except Exception as e:
        print(f"❌ TG 傳圖失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    print("🚀 啟動 CamGear 穩定監控模式...")

    # 使用 vidgear 的 CamGear 處理 YouTube 串流，這比原生 OpenCV 穩定得多
    options = {"STREAM_RESOLUTION": "1080p"}
    stream = CamGear(source=YT_URL, stream_mode=True, logging=True, **options).start()

    try:
        while True:
            frame = stream.read()
            if frame is None:
                print("⚠️ 讀取不到畫面，重試中...")
                time.sleep(5)
                continue

            news_img, current_text = process_and_ocr(frame)
            
            # 若內容改變且字數足夠，發送到 TG
            if len(current_text) > 5 and current_text != last_news:
                now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                cv2.imwrite("news.png", news_img)
                send_to_tg_photo(f"🔔 【股市快訊】{now_str}\n{current_text}", "news.png")
                last_news = current_text
                print(f"✅ 已推送：{current_text}")
            
            time.sleep(30)
    except Exception as e:
        print(f"🔥 運行異常: {e}")
    finally:
        stream.stop()

if __name__ == "__main__":
    run_monitor()
