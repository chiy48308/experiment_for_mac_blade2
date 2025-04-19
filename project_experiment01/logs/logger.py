"""
日誌記錄工具模組 - 基於 loguru 實現
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
import yaml


def setup_logger(experiment_name=None, log_level="INFO"):
    """
    配置日誌記錄器
    
    參數:
        experiment_name (str, optional): 實驗名稱，用於日誌文件命名
        log_level (str): 日誌記錄等級，預設為 INFO
        
    返回:
        logger: 配置好的日誌記錄器
    """
    # 清除默認處理器
    logger.remove()
    
    # 生成日誌目錄路徑
    log_dir = Path(__file__).parent.parent / "logs" / "files"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 生成日誌文件名
    if experiment_name:
        log_file = log_dir / f"{experiment_name}_{timestamp}.log"
    else:
        log_file = log_dir / f"experiment_{timestamp}.log"
    
    # 配置標準輸出處理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # 配置文件處理器
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # 文件中記錄所有級別的日誌
        rotation="10 MB",  # 日誌文件最大 10MB
        retention="14 days",  # 保留 14 天
        encoding="utf-8"
    )
    
    logger.info(f"日誌系統初始化完成，日誌文件: {log_file}")
    return logger


def get_logger(name=None):
    """
    獲取日誌記錄器
    
    參數:
        name (str, optional): 模組名稱
        
    返回:
        logger: 日誌記錄器
    """
    if name:
        return logger.bind(name=name)
    return logger


def log_experiment_start(config, stack_name=None):
    """
    記錄實驗開始
    
    參數:
        config (dict): 實驗配置
        stack_name (str, optional): Stack 名稱，如果指定，則只記錄特定 Stack 的配置
    """
    logger.info("=" * 80)
    logger.info(f"實驗開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stack_name:
        logger.info(f"正在運行 Stack: {stack_name}")
        if stack_name in config.get('stacks', {}):
            stack_config = config['stacks'][stack_name]
            logger.info(f"Stack 配置: {yaml.dump(stack_config, default_flow_style=False)}")
    else:
        logger.info("運行所有 Stack")
        logger.debug(f"完整配置: {yaml.dump(config, default_flow_style=False)}")
    
    logger.info("=" * 80)


def log_experiment_end(results=None, duration=None):
    """
    記錄實驗結束
    
    參數:
        results (dict, optional): 實驗結果摘要
        duration (float, optional): 實驗持續時間（秒）
    """
    logger.info("=" * 80)
    logger.info(f"實驗結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if duration:
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"實驗總耗時: {int(hours)}小時 {int(minutes)}分鐘 {seconds:.2f}秒")
    
    if results:
        logger.info("實驗結果摘要:")
        for stack_name, metrics in results.items():
            logger.info(f"  Stack {stack_name}:")
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    logger.info(f"    {metric_name}: {value:.4f}")
                else:
                    logger.info(f"    {metric_name}: {value}")
    
    logger.info("=" * 80)


def log_stack_progress(stack_name, phase, progress=None, total=None, message=None):
    """
    記錄 Stack 進度
    
    參數:
        stack_name (str): Stack 名稱
        phase (str): 當前階段 (如 'VAD', '特徵提取', '對齊', '評分')
        progress (int, optional): 當前進度
        total (int, optional): 總計數量
        message (str, optional): 附加訊息
    """
    if progress is not None and total is not None:
        percentage = (progress / total) * 100
        log_msg = f"[Stack {stack_name}] {phase}: {progress}/{total} ({percentage:.1f}%)"
    else:
        log_msg = f"[Stack {stack_name}] {phase}"
    
    if message:
        log_msg += f" - {message}"
    
    logger.info(log_msg)


def log_error(error, stack_name=None, phase=None):
    """
    記錄錯誤
    
    參數:
        error (Exception): 錯誤物件
        stack_name (str, optional): Stack 名稱
        phase (str, optional): 執行階段
    """
    if stack_name and phase:
        logger.error(f"[Stack {stack_name}] {phase} 發生錯誤: {str(error)}")
    elif stack_name:
        logger.error(f"[Stack {stack_name}] 發生錯誤: {str(error)}")
    else:
        logger.error(f"發生錯誤: {str(error)}")
    
    # 記錄完整的異常堆疊
    logger.exception(error)


if __name__ == "__main__":
    # 測試代碼
    setup_logger("test_experiment")
    log = get_logger("logger_test")
    
    log.debug("這是一條除錯訊息")
    log.info("這是一條資訊訊息")
    log.warning("這是一條警告訊息")
    log.error("這是一條錯誤訊息")
    
    # 測試實驗記錄
    test_config = {
        "global": {"sampling_rate": 16000},
        "stacks": {
            "stack1": {
                "name": "Test Stack",
                "vad": {"method": "webrtc"}
            }
        }
    }
    
    log_experiment_start(test_config, "stack1")
    
    # 模擬進度記錄
    for i in range(1, 6):
        log_stack_progress("stack1", "VAD處理", i, 5)
        time.sleep(0.5)
    
    # 測試實驗結束記錄
    test_results = {
        "stack1": {
            "mae": 0.123,
            "r2": 0.876,
            "pearson_correlation": 0.932
        }
    }
    
    log_experiment_end(test_results, 10.5) 