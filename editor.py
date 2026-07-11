import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["spotify_project"]
lyrics_collection = db["lyrics"]

# 🎯 核心修改指令
# 第一個參數 {"track_id": "舊的/打錯的Key"} 是搜尋條件
# 第二個參數 {"$set": {"track_id": "正確的Key"}} 是要更新的內容
lyrics_collection.update_one(
    {"track_id": "希望的プリズム_DOLLCHESTRA"}, 
    {"$set": {"track_id": "希望的プリズム (104期Ver.)_DOLLCHESTRA"}}
)


print("📝 資料庫欄位已成功修正！")