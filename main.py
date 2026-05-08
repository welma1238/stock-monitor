import os
import cv2
import yt_dlp
import time
import requests
import pytesseract
from PIL import Image
from datetime import datetime
import pytz

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# 請務必確認這個直播網址是「公開」且正在直播的
YT_URL = "https://www.youtube.com/watch?v=oB2QY06L5Ew&t=896s"

def get_live_stream_url(youtube_url):
    """強化版的串流網址獲取"""
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # 模擬瀏覽器特徵，減少 Private video 誤判
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
        except Exception as e:
            print(f"❌ 解析失敗: {e}")
            return None

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
        print(f"❌ TG 發送失敗: {e}")

def run_monitor():
    tz = pytz.timezone('Asia/Taipei')
    print("🚀 啟動強化版串流解析監控...")
    # 啟動時先發一個訊息確認連線
    send_to_tg_sync(text="🤖 監控機器人已上線！正在嘗試連接直播串流...")
    
    while True:
        try:
            stream_url = get_live_stream_url(YT_URL)
            
            if stream_url:
                cap = cv2.VideoCapture(stream_url)
                # 設定讀取逾時，避免卡死
                cap.set(cv2.CAP_PROP_TIMEOUT_MS, 10000)
                success, frame = cap.read()
                
                if success:
                    img_path = "stream_snap.png"
                    cv2.imwrite(img_path, frame)
                    
                    text_found = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra')
                    now_str = datetime.now(tz).strftime("%H:%M:%S")
                    print(f"[{now_str}] 畫面抓取成功")

                    if "最新" in text_found or "獨家" in text_found:
                        send_to_tg_sync(text=f"🚩 偵測到重大消息 ({now_str})", photo_path=img_path)
                    
                    # 每 10 分鐘強制回報一次畫面確認沒黑屏
                    if datetime.now(tz).minute % 10 == 0:
                        send_to_tg_sync(text=f"📊 串流狀態正常 ({now_str})", photo_path=img_path)
                else:
                    print("⚠️ 無法從串流讀取畫面")
                cap.release()
            else:
                print("⚠️ 無法取得串流網址，可能是地區限制或需要登入")
                
        except Exception as e:
            print(f"⚠️ 監控異常: {e}")
        
        time.sleep(60)

if __name__ == "__main__":
    run_monitor()
