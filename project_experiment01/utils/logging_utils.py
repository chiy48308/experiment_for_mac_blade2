"""
日誌管理器模塊 - 使用loguru處理實驗日誌
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
import json


class LoggingManager:
    """
    使用 loguru 庫的日誌管理工具類。
    用於記錄實驗過程中的各種級別的日誌，包括調試信息、一般信息和錯誤信息。
    """
    
    def __init__(self, log_dir="logs", experiment_name=None, log_level="INFO"):
        """
        初始化日誌管理器。
        
        Args:
            log_dir (str): 日誌存儲目錄
            experiment_name (str, optional): 實驗名稱，如不提供則使用時間戳
            log_level (str): 日誌記錄級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # 設定實驗名稱
        if experiment_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.experiment_name = f"experiment_{timestamp}"
        else:
            self.experiment_name = experiment_name
        
        # 設定日誌目錄
        self.log_dir = Path(log_dir)
        self.debug_log_dir = self.log_dir / "debug"
        self.info_log_dir = self.log_dir / "info"
        self.error_log_dir = self.log_dir / "error"
        
        # 確保目錄存在
        self.debug_log_dir.mkdir(parents=True, exist_ok=True)
        self.info_log_dir.mkdir(parents=True, exist_ok=True)
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 移除預設的 logger
        logger.remove()
        
        # 添加控制台輸出 (INFO 級別及以上)
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level
        )
        
        # 添加調試日誌文件 (DEBUG 級別及以上)
        debug_log_file = self.debug_log_dir / f"{self.experiment_name}_debug.log"
        logger.add(
            str(debug_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",    # 當日誌文件達到10MB時輪換
            retention="1 week",  # 保留一周的日誌
            compression="zip"    # 壓縮輪換的日誌
        )
        
        # 添加一般信息日誌文件 (INFO 級別及以上)
        info_log_file = self.info_log_dir / f"{self.experiment_name}_info.log"
        logger.add(
            str(info_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
            rotation="10 MB",
            retention="1 month",  # 保留一個月的日誌
            compression="zip"
        )
        
        # 添加錯誤日誌文件 (ERROR 級別及以上)
        error_log_file = self.error_log_dir / f"{self.experiment_name}_error.log"
        logger.add(
            str(error_log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="10 MB",
            retention="3 months",  # 保留三個月的日誌
            compression="zip"
        )
        
        # 紀錄初始化信息
        logger.info(f"日誌管理器初始化完成，實驗名稱: {self.experiment_name}")
        logger.debug(f"調試日誌目錄: {self.debug_log_dir}")
        logger.debug(f"信息日誌目錄: {self.info_log_dir}")
        logger.debug(f"錯誤日誌目錄: {self.error_log_dir}")
        
        self.logger = logger
        self.metrics = {}
        self.timings = {}
        self.start_time = datetime.now()
    
    def get_logger(self):
        """
        獲取 logger 實例。
        
        Returns:
            logger: loguru 的 logger 實例
        """
        return self.logger
    
    def log_experiment_start(self, config_info):
        """
        記錄實驗開始。
        
        Args:
            config_info (dict): 實驗配置信息
        """
        self.logger.info(f"========== 實驗 '{self.experiment_name}' 開始執行 ==========")
        self.logger.debug(f"實驗配置: {config_info}")
    
    def log_experiment_end(self, duration, results):
        """
        記錄實驗結束。
        
        Args:
            duration (float): 實驗執行時間（秒）
            results (dict): 實驗結果
        """
        self.logger.info(f"========== 實驗 '{self.experiment_name}' 執行完成 ==========")
        self.logger.info(f"執行時間: {duration:.2f} 秒")
        self.logger.debug(f"實驗結果: {results}")
    
    def log_stack_start(self, stack_name, stack_config):
        """
        記錄堆疊實驗開始。
        
        Args:
            stack_name (str): 堆疊名稱
            stack_config (dict): 堆疊配置
        """
        self.logger.info(f"---------- 開始執行堆疊: {stack_name} ----------")
        self.logger.debug(f"堆疊配置: {stack_config}")
    
    def log_stack_end(self, stack_name, duration, metrics):
        """
        記錄堆疊實驗結束。
        
        Args:
            stack_name (str): 堆疊名稱
            duration (float): 執行時間（秒）
            metrics (dict): 評估指標
        """
        self.logger.info(f"---------- 堆疊 {stack_name} 執行完成 ----------")
        self.logger.info(f"執行時間: {duration:.2f} 秒")
        self.logger.info(f"評估指標: {metrics}")
    
    def log_component_execution(self, component_type, component_name, duration, status="完成"):
        """
        記錄組件執行。
        
        Args:
            component_type (str): 組件類型 (VAD, 特徵提取等)
            component_name (str): 組件名稱
            duration (float): 執行時間（秒）
            status (str, optional): 執行狀態。預設為"完成"
        """
        self.logger.info(f"{component_type} - {component_name}: {status} (耗時: {duration:.2f} 秒)")
    
    def log_error(self, error_message, component=None, stack=None):
        """
        記錄錯誤。
        
        Args:
            error_message (str): 錯誤信息
            component (str, optional): 發生錯誤的組件
            stack (str, optional): 發生錯誤的堆疊
        """
        context = ""
        if stack:
            context += f"堆疊: {stack} "
        if component:
            context += f"組件: {component} "
        
        if context:
            self.logger.error(f"{context}- {error_message}")
        else:
            self.logger.error(error_message)
    
    def log_file_operation(self, operation, file_path, success=True):
        """
        記錄文件操作。
        
        Args:
            operation (str): 操作類型 (讀取, 寫入, 刪除等)
            file_path (str): 文件路徑
            success (bool, optional): 操作是否成功。預設為True
        """
        status = "成功" if success else "失敗"
        self.logger.debug(f"文件{operation} {status}: {file_path}")
        
        if not success:
            self.logger.error(f"文件{operation}失敗: {file_path}")
    
    def log_custom(self, level, message, **kwargs):
        """
        記錄自定義信息。
        
        Args:
            level (str): 日誌級別 ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            message (str): 日誌信息
            **kwargs: 其他參數，將添加到日誌信息中
        """
        if kwargs:
            message += f" - {kwargs}"
        
        level = level.upper()
        if level == "DEBUG":
            self.logger.debug(message)
        elif level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(f"[{level}] {message}")
    
    def start_timer(self, name):
        """開始計時特定操作"""
        self.timings[name] = {"start": datetime.now()}
        self.logger.debug(f"開始計時: {name}")
    
    def end_timer(self, name, log_level="DEBUG"):
        """結束特定操作的計時並記錄"""
        if name in self.timings:
            self.timings[name]["end"] = datetime.now()
            duration = self.timings[name]["end"] - self.timings[name]["start"]
            self.timings[name]["duration"] = duration.total_seconds()
            
            getattr(self.logger, log_level.lower())(f"操作 '{name}' 完成，耗時: {duration.total_seconds():.2f} 秒")
            return self.timings[name]["duration"]
        else:
            self.logger.warning(f"找不到操作 '{name}' 的開始時間")
            return None
    
    def log_metric(self, name, value, step=None):
        """記錄性能指標"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        metric_entry = {"value": value, "timestamp": datetime.now()}
        if step is not None:
            metric_entry["step"] = step
        
        self.metrics[name].append(metric_entry)
        self.logger.info(f"指標 {name}: {value}" + (f" (步驟 {step})" if step is not None else ""))
    
    def save_metrics(self, output_file=None):
        """保存所有收集的指標到檔案"""
        if output_file is None:
            output_file = os.path.join(self.log_dir, f"{self.experiment_name}_metrics.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, default=str, indent=2)
        
        self.logger.info(f"指標已保存到: {output_file}")
        return output_file
    
    def save_timings(self, output_file=None):
        """保存所有計時數據到檔案"""
        if output_file is None:
            output_file = os.path.join(self.log_dir, f"{self.experiment_name}_timings.json")
        
        # 將計時數據轉換為可序列化的格式
        serializable_timings = {}
        for name, timing in self.timings.items():
            serializable_timings[name] = {
                "start": timing.get("start", "").isoformat() if isinstance(timing.get("start"), datetime) else None,
                "end": timing.get("end", "").isoformat() if isinstance(timing.get("end"), datetime) else None,
                "duration": timing.get("duration")
            }
        
        with open(output_file, 'w') as f:
            json.dump(serializable_timings, f, indent=2)
        
        self.logger.info(f"計時數據已保存到: {output_file}")
        return output_file
    
    def summarize_experiment(self):
        """記錄實驗總結信息"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        self.logger.info(f"實驗 '{self.experiment_name}' 完成")
        self.logger.info(f"總耗時: {total_duration:.2f} 秒")
        
        # 添加指標摘要（如果有的話）
        if self.metrics:
            self.logger.info("指標摘要:")
            for metric_name, values in self.metrics.items():
                if values:
                    latest_value = values[-1]["value"]
                    self.logger.info(f"  - {metric_name}: {latest_value}")
        
        return {
            "experiment_name": self.experiment_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": total_duration,
            "log_file": self.log_dir / f"{self.experiment_name}.log"
        }


# 使用範例
if __name__ == "__main__":
    # 創建日誌管理器
    log_manager = LoggingManager(experiment_name="test_experiment")
    
    # 記錄實驗開始
    log_manager.log_experiment_start({"vad_method": "webrtc", "feature_method": "mfcc"})
    
    # 記錄堆疊執行
    log_manager.log_stack_start("Stack1", {"vad": "webrtc", "feature": "mfcc"})
    
    # 記錄組件執行
    log_manager.log_component_execution("VAD", "WebRTC", 1.5)
    log_manager.log_component_execution("特徵提取", "MFCC", 2.3)
    
    # 記錄自定義信息
    log_manager.log_custom("INFO", "處理文件", file="example.wav", duration=3.5)
    
    # 記錄錯誤
    try:
        raise ValueError("示例錯誤")
    except Exception as e:
        log_manager.log_error(str(e), component="MFCC提取", stack="Stack1")
    
    # 記錄堆疊完成
    log_manager.log_stack_end("Stack1", 5.8, {"rmse": 0.32, "correlation": 0.87})
    
    # 記錄實驗完成
    log_manager.log_experiment_end(10.2, {"overall_score": 0.85}) 