import os
import stable_whisper

def align_and_convert_to_lrc(model, audio_path, txt_path, lrc_path):
    # 1. 讀取原始歌詞，並將每一行存好 (這是我們最後要的完美排版)
    with open(txt_path, 'r', encoding='utf-8') as f:
        original_lines = [line.strip() for line in f.readlines() if line.strip()]
        
    if not original_lines:
        return False
        
    # 2. 將歌詞接成單一字串 (避開 List 引發的 < str / int 衝突 bug)
    lyrics_text = "\n".join(original_lines)
    
    # 3. 執行強制對齊 (此時模型保證不會崩潰)
    result = model.align(audio_path, lyrics_text, language='ja')
    
    # 4. 把所有辨識出來的詞 (Words) 攤平成一個大陣列
    all_words = []
    for segment in result.segments:
        all_words.extend(segment.words)
        
    # 5. 建立「字元」到「時間」的絕對對應表 (終極武器)
    char_to_time = []
    for w in all_words:
        # 將這個詞的開始時間，賦予給這個詞包含的每一個字元
        for _ in range(len(w.word)):
            char_to_time.append(w.start)
            
    # 6. 重建 LRC 檔案：照著你原本的行數，去查表拿時間
    with open(lrc_path, 'w', encoding='utf-8') as f:
        line_start_char_idx = 0
        
        for line in original_lines:
            # 查表獲取這行第一個字元的時間 (加上防呆機制防止越界)
            if line_start_char_idx < len(char_to_time):
                start_time = char_to_time[line_start_char_idx]
            else:
                start_time = 0.0
                
            # 將秒數轉為 [mm:ss.xx] 格式
            minutes = int(start_time // 60)
            seconds = start_time % 60
            time_tag = f"[{minutes:02d}:{seconds:05.2f}]"
            
            # 寫入 LRC (完美保留你的原版句子)
            f.write(f"{time_tag} {line}\n")
            
            # 推進索引：這行的長度 + 1 (加回我們剛剛用來連接字串的 \n 的長度)
            line_start_char_idx += len(line) + 1

    return True

if __name__ == "__main__":
    download_dir = "downloads"
    
    print("🤖 正在載入 Whisper AI 模型...")
    model = stable_whisper.load_model('small') 
    
    wav_files = [f for f in os.listdir(download_dir) if f.endswith(".wav")]
    print(f"\n📂 找到 {len(wav_files)} 首歌曲，開始執行終極對齊產線...\n")
    
    for wav_file in wav_files:
        song_name = os.path.splitext(wav_file)[0]
        audio_path = os.path.join(download_dir, wav_file)
        txt_path = os.path.join(download_dir, f"{song_name}.txt")
        lrc_path = os.path.join(download_dir, f"{song_name}.lrc")
        
        if os.path.exists(lrc_path):
            print(f"⏭️  [已存在] {song_name}.lrc (略過)")
            continue
            
        if not os.path.exists(txt_path):
            print(f"⚠️  [找不到歌詞] 缺少 {song_name}.txt，略過對齊")
            continue
            
        print(f"🎧 正在對齊：【 {song_name} 】...")
        try:
            success = align_and_convert_to_lrc(model, audio_path, txt_path, lrc_path)
            if success:
                print(f"✅ [成功] {song_name}.lrc 已完美生成！")
            else:
                print(f"❌ [失敗] {song_name}.txt 是空的")
        except Exception as e:
            print(f"❌ [失敗] {song_name} 對齊發生錯誤: {e}")
            
    print("\n🎉 產線執行完畢！")