import cv2
import yt_dlp
import pytesseract

# 1. 使用 yt-dlp 取得直播的 m3u8 網址
def get_live_url(youtube_url):
    ydl_opts = {'format': 'best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']

# 2. 影像處理與 OCR
def process_frame(frame):
    # 裁剪區域 (根據妳的需求調整座標，目標是下方的黃色新聞區)
    # 假設畫面 1280x720，裁剪下方約 580-680 行
    roi = frame[580:680, 50:1230] 
    
    # 轉灰階並二值化，提升 Tesseract 辨識率
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # OCR 辨識 (指定繁體中文)
    text = pytesseract.image_to_string(thresh, lang='chi_tra', config='--psm 7')
    return roi, text.strip()

# 實作測試
youtube_url = "https://www.youtube.com/watch?v=oB2QY06L5Ew"
live_m3u8 = get_live_url(youtube_url)

cap = cv2.VideoCapture(live_m3u8)
ret, frame = cap.read()
if ret:
    img_result, news_text = process_frame(frame)
    print(f"辨識結果: {news_text}")
    # 之後這裡接妳原本的 Telegram 發送邏輯
cap.release()
