import os
import time
import re
import random
import requests
from playwright.sync_api import sync_playwright
from PIL import Image
import pytesseract
import pytz
from datetime import datetime

# 1. 環境變數
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 妳指定的特定直播網址
YT_URL = "https://www.youtube.com/watch?v=R2iMq5LKXco" 

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
    print("🚀 啟動深度偽裝模式，嘗試突破驗證碼...")
    tz = pytz.timezone('Asia/Taipei')
    
    with sync_playwright() as p:
        # A. 啟動參數：徹底隱藏自動化特徵
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox", 
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled", # 隱藏 webdriver 標記
            "--incognito" # 使用無痕模式減少追蹤
        ])
        
        # B. 設備模擬：設定為台灣常見的 Chrome 環境
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}, 
            user_agent=user_agent,
            locale="zh-TW",
            timezone_id="Asia/Taipei"
        )
        
        page = context.new_page()
        
        # C. 注入 JavaScript 抹除機器人指紋
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"進入 YouTube: {YT_URL}")
        # 模擬從 Google 搜尋點擊進來的效果
        page.goto(YT_URL, wait_until="domcontentloaded", timeout=90000)
        
        # D. 模擬真人等待與隨機點擊
        time.sleep(random.uniform(5, 10)) 

        try:
            # 嘗試點擊同意按鈕
            for btn_text in ["Accept all", "全部接受", "我同意", "Agree", "I'm not a robot"]:
                target = page.get_by_role("button", name=btn_text)
                if target.is_visible():
                    target.click()
                    print(f"已嘗試點擊: {btn_text}")
                    time.sleep(5)
                    break
        except: pass
