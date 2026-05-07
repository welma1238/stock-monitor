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
# 從 Railway 系統抓取妳設定的變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s"

def run_task():
    # --- 診斷步驟 1：延遲啟動 ---
    # 避免容器剛啟動時環境變數尚未完全載入
    print("等待系統環境初始化 (10秒)...")
    time.sleep(10) 
    
    # --- 診斷步驟 2：變數檢查 ---
    global TG_TOKEN
    if not TG_TOKEN:
        # 如果變數是空的，嘗試重新抓取一次
        TG_TOKEN = os.getenv("TG_TOKEN")
        
    if not TG_TOKEN:
        print("❌ 關鍵錯誤：找不到環境變數 TG_TOKEN，請檢查 Railway 設定。")
        return
    else:
        print(f"✅ 環境變數偵測成功，Token 長度為: {len(TG_TOKEN)}")

    tz = pytz.timezone('Asia/Taipei')
    
    # 初始化機器人
    try:
        bot = Bot(token=TG_TOKEN)
        # 測試連線
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 監控守衛已上線！\n目前的記憶體狀態非常健康。"))
        print("機器人初始化成功並已發送測試訊息。")
    except Exception as e:
        print(f"❌ 機器人啟動失敗: {e}")
        return

    # 預設監控名單 (Welma 妳之後可以在這裡補上妳關注的股票)
    stock_map = {"台積電": "2330", "鴻海": "2317", "聯發科": "2454", "廣達": "2382"}

    with sync_playwright() as p:
        # 關鍵優化：資源極小化設定
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process", "--mute-audio"]
        )
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"開始瀏覽直播: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) 

        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            
            # 3. 監控時段判斷 (08:45 ~ 13:30)
            if "08:45" <= current_time <= "13:30":
                try:
                    img_path = "scan.png"
                    page.screenshot(path=img_path)
                    
                    # 4. OCR 辨識
                    text = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')

                    # 5. 消息類型判定
                    msg_type = ""
                    if "最新消息" in text:
                        msg_type = "🚩 【最新消息】"
                    elif "獨家消息" in text:
                        msg_type = "🔥 【獨家消息】"

                    if msg_type:
                        tags = []
                        # 找 4 位數代碼
                        code_match = re.search(r'(\d{4})', text)
                        if code_match: tags.append(f"#{code_match.group(1)}")
                        
                        # 從名單找股票名稱
                        for name, code in stock_map.items():
                            if name in text:
                                if f"#{name}" not in tags: tags.append(f"#{name}")
                                if f"#{code}" not in tags: tags.append(f"#{code}")
                        
                        tag_str = " ".join(tags)
                        caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"

                        with open(img_path, 'rb') as photo:
                            asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=caption))
                        print(f"已發送推播: {tag_str}")

                except Exception as e:
                    print(f"執行中錯誤: {e}")
                
                time.sleep(60) 
            else:
                # 盤後休眠模式，節省額度
                print(f"[{current_time}] 非交易時段，監控休眠中...")
                time.sleep(600)

if __name__ == "__main__":
    run_task()
