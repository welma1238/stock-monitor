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

def send_to_tg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)

def process_and_ocr(frame):
    h, w = frame.shape[:2]
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    crop_img = frame[y_start:y_end, x_start:x_end]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY_INV)
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 啟動時立刻發測試訊息
    send_to_tg(f"🤖 機器人正在啟動環境 (Node.js 已掛載)...")

    # 極簡化參數，讓它自己去抓能動的格式
    options = {
        "STREAM_RESOLUTION": "best", 
        "STREAM_PARAMS": {"n_exploit": True} # 加入針對 YouTube 加密的對策
    }
    
    try:
        stream = CamGear(source=YT_URL, stream_mode=True, logging=True, **options).start()
        send_to_tg("✅ 成功連線到直播網址！開始監控畫面...")
        
        while True:
            frame = stream.read()
            if frame is None: break
            
            news_img, current_text = process_and_ocr(frame)
            if len(current_text) > 5 and current_text != last_news:
                now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                cv2.imwrite("news.png", news_img)
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open("news.png", "rb") as photo:
                    requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": f"🔔 {now_str}\n{current_text}"}, files={"photo": photo})
                last_news = current_text
            time.sleep(30)
            
    except Exception as e:
        send_to_tg(f"❌ 嚴重錯誤報錯：{str(e)}")
    finally:
        if 'stream' in locals() and stream: stream.stop()

if __name__ == "__main__":
    run_monitor()
