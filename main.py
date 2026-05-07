import time
import os
import pytz
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import pytesseract
from PIL import Image
from telegram import Bot

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# --- 設定區 ---
# 這些變數會從 Render 的 Environment Variables 讀取
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 你的直播網址
YT_URL = "https://www.youtube.com/watch?v=AEBeWMM1atA" 

def run_task():
    # 取得台灣時間
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 啟動監控任務...")

    # 步驟 1: 啟動瀏覽器進行高清截圖
    # 使用接力賽模式：截圖完立即關閉瀏覽器，釋放記憶體給 OCR
    with sync_playwright() as p:
        print("正在啟動瀏覽器...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            print(f"正在進入直播間: {YT_URL}")
            page.goto(YT_URL, timeout=60000)
            
            # 給影片一點時間載入高清畫質
            print("等待畫面穩定中 (15秒)...")
            time.sleep(15) 
            
            # 截取全螢幕高清圖
            page.screenshot(path="temp_full.jpg", quality=90)
            print("截圖成功，關閉瀏覽器釋放資源。")
        except Exception as e:
            print(f"截圖過程發生錯誤: {e}")
            return # 發生錯誤就跳出，等待下一次循環
        finally:
            browser.close()

    # 步驟 2: 啟動輕量化 OCR (Tesseract)
    # Tesseract 比 EasyOCR 省下約 300MB 的記憶體
    try:
        print("啟動輕量 OCR 辨識...")
        # 讀取剛剛存下的圖片
        img = Image.open("temp_full.jpg")
        
        # 辨識繁體中文與英文
        full_text = pytesseract.image_to_string(img, lang='chi_tra+eng')
        # 清理掉多餘的換行符號方便判斷
        clean_text = full_text.replace('\n', '')
        
        print(f"辨識結果摘要: {clean_text[:50]}...")

        # 步驟 3: 判斷關鍵字邏輯
        # 判斷是否出現「最新」或「獨家」
        if "最新" in clean_text or "獨家" in clean_text:
            print("【觸發告警】偵測到關鍵消息！")
            
            # 進階功能：嘗試從文字中抓取 4 位數股票代碼
            stock_codes = re.findall(r'\d{4}', clean_text)
            hashtag = f"\n\n#{stock_codes[0]}" if stock_codes else ""
            
            # 設定標籤與時間
            label = "🔴 最新消息" if "最新" in clean_text else "🟠 獨家消息"
            current_time = now.strftime('%Y-%m-%d %H:%M:%S')
            
            # 推播至 Telegram
            print("發送 Telegram 推播中...")
            bot = Bot(token=TG_TOKEN)
            with open("temp_full.jpg", "rb") as photo:
                bot.send_photo(
                    chat_id=TG_CHAT_ID, 
                    photo=photo, 
                    caption=f"【{label}】\n時間：{current_time}\n內容摘要：{clean_text[:60]}...{hashtag}"
                )
            print("推播發送完成。")
        else:
            print("未偵測到目標關鍵字，繼續監控。")

    except Exception as e:
        print(f"OCR 或推播過程出錯: {e}")

# --- 主程式循環 ---
# 為了避免 Render 的 Free Plan 壓力太大，建議每 2 分鐘跑一次
while True:
    run_task()
    print("等待 120 秒後進行下次監控...\n")
    time.sleep(120)
