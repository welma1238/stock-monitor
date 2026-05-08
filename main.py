import os
import time
import re
import requests
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 環境變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=R2iMq5LKXco" # 妳需要的特定直播連結

def send_to_tg_sync(text=None, photo_path=None):
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        print(f"✅ TG 發送成功")
    except Exception as e:
        print(f"❌ 發送異常: {e}")

def run_task():
    print("🚀 啟動 YouTube 深度突破模式...")
    tz = pytz.timezone('Asia/Taipei')
    
    with sync_playwright() as p:
        # 1. 啟動參數優化：隱藏自動化控制特徵
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox", 
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled" # 關鍵：隱藏被控制特徵
        ])
        
        # 2. 模擬高解析度真實裝置
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}, 
            user_agent=user_agent,
            locale="zh-TW",
            timezone_id="Asia/Taipei"
        )
        
        page = context.new_page()
        
        # 3. 執行 JS 腳本移除 navigator.webdriver 標記
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"嘗試進入 YouTube 直播: {YT_URL}")
        page.goto(YT_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(10)

        # 4. 隨機點擊處理 (模擬真人動作突破驗證)
        try:
            # 處理各種可能的同意按鈕
            for btn_text in ["Accept all", "全部接受", "我同意", "Agree"]:
                target = page.get_by_role("button", name=btn_text)
                if target.is_visible():
                    target.click()
                    print(f"點擊同意: {btn_text}")
                    time.sleep(5)
                    break
        except: pass

        count = 0
        while True:
            now = datetime.now(tz)
            count += 1
            try:
                # 截圖前先隨機移動滑鼠
                page.mouse.move(100, 100)
                
                img_path = "scan.png"
                page.screenshot(path=img_path)
                
                # 進行 OCR 辨識
                img = Image.open(img_path)
                text_found = pytesseract.image_to_string(img, lang='chi_tra')
                print(f"[{now.strftime('%H:%M')}] 掃描 #{count}, 字數: {len(text_found)}")

                # 定期回報畫面
                if count % 3 == 0:
                    send_to_tg_sync(text=f"📊 監控狀態回報\n字數：{len(text_found)}", photo_path=img_path)

                # 核心業務邏輯：關鍵字偵測
                if "最新" in text_found or "獨家" in text_found:
                    code_match = re.search(r'(\d{4})', text_found)
                    tag = f" #{code_match.group(1)}" if code_match else ""
                    caption = f"🚩 偵測到重大消息\n⏰ 時間：{now.strftime('%H:%M:%S')}{tag}"
                    send_to_tg_sync(text=caption, photo_path=img_path)

            except Exception as e:
                print(f"掃描錯誤: {e}")
            
            time.sleep(60)

if __name__ == "__main__":
    run_task()
