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

def run_task():
    print("🚀 啟動初始化程序...")
    time.sleep(10) 
    
    global TG_TOKEN
    if not TG_TOKEN: TG_TOKEN = os.getenv("TG_TOKEN")
    if not TG_TOKEN: return

    tz = pytz.timezone('Asia/Taipei')
    bot = Bot(token=TG_TOKEN)
    asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🤖 診斷模式啟動！\n我會每 3 分鐘傳送一次截圖，確保監控畫面正常。"))

    with sync_playwright() as p:
        # 優化瀏覽器啟動參數
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"開啟測試頻道: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) 

        # 處理播放狀態
        try:
            page.mouse.click(640, 360)
            page.keyboard.press("k")
        except: pass

        count = 0
        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            count += 1
            
            try:
                img_path = "scan.png"
                page.screenshot(path=img_path)
                
                # OCR 辨識
                text = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                print(f"[{current_time}] 掃描次數: {count}, 辨識文字長度: {len(text)}")

                # --- 診斷邏輯：每 3 次掃描(約3分鐘)強制傳一張圖 ---
                if count % 3 == 0:
                    with open(img_path, 'rb') as photo:
                        asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=f"📸 定期畫面檢查\n偵測文字長度: {len(text)}"))

                # --- 原有新聞偵測邏輯 ---
                msg_type = ""
                if "最新" in text: msg_type = "🚩 【最新消息】"
                elif "獨家" in text: msg_type = "🔥 【獨家消息】"

                if msg_type:
                    tags = []
                    code_match = re.search(r'(\d{4})', text)
                    if code_match: tags.append(f"#{code_match.group(1)}")
                    
                    tag_str = " ".join(tags)
                    caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"
                    with open(img_path, 'rb') as photo:
                        asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=caption))
                    print(f"🎯 成功抓取新聞: {tag_str}")

            except Exception as e:
                print(f"執行錯誤: {e}")
            
            time.sleep(60) 

if __name__ == "__main__":
    run_task()
