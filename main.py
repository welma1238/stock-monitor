import os
import time
import re
import requests  # 確保 requirements.txt 中有加入 requests
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 1. 環境變數設定
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 目前使用妳提供的東森新聞測試連結
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s&autoplay=1"

# 2. 同步發送函數 (解決 coroutine was never awaited 報錯)
def send_to_tg_sync(text=None, photo_path=None):
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                res = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        
        if res.status_code == 200:
            print(f"✅ TG 發送成功")
        else:
            print(f"❌ TG 發送失敗: {res.text}")
    except Exception as e:
        print(f"❌ 發送異常: {e}")

def run_task():
    print("🚀 啟動同步穩定版監控程序...")
    time.sleep(5)
    
    tz = pytz.timezone('Asia/Taipei')
    send_to_tg_sync(text="🤖 最終穩定版已上線！\n正在嘗試突破 YouTube 同意頁面並傳送截圖...")

    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio"])
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"進入頻道: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) # 給頁面多一點載入時間

        # --- 突破 YouTube 同意頁面 (針對 截圖 2026-05-08 00.01.10.jpg 的修正) ---
        try:
            # 嘗試點擊英文或中文的同意按鈕
            for btn_name in ["Accept all", "全部接受", "我同意"]:
                btn = page.get_by_role("button", name=btn_name)
                if btn.is_visible():
                    btn.click()
                    print(f"✅ 已點擊 {btn_name} 按鈕")
                    time.sleep(10)
                    break
        except Exception as e:
            print(f"處理同意頁面時發生小提醒: {e}")

        # 嘗試點擊畫面並播放
        try:
            page.mouse.click(640, 360)
            page.keyboard.press("k")
        except:
            pass

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

                # 每 3 次掃描(約3分鐘)強制傳一張圖給妳確認畫面
                if count % 3 == 0:
                    send_to_tg_sync(text=f"📸 定期畫面檢查\n偵測文字長度: {len(text_found)}", photo_path=img_path)

                # 新聞偵測邏輯
                msg_type = ""
                if "最新" in text_found: msg_type = "🚩 【最新消息】"
                elif "獨家" in text_found: msg_type = "🔥 【獨家消息】"

                if msg_type:
                    # 簡單的正則表達式尋找四位數股票代碼
                    code_match = re.search(r'(\d{4})', text_found)
                    tag = f" #{code_match.group(1)}" if code_match else ""
                    
                    caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}{tag}"
                    send_to_tg_sync(text=caption, photo_path=img_path)

            except Exception as e:
                print(f"執行掃描錯誤: {e}")
            
            time.sleep(60) # 每分鐘掃描一次

if __name__ == "__main__":
    run_task()
