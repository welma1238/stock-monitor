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
    """裁剪底部跑馬燈"""
    h, w = frame.shape[:2]
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    
    crop_img = frame[y_start:y_end, x_start:x_end]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 155, 255, cv2.THRESH_BINARY_INV)
    
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def send_to_tg_msg(text):
    """發送純文字訊息"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"❌ TG 訊息發送失敗: {e}")

def send_to_tg_photo(text, photo_path):
    """發送圖片訊息"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo}, timeout=20)
    except Exception as e:
        print(f"❌ TG 傳圖失敗: {e}")

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 💡 啟動測試：程式一跑就先發訊息，確認 TG 通道正常
    start_time = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    send_to_tg_msg(f"🚀 監控機器人嘗試連線中...\n啟動時間：{start_time}")
    
    # 💡 簡化格式要求，避免 Requested format 報錯
    options = {
        "STREAM_RESOLUTION": "best", # 改為自動選擇最好畫質，不再強迫 1080p
        "STREAM_PARAMS": {"cookiefile": "cookies.txt"} if os.path.exists("cookies.txt") else {}
    }
    
    print("🚀 啟動 CamGear...")
    stream = None
    
    try:
        stream = CamGear(source=YT_URL, stream_mode=True, logging=True, **options).start()
        time.sleep(8) # 增加緩衝時間

        while True:
            frame = stream.read()
            if frame is None:
                print("⚠️ 畫面讀取空值，嘗試重新啟動串流...")
                break # 跳出內層迴圈觸發重新啟動

            news_img, current_text = process_and_ocr(frame)
            
            if len(current_text) > 5 and current_text != last_news:
                now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                cv2.imwrite("news.png", news_img)
                send_to_tg_photo(f"🔔 【股市快訊】{now_str}\n{current_text}", "news.png")
                last_news = current_text
            
            time.sleep(30)
    except Exception as e:
        send_to_tg_msg(f"❌ 機器人發生異常：{str(e)}")
        print(f"🔥 運行異常: {e}")
    finally:
        if stream:
            stream.stop()

if __name__ == "__main__":
    while True: # 外層大迴圈，崩潰了也會自動重啟
        run_monitor()
        time.sleep(60)
