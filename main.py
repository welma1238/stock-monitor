import os
import cv2
import time
import requests
import pytesseract
from datetime import datetime
import pytz
import streamlink

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
    # 針對直播畫面的跑馬燈區域裁剪
    y_start, y_end = int(h * 0.93), int(h * 0.98)
    x_start, x_end = int(w * 0.05), int(w * 0.95)
    crop_img = frame[y_start:y_end, x_start:x_end]
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return crop_img, text.strip()

def get_stream_url(url):
    """使用 streamlink 獲取最穩定的串流連結"""
    try:
        streams = streamlink.streams(url)
        if "720p" in streams:
            return streams["720p"].url
        elif "best" in streams:
            return streams["best"].url
    except Exception as e:
        print(f"❌ 獲取串流失敗: {e}")
    return None

def run_monitor():
    tw_tz = pytz.timezone('Asia/Taipei')
    last_news = ""
    print("🚀 啟動監控程式...")
    
    while True:
        try:
            real_url = get_stream_url(YT_URL)
            if not real_url:
                print("⚠️ 無法取得串流，冷靜 5 分鐘後重試...")
                time.sleep(300) # 💡 遇到 429 錯誤時強制休息，避免被封 IP
                continue

            cap = cv2.VideoCapture(real_url)
            # 成功啟動後才發一次通知
            send_to_tg("✅ 監控已重新連線，目前一切正常。")

            while True:
                success, frame = cap.read()
                if not success: break

                news_img, current_text = process_and_ocr(frame)
                if len(current_text) >= 5 and current_text != last_news:
                    now_str = datetime.now(tw_tz).strftime("%H:%M:%S")
                    cv2.imwrite("news.png", news_img)
                    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                    with open("news.png", "rb") as photo:
                        requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": f"🔔 {now_str}\n{current_text}"}, files={"photo": photo})
                    last_news = current_text
                
                time.sleep(30) # 每 30 秒掃描一次
            
            cap.release()
        except Exception as e:
            print(f"🔥 異常中斷: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_monitor()
