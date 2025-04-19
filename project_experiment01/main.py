#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import yaml
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import importlib.util

# 添加src目錄到python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 導入VAD模塊
from vad.webrtc import WebRTCVAD
from vad.silero import SileroVAD
from vad.adaptive import AdaptiveVAD
from vad.qa_vad import QAVAD

# 導入特徵提取模塊
from features.mfcc import MFCCExtractor
from features.plp import PLPExtractor
from features.pitch import PitchExtractor

# 導入對齊模塊
from alignment.mfa import MFAAligner
from alignment.dtw import DTWAligner

# 導入評分模塊
from scoring.rf_regressor import ScoringModel

# 導入評估模塊
from evaluation.segmentation_metrics import SegmentationEvaluator
from evaluation.scoring_metrics import ScoringEvaluator

# 導入Azure模塊
from azure.speech_scoring import AzureSpeechScorer

# 導入工具函數
from utils.data_utils import load_dataset, prepare_features
from utils.visualization import plot_results
from utils.logging_utils import LoggingManager

# 添加utils路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class ExperimentManager:
    """
    實驗管理器，負責加載配置、初始化組件、運行實驗並生成報告。
    """
    
    def __init__(self, config_path, output_dir=None):
        """
        初始化實驗管理器。
        
        Args:
            config_path (str): 配置文件路徑
            output_dir (str, optional): 輸出目錄。如果未提供，將使用預設的results目錄
        """
        # 設定根路徑
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 設定輸出目錄
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(self.root_dir, "results")
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 創建實驗ID (使用時間戳)
        self.experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 初始化日誌管理器
        log_dir = os.path.join(self.root_dir, "logs")
        self.logger_manager = LoggingManager(log_dir=log_dir, experiment_name=self.experiment_id)
        self.logger = self.logger_manager.get_logger()
        
        # 加載配置
        self.config_path = config_path
        self._load_config()
        
        # 記錄實驗開始
        self.logger_manager.log_experiment_start(self.config)
        
        # 初始化結果存儲
        self.results = {
            "stacks": {},
            "summary": {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config_path
        }
        
        # 記錄導入了實驗管理器
        self.logger.info(f"實驗管理器初始化完成，ID: {self.experiment_id}")
        
        # 初始化組件字典
        self.vad_modules = {
            'webrtc': WebRTCVAD,
            'silero': SileroVAD,
            'adaptive': AdaptiveVAD,
            'qa_vad': QAVAD
        }
        
        self.feature_extractors = {
            'mfcc': MFCCExtractor,
            'plp': PLPExtractor,
            'pitch': PitchExtractor
        }
        
        self.aligners = {
            'mfa': MFAAligner,
            'dtw': DTWAligner
        }
        
        self.scoring_models = {
            'rf_regressor': ScoringModel
        }
        
    def _load_config(self):
        """加載配置文件。"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            
            # 記錄配置加載成功
            self.logger.debug(f"成功加載配置文件: {self.config_path}")
        except Exception as e:
            self.logger.error(f"加載配置文件失敗: {str(e)}")
            raise
    
    def _import_component(self, component_type, component_name):
        """
        動態導入組件。
        
        Args:
            component_type (str): 組件類型 (vad, features, alignment, scoring)
            component_name (str): 組件名稱
            
        Returns:
            module: 導入的模組
        """
        try:
            # 構建模組路徑
            module_path = os.path.join(self.root_dir, "src", component_type, f"{component_name}.py")
            
            # 檢查模組文件是否存在
            if not os.path.exists(module_path):
                self.logger.error(f"模組文件不存在: {module_path}")
                raise FileNotFoundError(f"模組文件不存在: {module_path}")
            
            # 導入模組
            module_name = f"{component_type}.{component_name}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.logger.debug(f"成功導入組件: {component_type}.{component_name}")
            return module
        except Exception as e:
            self.logger.error(f"導入組件失敗 {component_type}.{component_name}: {str(e)}")
            raise
    
    def _initialize_stack_components(self, stack_config):
        """
        初始化堆疊中的所有組件。
        
        Args:
            stack_config (dict): 堆疊配置
            
        Returns:
            dict: 初始化後的組件字典
        """
        components = {}
        
        try:
            # 初始化VAD組件
            vad_name = stack_config["vad_method"]
            vad_params = stack_config.get("vad_params", {})
            vad_module = self._import_component("vad", vad_name)
            components["vad"] = getattr(vad_module, "WebRTCVAD")(**vad_params)
            
            # 初始化特徵提取組件
            features = []
            for feature_config in stack_config["feature_methods"]:
                feature_name = feature_config["name"]
                feature_params = feature_config.get("params", {})
                feature_module = self._import_component("features", feature_name)
                
                if feature_name == "mfcc":
                    feature_class = getattr(feature_module, "MFCCExtractor")
                else:
                    # 獲取模組中的第一個類 (假設每個模組只有一個主要類)
                    feature_class = next(
                        (getattr(feature_module, name) for name in dir(feature_module) 
                         if name.endswith("Extractor") and not name.startswith("_")),
                        None
                    )
                
                if feature_class:
                    features.append(feature_class(**feature_params))
                else:
                    self.logger.warning(f"模組 {feature_name} 中未找到提取器類")
            
            components["features"] = features
            
            # 初始化對齊組件 (如果有)
            if "alignment_method" in stack_config:
                align_name = stack_config["alignment_method"]
                align_params = stack_config.get("alignment_params", {})
                align_module = self._import_component("alignment", align_name)
                align_class = next(
                    (getattr(align_module, name) for name in dir(align_module)
                     if not name.startswith("_") and name.endswith(("Aligner", "Alignment"))),
                    None
                )
                if align_class:
                    components["alignment"] = align_class(**align_params)
            
            # 初始化評分組件
            score_name = stack_config["scoring_method"]
            score_params = stack_config.get("scoring_params", {})
            score_module = self._import_component("scoring", score_name)
            
            if score_name == "rf_regressor":
                score_class = getattr(score_module, "ScoringModel")
            else:
                # 獲取模組中的第一個類 (假設每個模組只有一個主要類)
                score_class = next(
                    (getattr(score_module, name) for name in dir(score_module)
                     if not name.startswith("_") and name.endswith(("Model", "Scorer"))),
                    None
                )
            
            if score_class:
                components["scoring"] = score_class(**score_params)
            else:
                self.logger.warning(f"模組 {score_name} 中未找到評分類")
            
            return components
        except Exception as e:
            self.logger.error(f"初始化堆疊組件失敗: {str(e)}")
            raise
    
    def run_stack(self, stack_name):
        """
        運行指定的實驗堆疊。
        
        Args:
            stack_name (str): 堆疊名稱
            
        Returns:
            dict: 堆疊執行結果
        """
        # 檢查堆疊是否存在
        if stack_name not in self.config["stacks"]:
            self.logger.error(f"堆疊不存在: {stack_name}")
            raise ValueError(f"堆疊不存在: {stack_name}")
        
        stack_config = self.config["stacks"][stack_name]
        
        # 記錄堆疊開始執行
        self.logger_manager.log_stack_start(stack_name, stack_config)
        
        # 堆疊開始時間
        stack_start_time = time.time()
        
        try:
            # 初始化組件
            components = self._initialize_stack_components(stack_config)
            
            # TODO: 實際執行堆疊的邏輯，現在僅作為框架示例
            # 這裡應該實現具體的VAD處理、特徵提取、對齊和評分邏輯
            
            # VAD 處理
            vad_start_time = time.time()
            # vad_results = components["vad"].process_file(...)
            vad_duration = time.time() - vad_start_time
            self.logger_manager.log_component_execution("VAD", stack_config["vad_method"], vad_duration)
            
            # 特徵提取
            for feature_extractor in components["features"]:
                feature_start_time = time.time()
                # feature_results = feature_extractor.extract(...)
                feature_duration = time.time() - feature_start_time
                self.logger_manager.log_component_execution("特徵提取", feature_extractor.__class__.__name__, feature_duration)
            
            # 對齊 (如果有)
            if "alignment" in components:
                align_start_time = time.time()
                # alignment_results = components["alignment"].align(...)
                align_duration = time.time() - align_start_time
                self.logger_manager.log_component_execution("對齊", stack_config["alignment_method"], align_duration)
            
            # 評分
            score_start_time = time.time()
            # scoring_results = components["scoring"].train_and_evaluate(...)
            score_duration = time.time() - score_start_time
            self.logger_manager.log_component_execution("評分", stack_config["scoring_method"], score_duration)
            
            # 堆疊執行時間
            stack_duration = time.time() - stack_start_time
            
            # 假設的評估指標 (實際應從scoring_results中獲取)
            metrics = {
                "rmse": 0.35,
                "mae": 0.25,
                "correlation": 0.82,
                "r2_score": 0.67
            }
            
            # 記錄堆疊執行完成
            self.logger_manager.log_stack_end(stack_name, stack_duration, metrics)
            
            # 保存結果
            self.results["stacks"][stack_name] = {
                "config": stack_config,
                "metrics": metrics,
                "duration": stack_duration
            }
            
            # 返回結果
            return self.results["stacks"][stack_name]
        except Exception as e:
            self.logger_manager.log_error(str(e), stack=stack_name)
            self.logger.exception(f"執行堆疊 {stack_name} 時發生錯誤")
            
            # 保存錯誤信息
            self.results["stacks"][stack_name] = {
                "config": stack_config,
                "error": str(e),
                "status": "failed"
            }
            return self.results["stacks"][stack_name]
    
    def run_all_stacks(self):
        """
        運行所有配置的實驗堆疊。
        
        Returns:
            dict: 所有堆疊的執行結果
        """
        self.logger.info("開始執行所有實驗堆疊")
        
        for stack_name in self.config["stacks"].keys():
            self.run_stack(stack_name)
        
        # 計算摘要統計
        self._calculate_summary()
        
        self.logger.info("所有實驗堆疊執行完成")
        return self.results
    
    def _calculate_summary(self):
        """計算實驗結果摘要統計。"""
        successful_stacks = [stack for stack, data in self.results["stacks"].items() 
                            if "error" not in data]
        
        if not successful_stacks:
            self.logger.warning("沒有成功執行的堆疊")
            self.results["summary"] = {
                "status": "no_successful_stacks",
                "success_rate": 0
            }
            return
        
        # 計算平均指標
        all_metrics = [data["metrics"] for stack, data in self.results["stacks"].items() 
                     if "metrics" in data]
        
        avg_metrics = {}
        for metric in all_metrics[0].keys():
            avg_metrics[metric] = sum(m[metric] for m in all_metrics) / len(all_metrics)
        
        # 找出最佳堆疊 (以RMSE為標準)
        best_stack = min(
            [(stack, data["metrics"]["rmse"]) for stack, data in self.results["stacks"].items() 
             if "metrics" in data],
            key=lambda x: x[1]
        )[0]
        
        # 總執行時間
        total_duration = sum(data.get("duration", 0) for data in self.results["stacks"].values())
        
        # 保存摘要
        self.results["summary"] = {
            "avg_metrics": avg_metrics,
            "best_stack": best_stack,
            "total_duration": total_duration,
            "success_rate": len(successful_stacks) / len(self.results["stacks"])
        }
        
        # 記錄實驗結束
        self.logger_manager.log_experiment_end(total_duration, self.results["summary"])
    
    def save_results(self, format="json"):
        """
        保存實驗結果。
        
        Args:
            format (str): 結果保存格式 ("json" 或 "yaml")
        """
        # 確保結果目錄存在
        results_dir = os.path.join(self.output_dir, "metrics", self.experiment_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # 構建文件路徑
        file_path = os.path.join(results_dir, f"results.{format}")
        
        try:
            if format == "json":
                import json
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False)
            elif format == "yaml":
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(self.results, f, default_flow_style=False, allow_unicode=True)
            else:
                self.logger.error(f"不支持的格式: {format}")
                raise ValueError(f"不支持的格式: {format}")
            
            self.logger.info(f"實驗結果已保存至: {file_path}")
            self.logger_manager.log_file_operation("保存", file_path)
        except Exception as e:
            self.logger.error(f"保存結果失敗: {str(e)}")
            self.logger_manager.log_file_operation("保存", file_path, success=False)
    
    def generate_report(self):
        """
        生成實驗報告。
        """
        try:
            # 導入報告生成模組
            sys.path.append(self.root_dir)
            from utils.report_generator import ReportGenerator
            
            # 初始化報告生成器
            report_dir = os.path.join(self.root_dir, "reports")
            report_generator = ReportGenerator(output_dir=report_dir)
            
            # 設置實驗配置
            report_generator.set_experiment_config(self.config)
            
            # 添加每個堆疊的結果
            for stack_name, stack_data in self.results["stacks"].items():
                if "metrics" in stack_data:
                    report_generator.add_stack_result(
                        stack_name=stack_name,
                        metrics=stack_data["metrics"],
                        config=stack_data["config"]
                    )
            
            # 添加摘要
            if "summary" in self.results:
                report_generator.add_summary(self.results["summary"])
            
            # 添加結論 (這裡是示例結論)
            if "summary" in self.results and "best_stack" in self.results["summary"]:
                best_stack = self.results["summary"]["best_stack"]
                conclusion = f"根據實驗結果，{best_stack}堆疊在測試數據上表現最佳，"
                conclusion += f"RMSE為{self.results['stacks'][best_stack]['metrics']['rmse']:.4f}。"
                conclusion += "建議在實際應用中使用此堆疊配置。"
                report_generator.add_conclusion(conclusion)
            
            # 保存報告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_generator.save_markdown_report(f"experiment_report_{self.experiment_id}.md")
            report_generator.save_pdf_report(f"experiment_report_{self.experiment_id}.pdf")
            
            # 匯出比較結果為CSV
            report_generator.export_comparison_csv(f"stack_comparison_{self.experiment_id}.csv")
            
            self.logger.info(f"實驗報告已生成: experiment_report_{self.experiment_id}")
        except Exception as e:
            self.logger.error(f"生成報告失敗: {str(e)}")


def main():
    """主程序入口。"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="實驗管理器")
    parser.add_argument("--config", type=str, default="config/experiment_config.yaml",
                        help="配置文件路徑")
    parser.add_argument("--output", type=str, default=None,
                        help="輸出目錄")
    parser.add_argument("--stack", type=str, default=None,
                        help="僅運行指定的堆疊")
    parser.add_argument("--report", action="store_true", default=True,
                        help="生成報告")
    
    args = parser.parse_args()
    
    # 獲取根目錄
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 配置文件路徑
    if not os.path.isabs(args.config):
        config_path = os.path.join(root_dir, args.config)
    else:
        config_path = args.config
    
    try:
        # 初始化實驗管理器
        experiment_manager = ExperimentManager(config_path, args.output)
        
        # 運行實驗
        if args.stack:
            # 僅運行指定堆疊
            experiment_manager.run_stack(args.stack)
        else:
            # 運行所有堆疊
            experiment_manager.run_all_stacks()
        
        # 保存結果
        experiment_manager.save_results(format="json")
        experiment_manager.save_results(format="yaml")
        
        # 生成報告（如有需要）
        if args.report:
            experiment_manager.generate_report()
        
        print(f"實驗完成，ID: {experiment_manager.experiment_id}")
        return 0
    except Exception as e:
        print(f"執行實驗時出錯: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 