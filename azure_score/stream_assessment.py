import os
import time
import azure.cognitiveservices.speech as speechsdk

def pronunciation_assessment_from_microphone(reference_text):
    """
    使用麥克風進行實時發音評估
    
    參數:
        reference_text (str): 參考文本
    """
    # 從環境變數讀取訂閱密鑰和區域
    speech_key = os.environ.get('SPEECH_KEY')
    speech_region = os.environ.get('SPEECH_REGION')
    
    if not speech_key or not speech_region:
        print("請設置 SPEECH_KEY 和 SPEECH_REGION 環境變數")
        return
    
    # 創建語音配置
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    
    # 使用默認麥克風
    audio_config = speechsdk.AudioConfig(use_default_microphone=True)
    
    # 創建語音識別器
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        language="en-US",  # 可變更為其他支持的語言
        audio_config=audio_config
    )
    
    # 創建發音評估配置
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True
    )
    
    # 啟用韻律評估 (僅支援美式英語)
    pronunciation_config.enable_prosody_assessment()
    
    # 應用配置到語音識別器
    pronunciation_config.apply_to(speech_recognizer)
    
    print("請開始朗讀參考文本...")
    print(f"參考文本: {reference_text}")
    print("按 Ctrl+C 停止錄音")

    # 定義回調函數
    done = False
    
    def stop_cb(evt):
        """停止回調"""
        nonlocal done
        print('正在停止錄音...')
        done = True
    
    def recognized_cb(evt):
        """識別結果回調"""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # 獲取發音評估結果
            pronunciation_result = speechsdk.PronunciationAssessmentResult(evt.result)
            print(f"\n識別的文本: {evt.result.text}")
            print(f"發音準確度: {pronunciation_result.accuracy_score}")
            print(f"流暢度: {pronunciation_result.fluency_score}")
            print(f"完整度: {pronunciation_result.completeness_score}")
            print(f"發音總分: {pronunciation_result.pronunciation_score}")

    # 連接事件
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)
    
    # 開始連續識別
    speech_recognizer.start_continuous_recognition()
    
    # 等待直到識別結束
    try:
        while not done:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("用戶中斷錄音")
    finally:
        # 停止識別
        speech_recognizer.stop_continuous_recognition()
        
    print("發音評估已完成")

if __name__ == "__main__":
    # 使用示例
    print("Azure 語音服務實時發音評估範例")
    print("請確保已設置 SPEECH_KEY 和 SPEECH_REGION 環境變數")
    
    # 獲取參考文本
    reference = input("請輸入參考文本: ")
    
    pronunciation_assessment_from_microphone(reference) 