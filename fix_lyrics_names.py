import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
# 為了避免 SSL 憑證問題，記得確認環境是否需要 tlsCAFile=certifi.where()，如果你在 local 跑不會報錯就先不用加
client = MongoClient(os.getenv("MONGO_URI"))
db = client["spotify_project"]
lyrics_collection = db["lyrics"]

def fetch_search_results(song_name):
    """透過 iTunes API 抓取歌曲與歌手資訊 (強制使用日文)"""
    
    # 🎯 關鍵修改：加上 &country=jp 和 &lang=ja_jp
    url = f"https://itunes.apple.com/search?term={song_name}&entity=song&limit=5&country=jp&lang=ja_jp"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            return [{"title": r["trackName"], "artist": r["artistName"]} for r in results]
    except Exception as e:
        print(f"搜尋失敗: {e}")
    return []

def process_lyrics_pipeline(file_path):
    # 1. 讀取現成的 LRC 內容
    with open(file_path, "r", encoding="utf-8") as f:
        lrc_content = f.read()
    
    # 2. 從檔名抓取純歌名 (去頭去尾)
    raw_song_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # 3. 線上搜尋候選者
    print(f"\n====================================")
    print(f"🎵 正在處理歌詞：【 {raw_song_name} 】")
    unique_songs = fetch_search_results(raw_song_name)
    
    if not unique_songs:
        print(f"❌ [找不到] 找不到關於 '{raw_song_name}' 的任何線上結果。")
        return False

    # 4. 秀出選項讓使用者互動確認
    for i, song in enumerate(unique_songs):
        print(f"[{i+1}] 歌名: {song['title']} | 歌手: {song['artist']}")
    print("[0] 都不是 (手動輸入歌手或跳過)")
    
    choice = input(f"👉 請選擇正確的歌曲編號 (0-{len(unique_songs)}): ")
    
    # 5. 處理選擇邏輯
    if choice.isdigit() and int(choice) > 0 and int(choice) <= len(unique_songs):
        selected = unique_songs[int(choice) - 1]
        final_title = selected["title"]
        final_artist = selected["artist"]
    elif choice == "0":
        final_title = raw_song_name
        final_artist = input("⌨️ 請手動輸入正確的歌手名稱 (或輸入 Skip 跳過): ").strip()
        if final_artist.lower() == "skip":
            return False
    else:
        print("⚠️ 輸入無效，跳過此歌。")
        return False

    # 6. 組裝 MongoDB Primary Key
    track_id = f"{final_title}_{final_artist}"
    print(f"🚀 準備寫入資料庫，Key: '{track_id}'")
    
    # 7. 一鍵送上雲端
    try:
        lyrics_collection.update_one(
            {"track_id": track_id},
            {"$set": {"lrc": lrc_content}},
            upsert=True
        )
        print("✅ 雲端資料庫同步成功！")
        return True
    except Exception as e:
        print(f"❌ 寫入資料庫失敗: {e}")
        return False

def main():
    lyrics_folder = "./downloads"
    
    if not os.path.exists(lyrics_folder):
        print(f"找不到資料夾: {lyrics_folder}")
        return

    # 只篩選出 .lrc 檔案
    lrc_files = [f for f in os.listdir(lyrics_folder) if f.endswith(".lrc")]
    print(f"📂 找到 {len(lrc_files)} 個 LRC 檔案，準備啟動確認產線...\n")

    for file_name in lrc_files:
        full_path = os.path.join(lyrics_folder, file_name)
        process_lyrics_pipeline(full_path)

if __name__ == "__main__":
    main()