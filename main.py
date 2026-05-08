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
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except: pass

def process_and_ocr(frame):
    h, w = frame.shape[:2]
    # 裁剪底部跑馬燈
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    crop_img = frame[y_start:y_end, x_start:x_end]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 💡 移除啟動宣告，避免洗版
    print("🚀 啟動中...")

    # 改用 streamlink 作為後端，這對直播更友善
    options = {
        "STREAM_RESOLUTION": "720p", # 稍微調降解析度提升成功率
        "STREAM_BACKEND": "streamlink", 
    }
    
    stream = None
    try:
        stream = CamGear(source=YT_URL, stream_mode=True, logging=True, **options).start()
        send_to_tg("✅ 機器人已成功連線，開始掃描新聞！")
        
        while True:
            frame = stream.read()
            if frame is None: break
            
            news_img, current_text = process_and_ocr(frame)
            if len(current_text) >= 5 and current_text != last_news:
                now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                cv2.imwrite("news.png", news_img)
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open("news.png", "rb") as photo:
                    requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": f"🔔 {now_str}\n{current_text}"}, files={"photo": photo})
                last_news = current_text
            
            time.sleep(30)
            
    except Exception as e:
        print(f"🔥 錯誤: {e}")
        time.sleep(60) # 出錯時等一分鐘再重試，避免洗版
    finally:
        if stream: stream.stop()

if __name__ == "__main__":
    run_monitor()
