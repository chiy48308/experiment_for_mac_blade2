import numpy as np
import librosa
import webrtcvad
import collections
import contextlib
import wave
import struct


class WebRTCVAD:
    """WebRTC VAD 實現，用於語音活動檢測"""
    
    def __init__(self, frame_size=30, aggressive_level=2, sampling_rate=16000):
        """
        初始化 WebRTC VAD
        
        參數:
            frame_size (int): 每幀長度（毫秒）
            aggressive_level (int): 積極程度 (0-3), 0最不積極，3最積極
            sampling_rate (int): 採樣率，必須是 8000, 16000, 32000, 48000 之一
        """
        self.frame_size = frame_size
        self.aggressive_level = aggressive_level
        self.sampling_rate = sampling_rate
        
        # 初始化VAD
        self.vad = webrtcvad.Vad(self.aggressive_level)
        
    def _frame_generator(self, audio, frame_duration_ms):
        """
        生成固定大小的音頻幀
        
        參數:
            audio (numpy.ndarray): 音頻信號
            frame_duration_ms (int): 幀長度(毫秒)
            
        返回:
            generator: 生成的音頻幀
        """
        # 轉換音頻到二進制格式
        audio = np.int16(audio * 32768).tobytes()
        
        n = int(self.sampling_rate * (frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(n) / self.sampling_rate) / 2.0
        while offset + n <= len(audio):
            yield audio[offset:offset + n], timestamp, duration
            timestamp += duration
            offset += n
            
    def detect(self, audio):
        """
        檢測音頻中的語音區段
        
        參數:
            audio (numpy.ndarray): 音頻信號，應為-1到1範圍的浮點數
            
        返回:
            list: 語音區段的時間戳 [(start1, end1), (start2, end2), ...]
        """
        frames = self._frame_generator(audio, self.frame_size)
        frames = list(frames)
        
        # 存儲是否為語音的判斷
        is_speech = []
        
        for frame, timestamp, duration in frames:
            is_speech.append(self.vad.is_speech(frame, self.sampling_rate))
            
        # 降噪：移除太短的語音段（少於3幀）
        segments = []
        in_speech = False
        current_segment = None
        
        for i, speech in enumerate(is_speech):
            if speech and not in_speech:
                # 開始新的語音段
                current_segment = frames[i][1]  # 開始時間
                in_speech = True
            elif not speech and in_speech:
                # 結束當前語音段
                segments.append((current_segment, frames[i-1][1] + frames[i-1][2]))  # (start, end)
                in_speech = False
                
        # 確保最後一個語音段被添加
        if in_speech:
            segments.append((current_segment, frames[-1][1] + frames[-1][2]))
            
        # 合併太近的語音段（間隔<200ms）
        merged_segments = []
        if segments:
            current_segment = segments[0]
            for i in range(1, len(segments)):
                if segments[i][0] - current_segment[1] < 0.2:  # 如果間隔小於200ms
                    current_segment = (current_segment[0], segments[i][1])  # 合併
                else:
                    merged_segments.append(current_segment)
                    current_segment = segments[i]
            merged_segments.append(current_segment)
            
        return merged_segments
    
    def process_file(self, file_path):
        """
        處理音頻文件並檢測語音段
        
        參數:
            file_path (str): 音頻文件路徑
            
        返回:
            list: 語音區段的時間戳
            numpy.ndarray: 原始音頻
        """
        audio, _ = librosa.load(file_path, sr=self.sampling_rate, mono=True)
        segments = self.detect(audio)
        return segments, audio
    
    def export_segments(self, file_path, output_dir=None):
        """
        導出檢測到的語音段到單獨的文件
        
        參數:
            file_path (str): 音頻文件路徑
            output_dir (str, optional): 輸出目錄
            
        返回:
            list: 保存的文件路徑
        """
        import os
        if output_dir is None:
            output_dir = os.path.dirname(file_path)
            
        segments, audio = self.process_file(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        output_files = []
        for i, (start, end) in enumerate(segments):
            start_sample = int(start * self.sampling_rate)
            end_sample = int(end * self.sampling_rate)
            segment_audio = audio[start_sample:end_sample]
            
            out_path = os.path.join(output_dir, f"{base_name}_segment_{i}.wav")
            librosa.output.write_wav(out_path, segment_audio, self.sampling_rate)
            output_files.append(out_path)
            
        return output_files


if __name__ == "__main__":
    # 使用示例
    vad = WebRTCVAD(frame_size=30, aggressive_level=2)
    audio_file = "path/to/audio.wav"
    segments, _ = vad.process_file(audio_file)
    print(f"檢測到 {len(segments)} 個語音段:")
    for i, (start, end) in enumerate(segments):
        print(f"  段落 {i+1}: {start:.2f}s - {end:.2f}s (持續 {end-start:.2f}s)") 