import time
import os
import pytz
from datetime import datetime
from playwright.sync_api import sync_playwright
import easyocr
from telegram import Bot

# 從環境變數讀取設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 這裡填入你的東森財經 YouTube 直播連結
YT_URL = "https://www.youtube.com/watch?v=AEBeWMM1atA" 

def run_task():
    print(f"[{datetime.now()}] 開始執行截圖任務...")
    
    # 步驟 1: 啟動瀏覽器截圖後立即關閉
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            page.goto(YT_URL, timeout=60000)
            time.sleep(15) # 給一點時間讓畫質變清晰
            page.screenshot(path="temp_full.jpg", quality=85)
            print("截圖成功，正在釋放瀏覽器記憶體...")
        except Exception as e:
            print(f"截圖失敗: {e}")
        finally:
            browser.close() # 關鍵：先關瀏覽器，把 300MB RAM 還給系統

    # 步驟 2: 瀏覽器關掉後，才啟動 OCR
    print("啟動 OCR 引擎...")
    reader = easyocr.Reader(['ch_tra', 'en'], gpu=False) # 確定不使用 GPU 節省開銷
    results = reader.readtext("temp_full.jpg", detail=0)
    full_text = "".join(results)
    
    print(f"識別內容: {full_text[:50]}...") # 打印前50個字看結果

    # 步驟 3: 判斷邏輯與推播
    if "最新" in full_text or "獨家" in full_text:
        print("偵測到關鍵字，準備發送 Telegram...")
        bot = Bot(token=TG_TOKEN)
        # 這裡建議用同步方式發送，簡單穩定
        with open("temp_full.jpg", "rb") as photo:
            bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=f"偵測到動態！\n時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 釋放 OCR 記憶體 (手動清理)
    del reader

# 簡單的循環，每 2 分鐘跑一次（避免過於頻繁導致崩潰）
while True:
    run_task()
    print("任務結束，休眠 120 秒...")
    time.sleep(120)
