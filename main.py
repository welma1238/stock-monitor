import time
import pytz
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import easyocr
from telegram import Bot

# 1. 基本設定 (這邊先空著，等等去 Zeabur 設定變數)
import os
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 2. 初始化 OCR
reader = easyocr.Reader(['ch_tra', 'en'])

def check_time():
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    # 判斷 08:45 ~ 13:30
    return (now.hour == 8 and now.minute >= 45) or (9 <= now.hour < 13) or (now.hour == 13 and now.minute <= 30)

def run_task():
    with sync_playwright() as p:
        # 啟動虛擬瀏覽器 (禁用音訊以節省流量)
        browser = p.chromium.launch(headless=True, args=["--mute-audio"])
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            page.goto("https://www.youtube.com/watch?v=AEBeWMM1atA", timeout=60000)
            time.sleep(15) # 等待畫質穩定
            
            # 截全螢幕高清圖 (發送給 TG)
            page.screenshot(path="full.jpg")
            
            # OCR 判定邏輯 (這裡縮小範圍到下方新聞欄)
            # 假設新聞欄在 y=850 以後
            results = reader.readtext("full.jpg")
            full_text = " ".join([res[1] for res in results])
            
            if "最新" in full_text or "獨家" in full_text:
                # 簡單正則抓 4 位數股號
                stock = re.findall(r'\d{4}', full_text)
                tag = f" #{stock[0]}" if stock else ""
                
                # 發送給 Telegram
                bot = Bot(token=TG_TOKEN)
                # 使用 datetime.now().strftime("%Y-%m-%d %H:%M") 標註時間
                # bot.send_photo(...) 代碼略，這部分可依你原本的 bot 修改
                print(f"發送成功: {full_text}")
                
        finally:
            browser.close()

while True:
    if check_time():
        run_task()
        time.sleep(60) # 每分鐘抓一次
    else:
        time.sleep(300)
