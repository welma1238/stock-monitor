import os
import time
import asyncio
from telegram import Bot
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 從環境變數讀取設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def run_task():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動監控任務...")

    # --- 1. 建立 Telegram Bot (使用最標準、不需要 HTTPXRequest 的寫法) ---
    bot = Bot(token=TG_TOKEN)
    
    try:
        # 直接嘗試發送訊息
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 機器人已在 Railway 順利啟動！"))
    except Exception as e:
        print(f"初始訊息發送失敗: {e}")

    # --- 2. 啟動瀏覽器監控 ---
    with sync_playwright() as p:
        print("正在啟動瀏覽器...")
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--mute-audio"]
        )
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print("正在進入直播間...")
        url = "https://www.youtube.com/watch?v=WMT8VRPX-sM" 
        page.goto(url)
        time.sleep(10) 
        
        print("監控運行中...")
        while True:
            # 這裡繼續你原本的截圖判斷邏輯
            time.sleep(60) 

        browser.close()

if __name__ == "__main__":
    run_task()
