import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["spotify_project"]
lyrics_collection = db["lyrics"]

def update_existing_lyrics():
    lyrics_folder = "./downloads"
    
    if not os.path.exists(lyrics_folder):
        print(f"找不到資料夾: {lyrics_folder}")
        return

    lrc_files = [f for f in os.listdir(lyrics_folder) if f.endswith(".lrc")]
    print(f"🚀 啟動【極速更新模式】，找到 {len(lrc_files)} 個 LRC 檔案...\n")
    
    for file_name in lrc_files:
        raw_song_name = os.path.splitext(file_name)[0]
        
        # 💡 魔法修改區：把標點符號變成萬用字元
        # [^\w]+ 代表「所有不是文字或數字的符號」，將其替換為 .*
        flexible_name = re.sub(r'[^\w]+', '.*', raw_song_name)
        regex_pattern = f"^{flexible_name}_"
        
        # 💡 加上 "$options": "i" 讓英文大小寫也免疫
        matched_docs = list(lyrics_collection.find({
            "track_id": {"$regex": regex_pattern, "$options": "i"}
        }))
        
        if len(matched_docs) == 1:
            track_id = matched_docs[0]["track_id"]
            
            with open(os.path.join(lyrics_folder, file_name), "r", encoding="utf-8") as f:
                new_lrc_content = f.read()
            
            lyrics_collection.update_one(
                {"track_id": track_id},
                {"$set": {"lrc": new_lrc_content}}
            )
            print(f"✅ 無縫更新成功: {track_id}")
            
        elif len(matched_docs) > 1:
            print(f"⚠️ 警告: 資料庫有多首以 '{raw_song_name}' 模糊比對成功的歌曲，請手動確認。")
        else:
            print(f"⏭️ 略過: 資料庫尚未建立 '{raw_song_name}'，請先使用 fix_lyrics_names.py 進行初次建檔。")

if __name__ == "__main__":
    update_existing_lyrics()