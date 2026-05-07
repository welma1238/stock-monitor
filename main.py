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

# 1. 環境變數設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s&autoplay=1"

# 定義一個統一的非同步發送函數，確保 100% 執行
async def send_to_tg(bot, chat_id, photo_path=None, text=None):
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=text)
        elif text:
            await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"發送 TG 失敗: {e}")

def run_task():
    print("🚀 啟動初始化程序...")
    time.sleep(10) 
    
    global TG_TOKEN
    if not TG_TOKEN: TG_TOKEN = os.getenv("TG_TOKEN")
    if not TG_TOKEN: return

    tz = pytz.timezone('Asia/Taipei')
    bot = Bot(token=TG_TOKEN)
    
    # 發送啟動通知
    asyncio.run(send_to_tg(bot, TG_CHAT_ID, text="🤖 診斷模式已修正重啟！\n每 3 分鐘我會嘗試傳送一張截圖。"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"開啟測試頻道: {YT_URL}")
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

                # --- 修正點：使用統一的發送函數並用 asyncio.run 包裹 ---
                if count % 3 == 0:
                    asyncio.run(send_to_tg(bot, TG_CHAT_ID, photo_path=img_path, text=f"📸 定期畫面檢查\n長度: {len(text_found)}"))
                    print(f"[{current_time}] 已執行診斷截圖發送指令")

                msg_type = ""
                if "最新" in text_found: msg_type = "🚩 【最新消息】"
                elif "獨家" in text_found: msg_type = "🔥 【獨家消息】"

                if msg_type:
                    tags = []
                    code_match = re.search(r'(\d{4})', text_found)
                    if code_match: tags.append(f"#{code_match.group(1)}")
                    tag_str = " ".join(tags)
                    caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"
                    asyncio.run(send_to_tg(bot, TG_CHAT_ID, photo_path=img_path, text=caption))

            except Exception as e:
                print(f"執行錯誤: {e}")
            
            time.sleep(60) 

if __name__ == "__main__":
    run_task()
