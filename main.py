import os
import time
import asyncio
import re
from telegram import Bot
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 環境變數與設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=WMT8VRPX-sM" 

def run_task():
    tz = pytz.timezone('Asia/Taipei')
    print(f"[{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}] 啟動監控任務...")
    bot = Bot(token=TG_TOKEN)

    # 啟動通知
    try:
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 股票監控機器人已上線 (08:45-13:30)"))
    except: pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        page.goto(YT_URL, timeout=60000)
        time.sleep(15) 

        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            
            # 1. 時間判斷邏輯 (08:45 - 13:30)
            if "08:45" <= current_time <= "13:30":
                screenshot_path = "live_temp.png"
                page.screenshot(path=screenshot_path)
                
                # 2. OCR 辨識 (繁體中文)
                # 針對黃色區塊位置進行裁切優化 (範例坐標，可依畫面調整)
                img = Image.open(screenshot_path)
                # 這裡建議針對妳觀察到的黃色標籤位置進行 crop，辨識率會更高
                text = pytesseract.image_to_string(img, lang='chi_tra')

                # 3. 條件判斷：最新消息 vs 獨家消息
                msg_type = ""
                if "最新消息" in text:
                    msg_type = "🚩 【最新消息】"
                elif "獨家消息" in text:
                    msg_type = "🔥 【獨家消息】"

                if msg_type:
                    # 4. 進階辨識：股票名稱與代碼 (正則表達式尋找 4 位數字)
                    stock_tags = ""
                    match = re.search(r'(\d{4})', text)
                    if match:
                        stock_tags = f"\n#{match.group(1)}"

                    # 5. 組裝訊息並推播
                    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    caption = f"{msg_type}\n⏰ 時間：{time_str}{stock_tags}"
                    
                    try:
                        with open(screenshot_path, 'rb') as photo:
                            asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=caption))
                        print(f"已推播：{msg_type} {stock_tags}")
                    except Exception as e:
                        print(f"推播失敗: {e}")

                time.sleep(60) # 盤中每分鐘檢查
            else:
                print(f"[{current_time}] 非監控時段，休息中...")
                time.sleep(600) # 盤後每 10 分鐘檢查一次

if __name__ == "__main__":
    run_task()
