import os
import subprocess
import shutil
import stable_whisper

def isolate_vocals(original_audio_path, separated_dir, song_name):
    """
    雙重替身大法：讓 Demucs 也只處理英文檔名，做完再用 Python 搬回日文資料夾
    """
    print("  -> 🪄 啟動 Demucs 進行人聲分離 (這會花一點時間)...")
    
    # 1. 建立給 Demucs 用的英文替身
    safe_input = "temp_demucs_in.wav"
    shutil.copy2(original_audio_path, safe_input)
    
    command = [
        "demucs",
        "--two-stems=vocals",
        "-o", separated_dir,
        safe_input
    ]
    
    # 執行分離
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Demucs 預設會輸出到 temp_demucs_in 資料夾
    temp_output_path = os.path.join(separated_dir, "htdemucs", "temp_demucs_in", "vocals.wav")
    
    # 2. 我們要把檔案搬回原本的日文資料夾當作快取
    final_cache_dir = os.path.join(separated_dir, "htdemucs", song_name)
    final_cache_path = os.path.join(final_cache_dir, "vocals.wav")
    
    # 確保日文資料夾存在
    os.makedirs(final_cache_dir, exist_ok=True)
    
    # 用 Python 搬移檔案 (Python 不怕日文)
    if os.path.exists(temp_output_path):
        shutil.move(temp_output_path, final_cache_path)
        # 刪除 Demucs 留下的英文暫存資料夾
        shutil.rmtree(os.path.join(separated_dir, "htdemucs", "temp_demucs_in"), ignore_errors=True)
        
    # 刪除輸入的替身檔
    if os.path.exists(safe_input):
        os.remove(safe_input)
        
    return final_cache_path

def align_and_convert_to_lrc(model, vocal_audio_path, txt_path, lrc_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        original_lines = [line.strip() for line in f.readlines() if line.strip()]
        
    if not original_lines:
        return False
        
    lyrics_text = "\n".join(original_lines)
    
    print("  -> 🎧 Whisper 模型精準對齊中...")
    
    # 🌟 給 Whisper 用的英文替身
    safe_temp_audio = "temp_whisper_in.wav"
    shutil.copy2(vocal_audio_path, safe_temp_audio)
    
    try:
        result = model.align(safe_temp_audio, lyrics_text, language='ja')
    finally:
        if os.path.exists(safe_temp_audio):
            os.remove(safe_temp_audio)
            
    all_words = []
    for segment in result.segments:
        all_words.extend(segment.words)
        
    char_to_time = []
    for w in all_words:
        for _ in range(len(w.word)):
            char_to_time.append(w.start)
            
    raw_times = []
    line_start_char_idx = 0
    for line in original_lines:
        if line_start_char_idx < len(char_to_time):
            raw_times.append(char_to_time[line_start_char_idx])
        else:
            raw_times.append(raw_times[-1] if raw_times else 0.0)
        line_start_char_idx += len(line) + 1

    for i in range(1, len(raw_times)):
        if raw_times[i] <= raw_times[i-1]:
            next_valid_idx = i
            while next_valid_idx < len(raw_times) and raw_times[next_valid_idx] <= raw_times[i-1]:
                next_valid_idx += 1
                
            if next_valid_idx < len(raw_times):
                end_time = raw_times[next_valid_idx]
            else:
                end_time = raw_times[i-1] + 2.0
                
            steps = next_valid_idx - i + 1
            step_size = (end_time - raw_times[i-1]) / steps
            
            print(f"  -> ⚠️ 發現微小重疊！已修正第 {i+1} 行至第 {next_valid_idx} 行的時間。")
            for j in range(i, next_valid_idx):
                raw_times[j] = raw_times[j-1] + step_size

    with open(lrc_path, 'w', encoding='utf-8') as f:
        for line, start_time in zip(original_lines, raw_times):
            minutes = int(start_time // 60)
            seconds = start_time % 60
            time_tag = f"[{minutes:02d}:{seconds:05.2f}]"
            f.write(f"{time_tag} {line}\n")
            
    return True

if __name__ == "__main__":
    download_dir = "downloads"
    separated_dir = "separated_vocals" 
    
    print("🤖 正在載入 Whisper AI 模型...")
    model = stable_whisper.load_model('small') 
    
    wav_files = [f for f in os.listdir(download_dir) if f.endswith(".wav")]
    print(f"\n📂 找到 {len(wav_files)} 首歌曲，開始執行分離與對齊產線...\n")
    
    for wav_file in wav_files:
        song_name = os.path.splitext(wav_file)[0]
        original_audio_path = os.path.join(download_dir, wav_file)
        txt_path = os.path.join(download_dir, f"{song_name}.txt")
        lrc_path = os.path.join(download_dir, f"{song_name}.lrc")
        
        if not os.path.exists(txt_path):
            print(f"⚠️  [找不到歌詞] 缺少 {song_name}.txt，略過對齊")
            continue
            
        print(f"=====================================")
        print(f"▶️ 正在處理：【 {song_name} 】")
        try:
            vocal_audio_path = os.path.join(separated_dir, "htdemucs", song_name, "vocals.wav")
            if not os.path.exists(vocal_audio_path):
                # 💡 注意這裡多傳了一個 song_name 給函數，用來建立正確的快取資料夾
                vocal_audio_path = isolate_vocals(original_audio_path, separated_dir, song_name)
            else:
                print("  -> ♻️ 發現已分離的人聲快取，直接使用！")

            # 確保 isolate_vocals 真的有成功產生快取檔，如果沒有就報錯跳過
            if not os.path.exists(vocal_audio_path):
                raise Exception("Demucs 處理失敗，無法生成人聲檔案。")

            success = align_and_convert_to_lrc(model, vocal_audio_path, txt_path, lrc_path)
            
            if success:
                print(f"✅ [成功] {song_name}.lrc 已寫入完成！")
            else:
                print(f"❌ [失敗] {song_name}.txt 是空的")
        except Exception as e:
            print(f"❌ [錯誤] 發生未預期的例外狀況: {e}")
            
    print("\n🎉 產線執行完畢！")