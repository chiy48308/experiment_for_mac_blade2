"""
PDF報告生成模組 - 產生實驗結果的PDF格式報告
"""
import os
from datetime import datetime
from pathlib import Path
import yaml
import markdown
import json
import pandas as pd
from weasyprint import HTML, CSS


def generate_pdf_report(experiment_name, config, results, output_path=None):
    """
    生成實驗結果的PDF格式報告
    
    參數:
        experiment_name (str): 實驗名稱
        config (dict): 實驗配置
        results (dict): 實驗結果
        output_path (str, optional): 輸出路徑
        
    返回:
        str: 報告文件路徑
    """
    # 導入markdown報告生成功能
    from .markdown_report import generate_markdown_report
    
    # 決定輸出路徑
    if output_path is None:
        reports_dir = Path(__file__).parent.parent / "reports" / "files"
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = reports_dir / f"{experiment_name}_{timestamp}.pdf"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 先生成Markdown報告
    md_output_path = output_path.with_suffix('.md')
    markdown_path = generate_markdown_report(experiment_name, config, results, str(md_output_path))
    
    # 讀取Markdown內容
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 添加額外的CSS樣式
    css_content = """
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        margin: 2cm;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    h2 {
        color: #2980b9;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 5px;
        margin-top: 20px;
    }
    h3 {
        color: #3498db;
        margin-top: 15px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    img {
        max-width: 100%;
        height: auto;
        margin: 10px 0;
        border: 1px solid #ddd;
        padding: 5px;
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #7f8c8d;
        font-size: 0.8em;
    }
    """
    
    # 將Markdown轉換為HTML
    html_content = markdown.markdown(
        markdown_content, 
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    
    # 添加完整HTML結構和CSS
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>實驗報告: {experiment_name}</title>
        <style>
            {css_content}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">
            生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    # 生成PDF
    try:
        HTML(string=full_html).write_pdf(
            str(output_path),
            stylesheets=[CSS(string=css_content)]
        )
        print(f"PDF報告已成功生成: {output_path}")
    except Exception as e:
        print(f"PDF生成失敗: {str(e)}")
        print("請確保已安裝WeasyPrint及其依賴項。如需幫助，請參考: https://weasyprint.readthedocs.io/en/latest/install.html")
        return None
    
    return str(output_path)


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
    
    try:
        report_path = generate_pdf_report("test_experiment", test_config, test_results)
        if report_path:
            print(f"生成的報告路徑: {report_path}")
    except ImportError:
        print("無法生成PDF報告。請確保已安裝所需的依賴項: pip install weasyprint markdown") 