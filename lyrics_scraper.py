import os
import requests
from bs4 import BeautifulSoup
import time
import re

def search_and_download_lyrics_interactive(search_keyword, original_name, save_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.uta-net.com/search/?Keyword={search_keyword}"
    
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print(f"[網站阻擋] 狀態碼 {response.status_code}，請稍後再試。")
            return False

        soup = BeautifulSoup(response.text, "html.parser")
        
        all_links = soup.find_all("a", href=lambda href: href and href.startswith("/song/"))
        unique_songs = []
        seen = set()
        
        for link in all_links:
            if link['href'] not in seen:
                unique_songs.append(link)
                seen.add(link['href'])
            if len(unique_songs) == 5: 
                break
                
        if not unique_songs:
            print(f"❌ [找不到] 找不到關於 '{search_keyword}' 的結果。")
            return False
            
        print(f"\n====================================")
        print(f"🎵 正在處理音檔：【 {original_name} 】")
        print(f"🔍 實際搜尋關鍵字： {search_keyword}")
        print(f"====================================")
        for i, song in enumerate(unique_songs):
            print(f"[{i+1}] {song.text.strip()}")
        print("[0] 都不是 (進入手動搜尋或跳過)")
        
        choice = input(f"👉 請選擇你要的歌曲編號 (0-{len(unique_songs)}): ")
        
        if not choice.isdigit() or int(choice) == 0 or int(choice) > len(unique_songs):
            return False
            
        selected_link = unique_songs[int(choice)-1]
        song_url = "https://www.uta-net.com" + selected_link['href']
        
        song_page = requests.get(song_url, headers=headers)
        song_soup = BeautifulSoup(song_page.text, "html.parser")
        lyrics_div = song_soup.find("div", id="kashi_area")
        
        if lyrics_div:
            lyrics = lyrics_div.get_text(separator="\n").strip()
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(lyrics)
            print(f"✅ [成功存檔] {original_name}\n")
            return True
        else:
            print(f"❌ [解析失敗] 找不到歌詞區塊\n")
            return True # 雖然失敗但也算處理過了，不用再手動
            
    except Exception as e:
        print(f"❌ [發生錯誤] {original_name}: {e}\n")
        return False

if __name__ == "__main__":
    download_dir = "downloads"
    wav_files = [f for f in os.listdir(download_dir) if f.endswith(".wav")]
    print(f"共找到 {len(wav_files)} 首歌曲，開始執行半自動歌詞爬蟲...\n")
    
    for wav_file in wav_files:
        original_name = os.path.splitext(wav_file)[0]
        txt_path = os.path.join(download_dir, f"{original_name}.txt")
        
        if os.path.exists(txt_path):
            print(f"⏭️  [已存在] {original_name}.txt (略過)")
            continue
            
        # 🧹 清洗搜尋字串 (這次幫你保留了冒號！)
        search_keyword = re.sub(r'[\(\[【].*?[\)\]】]', '', original_name)
        search_keyword = search_keyword.split('—')[0]
        search_keyword = search_keyword.split('-')[0]
        # 刪除了針對冒號的 split，讓 BURN : BORN 得以存活
        search_keyword = search_keyword.strip()
        
        # 使用一個 while 迴圈，讓你可以不斷嘗試手動輸入，直到成功或放棄
        while True:
            success = search_and_download_lyrics_interactive(search_keyword, original_name, txt_path)
            
            if success:
                break # 成功抓到就跳出迴圈，換下一首歌
            else:
                # 如果選了 0 或是根本沒搜到，啟動手動防呆機制
                print(f"\n⚠️  無法自動匹配【 {original_name} 】")
                custom_keyword = input(f"✏️  請手動輸入要搜尋的歌名 (直接按 Enter 放棄這首): ").strip()
                
                if custom_keyword == "":
                    print(f"⏭️  [放棄] 跳過 {original_name}\n")
                    break # 放棄，換下一首歌
                else:
                    search_keyword = custom_keyword # 換上你手動打的關鍵字，再跑一次迴圈！
        
        time.sleep(1)
        
    print("\n🎉 所有歌曲處理完畢！")