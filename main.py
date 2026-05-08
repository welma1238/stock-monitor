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
    """
    優化 OCR 處理：強化對比度以利辨識黃底藍字
    """
    h, w = frame.shape[:2]
    # 針對 1080p 比例裁剪底部跑馬燈
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    
    crop_img = frame[y_start:y_end, x_start:x_end]
    
    # 轉灰階並使用 Otsu 二值化來自動抓取文字輪廓
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # OCR 辨識，設定為繁體中文，psm 7 代表處理單行文字
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    
    # 確保一啟動就發送通知
    send_to_tg(f"🚀 監控模式已優化！正在掃描股市跑馬燈...")

    options = {
        "STREAM_RESOLUTION": "best", 
        "STREAM_PARAMS": {"n_exploit": True}
    }
    
    try:
        # 啟動串流並給予 5 秒緩衝
        stream = CamGear(source=YT_URL, stream_mode=True, logging=True, **options).start()
        time.sleep(5)
        
        while True:
            frame = stream.read()
            if frame is None:
                print("⚠️ 讀取中斷，重新嘗試...")
                break
            
            news_img, current_text = process_and_ocr(frame)
            
            # 放寬門檻：只要有字且跟上次不同就發送，方便測試
            if len(current_text) >= 3 and current_text != last_news:
                now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                cv2.imwrite("news.png", news_img)
                
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                caption = f"🔔 【股市快報】{now_str}\n\n解析內容：\n{current_text}"
                
                with open("news.png", "rb") as photo:
                    requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption}, files={"photo": photo})
                
                last_news = current_text
                print(f"✅ 推送成功: {current_text}")
            
            # 每 20 秒檢查一次，提升即時感
            time.sleep(20)
            
    except Exception as e:
        send_to_tg(f"❌ 監控發生錯誤：{str(e)}")
    finally:
        if 'stream' in locals() and stream:
            stream.stop()

if __name__ == "__main__":
    while True:
        run_monitor()
        time.sleep(10)
    
