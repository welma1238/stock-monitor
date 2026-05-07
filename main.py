import os
import time
import asyncio
from telegram import Bot
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 1. 從 Railway 的 Variables 讀取設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 妳的 YouTube 直播網址
YT_URL = "https://www.youtube.com/watch?v=WMT8VRPX-sM"

def run_task():
    # 設定台灣時區
    tz = pytz.timezone('Asia/Taipei')
    print(f"[{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}] 啟動監控任務...")

    # --- 第一步：建立 Telegram Bot 並發送啟動通知 ---
    # 使用 asyncio.run 確保在非同步模式下成功發送
    bot = Bot(token=TG_TOKEN)
    try:
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 機器人已在 Railway 順利啟動並開始監控！"))
    except Exception as e:
        print(f"發送啟動訊息失敗: {e}")

    # --- 第二步：啟動瀏覽器進行監控 ---
    with sync_playwright() as p:
        print("正在啟動瀏覽器...")
        # 使用合併後的參數，確保在雲端容器內不會崩潰
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--mute-audio"]
        )
        
        # 設定視窗解析度為 1080p
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            print(f"正在進入直播間: {YT_URL}")
            page.goto(YT_URL, timeout=60000)
            time.sleep(15)  # 等待 15 秒確保畫面載入完成
            
            print("開始循環監控邏輯...")
            while True:
                # 這裡放入妳原本的 OCR 辨識與截圖邏輯
                # 例如：截圖 -> OCR -> 判斷黃色區塊 -> 傳送 TG
                
                # 目前為了測試穩定性，我們設定每 60 秒循環一次
                time.sleep(60)
                
        except Exception as e:
            print(f"執行監控時發生錯誤: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_task()
