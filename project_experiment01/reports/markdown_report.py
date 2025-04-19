"""
Markdown報告生成模組 - 產生實驗結果的Markdown格式報告
"""
import os
import yaml
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import math


def generate_markdown_report(experiment_name, config, results, output_path=None):
    """
    生成實驗結果的Markdown格式報告
    
    參數:
        experiment_name (str): 實驗名稱
        config (dict): 實驗配置
        results (dict): 實驗結果
        output_path (str, optional): 輸出路徑
        
    返回:
        str: 報告文件路徑
    """
    # 決定輸出路徑
    if output_path is None:
        reports_dir = Path(__file__).parent.parent / "reports" / "files"
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = reports_dir / f"{experiment_name}_{timestamp}.md"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 組合報告內容
    report_content = []
    
    # 添加標題與摘要部分
    report_content.extend([
        f"# 實驗報告: {experiment_name}\n",
        f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## 摘要\n",
        f"此報告包含實驗 **{experiment_name}** 的完整結果，包括各Stack的執行配置、評估指標和比較分析。\n"
    ])
    
    # 添加實驗配置部分
    report_content.extend([
        "## 實驗配置\n",
        "### 全局參數\n",
        "```yaml",
        yaml.dump(config.get('global', {}), default_flow_style=False),
        "```\n"
    ])
    
    # 添加各Stack結果
    report_content.append("## 實驗結果\n")
    
    # 獲取所有評估指標
    all_metrics = set()
    for stack_metrics in results.values():
        for metric in stack_metrics.keys():
            all_metrics.add(metric)
    
    # 創建比較表格
    if results:
        report_content.append("### 結果對比\n")
        
        # 創建表格數據
        table_data = {"Stack": []}
        for metric in sorted(all_metrics):
            table_data[metric] = []
        
        for stack_name, stack_metrics in results.items():
            stack_display_name = config.get('stacks', {}).get(stack_name, {}).get('name', stack_name)
            table_data["Stack"].append(stack_display_name)
            
            for metric in sorted(all_metrics):
                if metric in stack_metrics:
                    value = stack_metrics[metric]
                    if isinstance(value, float):
                        table_data[metric].append(f"{value:.4f}")
                    else:
                        table_data[metric].append(str(value))
                else:
                    table_data[metric].append("N/A")
        
        # 創建Markdown表格
        report_content.append("| Stack | " + " | ".join(sorted(all_metrics)) + " |")
        report_content.append("| --- | " + " | ".join(["---"] * len(all_metrics)) + " |")
        
        for i in range(len(table_data["Stack"])):
            row = f"| {table_data['Stack'][i]} |"
            for metric in sorted(all_metrics):
                row += f" {table_data[metric][i]} |"
            report_content.append(row)
        
        report_content.append("\n")
    
    # 添加各Stack詳細信息
    for stack_name, stack_config in config.get('stacks', {}).items():
        stack_display_name = stack_config.get('name', stack_name)
        report_content.extend([
            f"### Stack: {stack_display_name}\n",
            f"**描述**: {stack_config.get('description', 'N/A')}\n",
            "#### 配置\n",
            "```yaml",
            yaml.dump(stack_config, default_flow_style=False),
            "```\n"
        ])
        
        # 添加評估指標
        if stack_name in results:
            report_content.append("#### 評估指標\n")
            metrics = results[stack_name]
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    report_content.append(f"- **{metric_name}**: {value:.4f}")
                else:
                    report_content.append(f"- **{metric_name}**: {value}")
            report_content.append("\n")
    
    # 添加可視化圖表引用
    report_content.extend([
        "## 可視化圖表\n",
        "以下是實驗結果的可視化圖表:\n"
    ])
    
    # 獲取可能的可視化圖表路徑
    vis_dir = Path(__file__).parent.parent / "results" / experiment_name / "visualizations"
    if vis_dir.exists():
        for stack_name in config.get('stacks', {}).keys():
            stack_vis_dir = vis_dir / stack_name
            if stack_vis_dir.exists():
                stack_display_name = config.get('stacks', {}).get(stack_name, {}).get('name', stack_name)
                report_content.append(f"### {stack_display_name}\n")
                
                # 列出所有圖表
                image_files = list(stack_vis_dir.glob("*.png")) + list(stack_vis_dir.glob("*.jpg"))
                for img_file in sorted(image_files):
                    # 獲取相對路徑
                    rel_path = os.path.relpath(img_file, Path(output_path).parent)
                    img_name = img_file.stem.replace("_", " ").title()
                    report_content.append(f"![{img_name}]({rel_path})\n")
                    report_content.append(f"*圖表 {img_name}*\n\n")
    
    # 添加結論部分
    report_content.extend([
        "## 結論\n",
        "根據實驗結果，我們可以得出以下結論:\n",
        "_此部分需手動填寫具體結論_\n"
    ])
    
    # 添加建議部分
    report_content.extend([
        "## 建議\n",
        "基於本次實驗結果，我們提出以下改進建議:\n",
        "_此部分需手動填寫具體建議_\n"
    ])
    
    # 寫入報告文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_content))
    
    return str(output_path)


def _find_best_stack(results, metric, higher_is_better=True):
    """
    找出特定指標最佳的Stack
    
    參數:
        results (dict): 實驗結果
        metric (str): 指標名稱
        higher_is_better (bool): 是否越高越好
        
    返回:
        tuple: (最佳Stack名稱, 最佳值)
    """
    best_stack = None
    best_value = float('-inf') if higher_is_better else float('inf')
    
    for stack_name, metrics in results.items():
        if metric in metrics:
            value = metrics[metric]
            if isinstance(value, (int, float)):
                if higher_is_better and value > best_value:
                    best_value = value
                    best_stack = stack_name
                elif not higher_is_better and value < best_value:
                    best_value = value
                    best_stack = stack_name
    
    return best_stack, best_value


if __name__ == "__main__":
    # 測試代碼
    test_config = {
        "global": {
            "sampling_rate": 16000,
            "window_size": 0.025,
            "hop_length": 0.01
        },
        "stacks": {
            "stack1": {
                "name": "WebRTC+MFCC 基準實驗",
                "description": "使用WebRTC進行VAD，MFCC特徵",
                "vad": {"method": "webrtc", "params": {"aggressive_level": 2}},
                "features": [{"method": "mfcc"}]
            },
            "stack2": {
                "name": "Silero+MFCC 實驗",
                "description": "使用Silero進行VAD，MFCC特徵",
                "vad": {"method": "silero", "params": {"threshold": 0.5}},
                "features": [{"method": "mfcc"}]
            }
        }
    }
    
    test_results = {
        "stack1": {
            "mae": 0.456,
            "r2": 0.789,
            "pearson_correlation": 0.876,
            "segment_accuracy": 0.65
        },
        "stack2": {
            "mae": 0.321,
            "r2": 0.891,
            "pearson_correlation": 0.923,
            "segment_accuracy": 0.78
        }
    }
    
    report_path = generate_markdown_report("test_experiment", test_config, test_results)
    print(f"生成的報告路徑: {report_path}") 