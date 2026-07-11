import os
import re

def add_intro_notes():
    lyrics_folder = "./downloads"
    
    if not os.path.exists(lyrics_folder):
        print(f"找不到資料夾: {lyrics_folder}")
        return

    lrc_files = [f for f in os.listdir(lyrics_folder) if f.endswith(".lrc")]
    print(f"🔍 掃描 {len(lrc_files)} 個 LRC 檔案，尋找長前奏...\n")
    
    # 抓取 [mm:ss.xx] 的正則表達式
    time_reg = re.compile(r"^\[(\d{2}):(\d{2})\.\d{2,3}\]")
    updated_count = 0
    
    for file_name in lrc_files:
        file_path = os.path.join(lyrics_folder, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            continue
            
        # 尋找第一句有時間軸的歌詞
        for i, line in enumerate(lines):
            match = time_reg.match(line)
            if match:
                mins = int(match.group(1))
                secs = int(match.group(2))
                total_secs = mins * 60 + secs
                
                # 如果第一句歌詞超過 2 秒，且它本身不是 00:00.00
                if total_secs >= 2:
                    # 插入音符符號到最前面
                    lines.insert(i, "[00:00.00] ♪\n")
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                        
                    print(f"🎵 補上前奏音符: {file_name} (原第一句在 {mins:02d}:{secs:02d})")
                    updated_count += 1
                break # 找到第一句就結束檢查
                
    print(f"\n✅ 處理完成！共幫 {updated_count} 首歌加上了 ♪ 前奏。")

if __name__ == "__main__":
    add_intro_notes()