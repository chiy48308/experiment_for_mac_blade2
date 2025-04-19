import os
import azure.cognitiveservices.speech as speechsdk

def pronunciation_assessment_from_file(file_path, reference_text):
    """
    從音頻文件進行發音評估
    
    參數:
        file_path (str): 音頻文件路徑
        reference_text (str): 參考文本
    """
    # 從環境變數讀取訂閱密鑰和區域
    # 注意: 使用前需要設置這些環境變數
    # export SPEECH_KEY=your_speech_key
    # export SPEECH_REGION=your_speech_region
    speech_key = os.environ.get('SPEECH_KEY')
    speech_region = os.environ.get('SPEECH_REGION')
    
    if not speech_key or not speech_region:
        print("請設置 SPEECH_KEY 和 SPEECH_REGION 環境變數")
        return
    
    # 創建語音配置
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    
    # 設置音頻來源
    audio_config = speechsdk.AudioConfig(filename=file_path)
    
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
    
    # 執行語音識別
    print("評估發音中...")
    result = speech_recognizer.recognize_once()
    
    # 檢查結果
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        # 獲取發音評估結果
        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
        
        print(f"識別的文本: {result.text}")
        print(f"發音準確度: {pronunciation_result.accuracy_score}")
        print(f"流暢度: {pronunciation_result.fluency_score}")
        print(f"完整度: {pronunciation_result.completeness_score}")
        print(f"發音總分: {pronunciation_result.pronunciation_score}")
        
        # 獲取詳細結果 (包含音素級評分)
        detailed_result = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
        print(f"\n詳細結果 JSON:\n{detailed_result}")
        
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print(f"無法識別語音: {result.no_match_details}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        print(f"語音識別已取消: {cancellation.reason}")
        if cancellation.reason == speechsdk.CancellationReason.Error:
            print(f"錯誤詳情: {cancellation.error_details}")

if __name__ == "__main__":
    # 使用示例
    print("Azure 語音服務發音評估範例")
    print("請確保已設置 SPEECH_KEY 和 SPEECH_REGION 環境變數")
    print("還需要準備一個音頻文件用於測試")
    
    # 測試參數
    audio_file = input("請輸入音頻文件路徑: ")
    reference = input("請輸入參考文本: ")
    
    pronunciation_assessment_from_file(audio_file, reference) 