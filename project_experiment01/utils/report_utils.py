import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import jinja2
import markdown
import weasyprint
import yaml
import json
from pathlib import Path

class ReportGenerator:
    """實驗報告生成器，用於創建Markdown和PDF格式的實驗結果報告"""
    
    def __init__(self, report_dir="./reports", template_dir="./utils/templates"):
        """
        初始化報告生成器
        
        參數:
            report_dir (str): 報告存儲目錄
            template_dir (str): 報告模板目錄
        """
        self.report_dir = Path(report_dir)
        self.template_dir = Path(template_dir)
        
        # 創建報告目錄
        self.md_dir = self.report_dir / "markdown"
        self.pdf_dir = self.report_dir / "pdf"
        self.md_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2模板引擎
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # 創建默認模板（如果模板目錄不存在）
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_templates()
    
    def _create_default_templates(self):
        """創建默認的報告模板"""
        # 實驗總結報告模板
        summary_template = """# 實驗報告摘要

## 概述
- **實驗名稱**: {{ experiment_name }}
- **執行時間**: {{ execution_time }}
- **執行者**: {{ executor }}

## 實驗配置
{{ config_summary }}

## 執行摘要
{{ execution_summary }}

## 實驗堆疊結果
{% for stack in stacks %}
### {{ stack.name }}
- **描述**: {{ stack.description }}
- **組件**: {{ stack.components }}
- **主要評估指標**:
{% for metric_name, metric_value in stack.metrics.items() %}
  - {{ metric_name }}: {{ metric_value }}
{% endfor %}
{% endfor %}

## 結論
{{ conclusion }}

"""
        
        # 詳細實驗報告模板
        detailed_template = """# 詳細實驗報告

## 實驗信息
- **實驗名稱**: {{ experiment_name }}
- **執行時間**: {{ execution_time }}
- **執行者**: {{ executor }}
- **目的**: {{ purpose }}

## 實驗配置
```yaml
{{ config_details }}
```

## 資料集描述
{{ dataset_description }}

## 實驗堆疊詳細結果
{% for stack in stacks %}
### {{ stack.name }}
#### 配置
```yaml
{{ stack.config }}
```

#### 處理流程
{{ stack.process_description }}

#### 評估指標
{% for metric_name, metric_value in stack.metrics.items() %}
- **{{ metric_name }}**: {{ metric_value }}
{% endfor %}

#### 圖表分析
{{ stack.plot_descriptions }}

![{{ stack.name }}_performance]({{ stack.plot_path }})

{% endfor %}

## 比較分析
{{ comparison_analysis }}

## 結論與推薦
{{ conclusion }}

## 附錄: 原始結果數據
```json
{{ raw_data }}
```
"""
        
        # 寫入模板文件
        with open(self.template_dir / "summary_report_template.md", "w", encoding="utf-8") as f:
            f.write(summary_template)
            
        with open(self.template_dir / "detailed_report_template.md", "w", encoding="utf-8") as f:
            f.write(detailed_template)
    
    def generate_summary_report(self, experiment_name, results_data, config, executor="自動化系統"):
        """
        生成實驗概述報告
        
        參數:
            experiment_name (str): 實驗名稱
            results_data (dict): 實驗結果數據
            config (dict): 實驗配置
            executor (str): 執行者名稱
        
        返回:
            str: 生成報告的文件路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{experiment_name}_{timestamp}_summary"
        
        # 準備模板數據
        template_data = {
            "experiment_name": experiment_name,
            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executor": executor,
            "config_summary": yaml.dump(self._extract_config_summary(config), default_flow_style=False, allow_unicode=True),
            "execution_summary": self._generate_execution_summary(results_data),
            "stacks": self._extract_stack_results(results_data),
            "conclusion": self._generate_conclusion(results_data)
        }
        
        # 渲染模板
        template = self.env.get_template("summary_report_template.md")
        report_content = template.render(**template_data)
        
        # 保存報告
        md_path = self.md_dir / f"{report_name}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # 轉換為PDF
        pdf_path = self.pdf_dir / f"{report_name}.pdf"
        self._convert_md_to_pdf(md_path, pdf_path)
        
        return str(md_path)
    
    def generate_detailed_report(self, experiment_name, results_data, config, plots_data, purpose="", executor="自動化系統"):
        """
        生成詳細實驗報告
        
        參數:
            experiment_name (str): 實驗名稱
            results_data (dict): 實驗結果數據
            config (dict): 實驗配置
            plots_data (dict): 圖表數據路徑和描述
            purpose (str): 實驗目的
            executor (str): 執行者名稱
        
        返回:
            str: 生成報告的文件路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{experiment_name}_{timestamp}_detailed"
        
        # 準備模板數據
        template_data = {
            "experiment_name": experiment_name,
            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executor": executor,
            "purpose": purpose,
            "config_details": yaml.dump(config, default_flow_style=False, allow_unicode=True),
            "dataset_description": self._extract_dataset_info(config),
            "stacks": self._extract_detailed_stack_results(results_data, config, plots_data),
            "comparison_analysis": self._generate_comparison_analysis(results_data),
            "conclusion": self._generate_detailed_conclusion(results_data),
            "raw_data": json.dumps(results_data, indent=2, ensure_ascii=False)
        }
        
        # 渲染模板
        template = self.env.get_template("detailed_report_template.md")
        report_content = template.render(**template_data)
        
        # 保存報告
        md_path = self.md_dir / f"{report_name}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # 轉換為PDF
        pdf_path = self.pdf_dir / f"{report_name}.pdf"
        self._convert_md_to_pdf(md_path, pdf_path)
        
        return str(md_path)
    
    def _convert_md_to_pdf(self, md_path, pdf_path):
        """將Markdown文件轉換為PDF"""
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            
            # 轉換為HTML
            html_content = markdown.markdown(
                md_content,
                extensions=['tables', 'fenced_code', 'codehilite']
            )
            
            # 添加基本樣式
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; margin-top: 20px; }}
                    h3 {{ color: #2980b9; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #f2f2f2; }}
                    code {{ background: #f8f8f8; padding: 2px 5px; border-radius: 3px; }}
                    pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                    img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 轉換為PDF
            weasyprint.HTML(string=styled_html).write_pdf(pdf_path)
            
        except Exception as e:
            print(f"PDF轉換錯誤: {str(e)}")
    
    def _extract_config_summary(self, config):
        """從配置中提取摘要信息"""
        if not config:
            return {"無配置數據": True}
            
        summary = {
            "global_params": config.get("global_params", {}),
            "stacks": {}
        }
        
        for stack_name, stack_config in config.get("stacks", {}).items():
            summary["stacks"][stack_name] = {
                "description": stack_config.get("description", "無描述"),
                "vad_method": stack_config.get("vad_method", {}).get("name", "無VAD方法"),
                "feature_method": stack_config.get("feature_method", {}).get("name", "無特徵提取方法"),
                "scoring_method": stack_config.get("scoring_method", {}).get("name", "無評分方法")
            }
            
        return summary
    
    def _generate_execution_summary(self, results_data):
        """生成執行摘要"""
        if not results_data or "summary" not in results_data:
            return "無執行摘要數據"
            
        summary = results_data.get("summary", {})
        return f"""
總執行時間: {summary.get('total_execution_time', '未知')}
執行的實驗堆疊數: {len(results_data.get('stacks', {}))}
處理的音頻文件數: {summary.get('total_files_processed', '未知')}
生成的特徵數: {summary.get('total_features_generated', '未知')}
        """
    
    def _extract_stack_results(self, results_data):
        """提取實驗堆疊結果"""
        stacks_results = []
        
        if not results_data or "stacks" not in results_data:
            return stacks_results
            
        for stack_name, stack_data in results_data.get("stacks", {}).items():
            stack_result = {
                "name": stack_name,
                "description": stack_data.get("description", "無描述"),
                "components": self._format_components(stack_data.get("components", {})),
                "metrics": stack_data.get("metrics", {})
            }
            stacks_results.append(stack_result)
            
        return stacks_results
    
    def _format_components(self, components):
        """格式化組件信息"""
        if not components:
            return "無組件信息"
            
        result = []
        for component_type, component_data in components.items():
            result.append(f"{component_type}: {component_data.get('name', '未知')}")
            
        return ", ".join(result)
    
    def _generate_conclusion(self, results_data):
        """生成結論"""
        if not results_data or "stacks" not in results_data:
            return "無數據可用於得出結論"
            
        # 尋找最佳性能的堆疊
        best_stack = None
        best_score = float('-inf')
        
        for stack_name, stack_data in results_data.get("stacks", {}).items():
            metrics = stack_data.get("metrics", {})
            # 假設主要評估指標是R²或相關性
            score = metrics.get("r2_score", metrics.get("correlation", 0))
            
            if score > best_score:
                best_score = score
                best_stack = stack_name
        
        if best_stack:
            return f"""
基於實驗結果分析，堆疊 "{best_stack}" 表現最佳，其主要評估指標得分為 {best_score:.4f}。
建議在後續實驗中進一步探索此配置，或基於此配置進行更細粒度的參數調整。
            """
        else:
            return "實驗結果無法確定最佳堆疊，建議檢查評估指標的計算方法或重新設計實驗。"
    
    def _extract_dataset_info(self, config):
        """提取數據集信息"""
        if not config or "global_params" not in config:
            return "無數據集信息"
            
        global_params = config.get("global_params", {})
        data_path = global_params.get("data_path", "未指定")
        
        return f"""
數據路徑: {data_path}
採樣率: {global_params.get("sampling_rate", "未指定")} Hz
位深度: {global_params.get("bit_depth", "未指定")} 位
通道數: {global_params.get("channels", "未指定")}
窗口大小: {global_params.get("window_size", "未指定")} ms
窗口移動步長: {global_params.get("window_step", "未指定")} ms
        """
    
    def _extract_detailed_stack_results(self, results_data, config, plots_data):
        """提取詳細的實驗堆疊結果"""
        detailed_stacks = []
        
        if not results_data or "stacks" not in results_data:
            return detailed_stacks
            
        stacks_config = config.get("stacks", {})
        
        for stack_name, stack_data in results_data.get("stacks", {}).items():
            stack_config = stacks_config.get(stack_name, {})
            
            detailed_stack = {
                "name": stack_name,
                "config": yaml.dump(stack_config, default_flow_style=False, allow_unicode=True),
                "process_description": self._generate_process_description(stack_data, stack_config),
                "metrics": stack_data.get("metrics", {}),
                "plot_descriptions": plots_data.get(stack_name, {}).get("description", "無圖表描述"),
                "plot_path": plots_data.get(stack_name, {}).get("path", "")
            }
            
            detailed_stacks.append(detailed_stack)
            
        return detailed_stacks
    
    def _generate_process_description(self, stack_data, stack_config):
        """生成處理流程描述"""
        components = stack_data.get("components", {})
        
        vad_method = components.get("vad", {}).get("name", "未知VAD方法")
        vad_params = stack_config.get("vad_method", {}).get("params", {})
        
        feature_method = components.get("feature", {}).get("name", "未知特徵提取方法")
        feature_params = stack_config.get("feature_method", {}).get("params", {})
        
        scoring_method = components.get("scoring", {}).get("name", "未知評分方法")
        scoring_params = stack_config.get("scoring_method", {}).get("params", {})
        
        return f"""
此實驗堆疊使用了以下處理流程:

1. **語音活動檢測 (VAD)**:
   - 方法: {vad_method}
   - 參數: {vad_params}
   - 處理結果: 分離出 {stack_data.get("vad_segments_count", "未知")} 個語音段

2. **特徵提取**:
   - 方法: {feature_method}
   - 參數: {feature_params}
   - 生成特徵數: {stack_data.get("features_count", "未知")}

3. **特徵對齊** (如適用):
   - 處理結果: 對齊了 {stack_data.get("aligned_features_count", "未知")} 個特徵

4. **模型評分**:
   - 方法: {scoring_method}
   - 參數: {scoring_params}
   - 訓練樣本數: {stack_data.get("training_samples_count", "未知")}
   - 測試樣本數: {stack_data.get("test_samples_count", "未知")}
        """
    
    def _generate_comparison_analysis(self, results_data):
        """生成比較分析"""
        if not results_data or "stacks" not in results_data:
            return "無法進行比較分析，數據不足"
            
        # 提取評估指標進行比較
        metrics_comparison = {}
        
        for stack_name, stack_data in results_data.get("stacks", {}).items():
            metrics = stack_data.get("metrics", {})
            
            for metric_name, metric_value in metrics.items():
                if metric_name not in metrics_comparison:
                    metrics_comparison[metric_name] = []
                    
                metrics_comparison[metric_name].append({
                    "stack": stack_name,
                    "value": metric_value
                })
        
        # 生成比較結果
        comparison_text = "## 各堆疊評估指標比較\n\n"
        
        for metric_name, values in metrics_comparison.items():
            # 按指標值排序
            sorted_values = sorted(values, key=lambda x: x["value"], reverse=True)
            
            comparison_text += f"### {metric_name}\n\n"
            comparison_text += "| 堆疊 | 指標值 |\n"
            comparison_text += "| --- | --- |\n"
            
            for item in sorted_values:
                comparison_text += f"| {item['stack']} | {item['value']:.4f} |\n"
                
            comparison_text += "\n"
        
        return comparison_text
    
    def _generate_detailed_conclusion(self, results_data):
        """生成詳細結論"""
        if not results_data or "stacks" not in results_data:
            return "無數據可用於得出結論"
            
        # 尋找最佳性能的堆疊及其組件
        metrics_by_stack = {}
        components_by_stack = {}
        
        for stack_name, stack_data in results_data.get("stacks", {}).items():
            metrics = stack_data.get("metrics", {})
            components = stack_data.get("components", {})
            
            # 假設主要評估指標是R²
            r2_score = metrics.get("r2_score", 0)
            metrics_by_stack[stack_name] = r2_score
            components_by_stack[stack_name] = components
        
        # 按R²排序堆疊
        sorted_stacks = sorted(metrics_by_stack.items(), key=lambda x: x[1], reverse=True)
        
        # 分析最佳組件組合
        best_stack = sorted_stacks[0][0] if sorted_stacks else None
        
        if not best_stack:
            return "實驗結果無法確定最佳堆疊，建議檢查評估指標的計算方法或重新設計實驗。"
            
        best_components = components_by_stack.get(best_stack, {})
        best_vad = best_components.get("vad", {}).get("name", "未知")
        best_feature = best_components.get("feature", {}).get("name", "未知")
        best_scoring = best_components.get("scoring", {}).get("name", "未知")
        
        # 生成結論
        conclusion = f"""
## 綜合結論

基於實驗結果分析，堆疊 "{best_stack}" 表現最佳，其R²得分為 {metrics_by_stack[best_stack]:.4f}。

### 最佳組件組合:
- VAD方法: {best_vad}
- 特徵提取方法: {best_feature}
- 評分模型: {best_scoring}

### 建議:
1. 進一步優化 {best_stack} 堆疊的參數設置，特別是 {best_feature} 的參數。
2. 考慮嘗試將 {best_feature} 特徵提取方法與其他VAD方法組合。
3. 對比使用深度學習模型替代 {best_scoring} 評分模型的效果。
4. 增加數據集規模，驗證當前結果在更大規模數據上的穩定性。

### 後續工作:
- 設計更細粒度的參數優化實驗
- 嘗試組合多種特徵提取方法
- 探索特徵選擇技術以提升模型性能
- 開發集成方法將多個模型結果融合
        """
        
        return conclusion 