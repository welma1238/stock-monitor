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
YT_URL = "https://www.youtube.com/watch?v=WMT8VRPX-sM"

def run_task():
    tz = pytz.timezone('Asia/Taipei')
    bot = Bot(token=TG_TOKEN)

    # 發送啟動成功訊息
    try:
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 資源優化版監控已啟動\n監控時段：08:45-13:30"))
    except: pass

    # 預設熱門股名單 (手動加入妳最關心的幾檔，避免讀取全台股導致記憶體崩潰)
    stock_map = {"台積電": "2330", "鴻海": "2317", "聯發科": "2454", "廣達": "2382"}

    with sync_playwright() as p:
        # 關鍵優化：限制單一進程，減少記憶體占用
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process", "--mute-audio"]
        )
        context = browser.new_context(viewport={'width': 1280, 'height': 720}) # 降低解析度以省記憶體
        page = context.new_page()
        
        print(f"進入直播間: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) 

        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            
            # 2. 監控時段判斷 (08:45 ~ 13:30)
            if "08:45" <= current_time <= "13:30":
                try:
                    img_path = "scan.png"
                    page.screenshot(path=img_path)
                    
                    # 3. OCR 辨識 (繁體中文)
                    text = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')

                    # 4. 判斷消息類型
                    msg_type = ""
                    if "最新消息" in text:
                        msg_type = "🚩 【最新消息】"
                    elif "獨家消息" in text:
                        msg_type = "🔥 【獨家消息】"

                    if msg_type:
                        tags = []
                        # 找代碼
                        code_match = re.search(r'(\d{4})', text)
                        if code_match: tags.append(f"#{code_match.group(1)}")
                        
                        # 找名稱 (實現 #台積電 功能)
                        for name, code in stock_map.items():
                            if name in text:
                                if f"#{name}" not in tags: tags.append(f"#{name}")
                                if f"#{code}" not in tags: tags.append(f"#{code}")
                        
                        tag_str = " ".join(tags)
                        caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"

                        with open(img_path, 'rb') as photo:
                            asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=caption))

                except Exception as e:
                    print(f"錯誤: {e}")
                
                time.sleep(60) 
            else:
                print(f"[{current_time}] 休息中...")
                time.sleep(600)

if __name__ == "__main__":
    run_task()
