import yt_dlp
import os

def download_audio_batch(url_file_path, output_dir="downloads"):
    # 確保輸出資料夾存在
    os.makedirs(output_dir, exist_ok=True)
    
    # yt-dlp 的設定選項
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s', # 輸出檔名格式
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',                 # 轉換為 wav (可改為 mp3)
            'preferredquality': '192',               # 音質
        }],
        'quiet': False, # 設為 True 可以隱藏終端機的下載進度條
    }

    # 讀取 txt 檔內的網址
    with open(url_file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    # 執行批次下載
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

if __name__ == "__main__":
    print("開始批次下載音檔...")
    download_audio_batch("urls.txt")
    print("下載完成！")