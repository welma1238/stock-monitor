import os
import time
import re
import requests  # 改用 requests 確保 100% 同步發送
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 1. 環境變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s&autoplay=1"

# 2. 建立一個絕對不會出錯的同步發送函數
def send_to_tg_sync(text=None, photo_path=None):
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        print(f"✅ TG 發送成功: {text[:20]}...")
    except Exception as e:
        print(f"❌ TG 發送失敗: {e}")

def run_task():
    print("🚀 啟動初始化程序 (同步穩定版)...")
    time.sleep(5)
    
    tz = pytz.timezone('Asia/Taipei')
    send_to_tg_sync(text="🤖 同步發送模式啟動！\n我會每 3 分鐘強制傳送截圖。")

    with sync_playwright() as p:
        # 使用同步 Playwright
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"開啟頻道: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) 

        count = 0
        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            count += 1
            
            try:
                img_path = "scan.png"
                page.screenshot(path=img_path)
                
                # OCR 辨識
                text_found = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                print(f"[{current_time}] 掃描次數: {count}, 文字長度: {len(text_found)}")

                # 每 3 分鐘強制發送診斷圖
                if count % 3 == 0:
                    send_to_tg_sync(text=f"📸 定期畫面檢查\n偵測文字長度: {len(text_found)}", photo_path=img_path)

                # 關鍵字邏輯
                msg_type = ""
                if "最新" in text_found: msg_type = "🚩 【最新消息】"
                elif "獨家" in text_found: msg_type = "🔥 【獨家消息】"

                if msg_type:
                    tags = []
                    code_match = re.search(r'(\d{4})', text_found)
                    if code_match: tags.append(f"#{code_match.group(1)}")
                    tag_str = " ".join(tags)
                    caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"
                    send_to_tg_sync(text=caption, photo_path=img_path)

            except Exception as e:
                print(f"執行錯誤: {e}")
            
            time.sleep(60) 

if __name__ == "__main__":
    run_task()
