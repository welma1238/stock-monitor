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
# 使用妳提供的測試連結
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s&autoplay=1"

def run_task():
    print("等待系統環境初始化 (10秒)...")
    time.sleep(10) 
    
    global TG_TOKEN
    if not TG_TOKEN:
        TG_TOKEN = os.getenv("TG_TOKEN")
        
    if not TG_TOKEN:
        print("❌ 關鍵錯誤：找不到環境變數 TG_TOKEN")
        return

    tz = pytz.timezone('Asia/Taipei')
    
    try:
        bot = Bot(token=TG_TOKEN)
        asyncio.run(bot.send_message(chat_id=TG_CHAT_ID, text="🚀 測試模式已啟動！\n正在掃描東森新聞測試連結..."))
        print("✅ 機器人連線成功")
    except Exception as e:
        print(f"❌ 機器人啟動失敗: {e}")
        return

    # 監控名單 (妳可以視測試畫面內容增減)
    stock_map = {"台積電": "2330", "鴻海": "2317", "聯發科": "2454", "廣達": "2382", "中興電": "1513"}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process", "--mute-audio"]
        )
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        print(f"進入直播間: {YT_URL}")
        page.goto(YT_URL, timeout=90000)
        time.sleep(15) # 等待頁面加載

        # --- 處理 YouTube 遮擋與播放 ---
        try:
            # 嘗試點擊可能的 Cookie 同意按鈕
            if page.get_by_role("button", name="全部接受").is_visible():
                page.get_by_role("button", name="全部接受").click()
                print("已點擊同意條款")
            
            # 強制點擊畫面中央並按下播放鍵
            page.mouse.click(640, 360)
            page.keyboard.press("k")
            print("已發送播放指令")
        except:
            pass

        while True:
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")
            
            # 【測試模式】：暫時註解掉時段限制，讓妳現在就能測
            # if "08:45" <= current_time <= "13:30":
            if True: # 強制執行掃描
                try:
                    img_path = "scan.png"
                    # 截取影片主區域，避免邊欄干擾
                    page.screenshot(path=img_path)
                    
                    # OCR 辨識
                    text = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                    print(f"[{current_time}] 掃描中... 辨識到文字長度: {len(text)}")

                    # 只要偵測到「最新」或「獨家」就發送
                    msg_type = ""
                    if "最新" in text:
                        msg_type = "🚩 【最新消息】"
                    elif "獨家" in text:
                        msg_type = "🔥 【獨家消息】"

                    # 測試備案：如果一直沒抓到關鍵字，每 5 分鐘強制傳一張圖確認畫面
                    if now.minute % 5 == 0 and now.second < 60:
                        print("執行每五分鐘定時畫面檢查...")
                        # 這裡可以視需求決定要不要傳測試圖

                    if msg_type:
                        tags = []
                        # 找 4 位數代碼
                        code_match = re.search(r'(\d{4})', text)
                        if code_match: tags.append(f"#{code_match.group(1)}")
                        
                        # 匹配名單
                        for name, code in stock_map.items():
                            if name in text:
                                if f"#{name}" not in tags: tags.append(f"#{name}")
                                if f"#{code}" not in tags: tags.append(f"#{code}")
                        
                        tag_str = " ".join(tags)
                        caption = f"{msg_type}\n⏰ 時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n{tag_str}"

                        with open(img_path, 'rb') as photo:
                            asyncio.run(bot.send_photo(chat_id=TG_CHAT_ID, photo=photo, caption=caption))
                        print(f"🎯 已發送推播: {msg_type} {tag_str}")

                except Exception as e:
                    print(f"執行錯誤: {e}")
                
                time.sleep(60) 
            else:
                print(f"[{current_time}] 休息中...")
                time.sleep(600)

if __name__ == "__main__":
    run_task()
