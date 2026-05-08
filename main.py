import os
import time
import re
import requests
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 換一個直播連結試試看，有時候特定影片會有更嚴格的限制
YT_URL = "https://www.youtube.com/watch?v=cDxN3VW3Xrw"

def send_to_tg_sync(text=None, photo_path=None):
    try:
        if photo_path:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": photo})
        else:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        print(f"✅ TG 發送成功")
    except Exception as e:
        print(f"❌ 發送異常: {e}")

def run_task():
    print("🚀 啟動突破偵測穩定版...")
    time.sleep(5)
    tz = pytz.timezone('Asia/Taipei')
    send_to_tg_sync(text="🤖 偽裝模式啟動！正在嘗試最後一次突破 YouTube 偵測...")

    with sync_playwright() as p:
        # 關鍵：設定更像真人的 User-Agent
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        context = browser.new_context(viewport={'width': 1280, 'height': 720}, user_agent=user_agent)
        page = context.new_page()
        
        print(f"進入頻道: {YT_URL}")
        # 加上 referer 讓它看起來是從 Google 搜尋來的
        page.goto(YT_URL, wait_until="networkidle", timeout=90000)
        time.sleep(15) 

        # 處理同意按鈕 (如果有的話)
        try:
            for btn_name in ["Accept all", "全部接受", "我同意", "Agree"]:
                btn = page.get_by_role("button", name=btn_name)
                if btn.is_visible():
                    btn.click()
                    time.sleep(5)
                    break
        except: pass

        # 嘗試模擬捲動與點擊播放
        try:
            page.evaluate("window.scrollTo(0, 200)")
            time.sleep(2)
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
                text_found = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                print(f"[{current_time}] 掃描 #{count}, 字數: {len(text_found)}")

                if count % 3 == 0:
                    send_to_tg_sync(text=f"📸 畫面檢查\n長度: {len(text_found)}\n(如果還是黑框或登入頁，請明早直接換正式直播連結試試)", photo_path=img_path)

                if "最新" in text_found or "獨家" in text_found:
                    code_match = re.search(r'(\d{4})', text_found)
                    tag = f" #{code_match.group(1)}" if code_match else ""
                    caption = f"🚩 偵測到新聞\n⏰ 時間：{now.strftime('%H:%M:%S')}{tag}"
                    send_to_tg_sync(text=caption, photo_path=img_path)

            except Exception as e:
                print(f"掃描錯誤: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_task()
