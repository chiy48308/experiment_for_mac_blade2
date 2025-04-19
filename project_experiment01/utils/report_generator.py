"""
報告生成器模塊 - 生成實驗報告的工具
"""

import os
import json
import yaml
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from pathlib import Path
import markdown
from jinja2 import Template
import base64
from io import BytesIO
import seaborn as sns


class ReportGenerator:
    """生成實驗報告的類，支持Markdown和HTML格式"""
    
    def __init__(self, reports_dir='reports', experiment_name=None):
        """
        初始化報告生成器
        
        參數:
            reports_dir (str): 報告存儲目錄
            experiment_name (str): 實驗名稱，如果為None則使用時間戳
        """
        self.reports_dir = Path(reports_dir)
        os.makedirs(reports_dir, exist_ok=True)
        
        # 如果沒有提供實驗名稱，使用時間戳
        if experiment_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = f"experiment_{timestamp}"
        
        self.experiment_name = experiment_name
        self.report_data = {
            "title": f"實驗報告: {experiment_name}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "experiment_name": experiment_name,
            "sections": []
        }
        
        # 創建實驗報告目錄
        self.experiment_report_dir = self.reports_dir / experiment_name
        os.makedirs(self.experiment_report_dir, exist_ok=True)
        
        # 圖像目錄
        self.images_dir = self.experiment_report_dir / "images"
        os.makedirs(self.images_dir, exist_ok=True)
    
    def add_title(self, title):
        """設置報告標題"""
        self.report_data["title"] = title
    
    def add_section(self, title, content=None, level=1):
        """
        添加報告章節
        
        參數:
            title (str): 章節標題
            content (str): 章節內容
            level (int): 標題級別 (1-6)
        """
        section = {
            "title": title,
            "level": level,
            "content": content or "",
            "subsections": [],
            "tables": [],
            "figures": []
        }
        
        if level == 1:
            self.report_data["sections"].append(section)
            return section
        else:
            # 找到適當的父章節
            parent_section = self._find_parent_section(level)
            if parent_section:
                parent_section["subsections"].append(section)
            else:
                # 如果找不到合適的父章節，添加到頂層
                self.report_data["sections"].append(section)
            
            return section
    
    def _find_parent_section(self, current_level):
        """查找適合作為父節點的章節"""
        if current_level <= 1 or len(self.report_data["sections"]) == 0:
            return None
        
        # 從最近添加的章節開始搜索
        sections_to_check = self.report_data["sections"]
        
        while current_level > 1:
            current_level -= 1
            
            # 從最後添加的開始檢查
            for section in reversed(sections_to_check):
                if section.get("level", 1) == current_level:
                    return section
                
                # 檢查子章節
                subsections = self._get_latest_subsections(section)
                if subsections:
                    for subsection in reversed(subsections):
                        if subsection.get("level", 1) == current_level:
                            return subsection
            
        return self.report_data["sections"][-1] if self.report_data["sections"] else None
    
    def _get_latest_subsections(self, section):
        """獲取章節的所有子章節"""
        if "subsections" in section:
            return section["subsections"]
        return []
    
    def add_paragraph(self, content, section=None):
        """
        添加段落內容
        
        參數:
            content (str): 段落內容
            section (dict): 要添加到的章節，如果為None則添加到最後一個章節
        """
        if section is None:
            if self.report_data["sections"]:
                section = self.report_data["sections"][-1]
            else:
                section = self.add_section("未命名章節")
        
        if "content" not in section:
            section["content"] = ""
        
        section["content"] += f"\n\n{content}"
    
    def add_table(self, data, headers=None, caption="表格", section=None):
        """
        添加表格
        
        參數:
            data (list or DataFrame): 表格數據
            headers (list): 表頭，可選
            caption (str): 表格標題
            section (dict): 要添加到的章節，如果為None則添加到最後一個章節
        """
        if section is None:
            if self.report_data["sections"]:
                section = self.report_data["sections"][-1]
            else:
                section = self.add_section("未命名章節")
        
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.DataFrame(data, columns=headers)
        
        # 生成Markdown表格
        markdown_table = df.to_markdown(index=False)
        
        # 添加表格到章節
        table_data = {
            "caption": caption,
            "markdown": markdown_table,
            "html": df.to_html(index=False, classes="table table-striped"),
            "data": df.to_dict(orient="records")
        }
        
        if "tables" not in section:
            section["tables"] = []
        
        section["tables"].append(table_data)
        
        # 在內容中引用表格
        table_ref = f"\n\n**{caption}**\n\n{markdown_table}\n"
        self.add_paragraph(table_ref, section)
    
    def add_figure(self, fig=None, image_path=None, caption="圖片", section=None, width=None, height=None, dpi=150):
        """
        添加圖片
        
        參數:
            fig (matplotlib.figure.Figure): matplotlib圖形對象
            image_path (str): 圖像文件路徑（與fig二選一）
            caption (str): 圖片標題
            section (dict): 要添加到的章節，如果為None則添加到最後一個章節
            width (int): 圖片寬度（僅用於HTML輸出）
            height (int): 圖片高度（僅用於HTML輸出）
            dpi (int): 圖片DPI
        """
        if section is None:
            if self.report_data["sections"]:
                section = self.report_data["sections"][-1]
            else:
                section = self.add_section("未命名章節")
        
        if fig is not None:
            # 保存圖片到文件
            img_filename = f"{self.experiment_name}_{len(section.get('figures', []))}.png"
            img_path = self.images_dir / img_filename
            fig.savefig(img_path, dpi=dpi, bbox_inches='tight')
            
            # 獲取base64編碼的圖片數據（用於HTML）
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
        elif image_path is not None:
            # 使用提供的圖片路徑
            img_filename = os.path.basename(image_path)
            img_path = Path(image_path)
            
            # 複製圖片到報告目錄
            import shutil
            target_path = self.images_dir / img_filename
            shutil.copy(img_path, target_path)
            img_path = target_path
            
            # 讀取圖片生成base64
            with open(img_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        else:
            raise ValueError("必須提供fig或image_path參數")
        
        # 添加圖片到章節
        figure_data = {
            "caption": caption,
            "path": str(img_path),
            "filename": img_filename,
            "base64": img_base64,
            "width": width,
            "height": height
        }
        
        if "figures" not in section:
            section["figures"] = []
        
        section["figures"].append(figure_data)
        
        # 在內容中引用圖片
        rel_path = os.path.relpath(img_path, self.reports_dir)
        figure_ref = f"\n\n**{caption}**\n\n![{caption}]({rel_path})\n"
        self.add_paragraph(figure_ref, section)
    
    def add_metrics_summary(self, metrics, section_title="實驗指標摘要"):
        """
        添加指標摘要章節
        
        參數:
            metrics (dict): 指標數據字典
            section_title (str): 章節標題
        """
        section = self.add_section(section_title)
        
        # 轉換指標為表格格式
        if metrics:
            metrics_table = []
            for name, values in metrics.items():
                if isinstance(values, list):
                    # 假設列表最後一個是最新值
                    value = values[-1]["value"] if values else "N/A"
                    step = values[-1].get("step", "N/A") if values else "N/A"
                    metrics_table.append({
                        "指標名稱": name,
                        "值": value,
                        "步驟": step
                    })
                else:
                    # 假設直接是數值
                    metrics_table.append({
                        "指標名稱": name,
                        "值": values,
                        "步驟": "N/A"
                    })
            
            self.add_table(metrics_table, caption="實驗指標表", section=section)
            
            # 如果有多個時間步的指標，繪製趨勢圖
            for name, values in metrics.items():
                if isinstance(values, list) and len(values) > 1:
                    try:
                        steps = [v.get("step", i) for i, v in enumerate(values)]
                        metric_values = [v["value"] for v in values]
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(steps, metric_values, marker='o', linestyle='-')
                        ax.set_title(f"{name} 趨勢")
                        ax.set_xlabel("步驟")
                        ax.set_ylabel(name)
                        ax.grid(True)
                        
                        self.add_figure(fig, caption=f"{name} 趨勢圖", section=section)
                        plt.close(fig)
                    except Exception as e:
                        print(f"繪製 {name} 趨勢圖時出錯: {e}")
    
    def add_comparison_table(self, stack_results, metrics, section_title="實驗堆疊比較"):
        """
        添加實驗堆疊比較表
        
        參數:
            stack_results (dict): 不同堆疊的結果 {stack_name: {metric: value}}
            metrics (list): 要比較的指標列表
            section_title (str): 章節標題
        """
        section = self.add_section(section_title)
        
        # 創建比較表
        comparison_data = []
        for stack_name, results in stack_results.items():
            row = {"堆疊": stack_name}
            for metric in metrics:
                row[metric] = results.get(metric, "N/A")
            comparison_data.append(row)
        
        df = pd.DataFrame(comparison_data)
        self.add_table(df, caption="堆疊性能比較", section=section)
        
        # 為每個指標生成比較圖
        for metric in metrics:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                stacks = [result["堆疊"] for result in comparison_data]
                values = [result.get(metric, 0) for result in comparison_data]
                
                # 繪製條形圖
                sns.barplot(x=stacks, y=values, ax=ax)
                ax.set_title(f"{metric} 比較")
                ax.set_xlabel("實驗堆疊")
                ax.set_ylabel(metric)
                ax.tick_params(axis='x', rotation=45)
                
                self.add_figure(fig, caption=f"{metric} 堆疊比較", section=section)
                plt.close(fig)
            except Exception as e:
                print(f"繪製 {metric} 比較圖時出錯: {e}")
    
    def add_experiment_config(self, config, section_title="實驗配置"):
        """
        添加實驗配置章節
        
        參數:
            config (dict): 實驗配置
            section_title (str): 章節標題
        """
        section = self.add_section(section_title)
        
        # 格式化配置為YAML字符串
        config_yaml = yaml.dump(config, default_flow_style=False, allow_unicode=True)
        self.add_paragraph(f"```yaml\n{config_yaml}\n```", section)
    
    def add_conclusion(self, conclusion_text, recommendations=None):
        """
        添加結論章節
        
        參數:
            conclusion_text (str): 結論文本
            recommendations (list): 推薦項列表
        """
        section = self.add_section("結論和建議")
        self.add_paragraph(conclusion_text, section)
        
        if recommendations:
            rec_text = "### 建議\n\n"
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"{i}. {rec}\n"
            self.add_paragraph(rec_text, section)
    
    def generate_markdown(self, output_path=None):
        """
        生成Markdown格式報告
        
        參數:
            output_path (str): 輸出文件路徑，如果為None則自動生成
        
        返回:
            str: 輸出文件路徑
        """
        if output_path is None:
            output_path = self.experiment_report_dir / f"{self.experiment_name}_report.md"
        
        md_content = f"# {self.report_data['title']}\n\n"
        md_content += f"生成日期: {self.report_data['date']}\n\n"
        
        # 生成目錄
        md_content += "## 目錄\n\n"
        for section in self.report_data["sections"]:
            section_marker = "#" * section["level"]
            md_content += f"- [{section['title']}](#{section['title'].lower().replace(' ', '-')})\n"
            for subsection in section.get("subsections", []):
                subsection_marker = "#" * subsection["level"]
                md_content += f"  - [{subsection['title']}](#{subsection['title'].lower().replace(' ', '-')})\n"
        
        md_content += "\n\n---\n\n"
        
        # 添加章節內容
        for section in self.report_data["sections"]:
            md_content += self._section_to_markdown(section)
        
        # 寫入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(output_path)
    
    def _section_to_markdown(self, section, base_level=0):
        """將章節轉換為Markdown格式"""
        level = section.get("level", 1) + base_level
        section_marker = "#" * level
        
        md = f"{section_marker} {section['title']}\n\n"
        
        if section.get("content"):
            md += f"{section['content']}\n\n"
        
        # 添加子章節
        for subsection in section.get("subsections", []):
            md += self._section_to_markdown(subsection, base_level)
        
        return md
    
    def generate_html(self, output_path=None, template=None):
        """
        生成HTML格式報告
        
        參數:
            output_path (str): 輸出文件路徑，如果為None則自動生成
            template (str): 自定義HTML模板
        
        返回:
            str: 輸出文件路徑
        """
        if output_path is None:
            output_path = self.experiment_report_dir / f"{self.experiment_name}_report.html"
        
        # 預設HTML模板
        if template is None:
            template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{{ title }}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    h1, h2, h3, h4, h5, h6 {
                        color: #2c3e50;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1em 0;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #f2f2f2;
                    }
                    tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    img {
                        max-width: 100%;
                        height: auto;
                        margin: 1em 0;
                    }
                    .figure {
                        text-align: center;
                        margin: 1.5em 0;
                    }
                    .figure img {
                        max-width: 800px;
                        border: 1px solid #ddd;
                        padding: 5px;
                    }
                    .figure figcaption {
                        font-style: italic;
                        margin-top: 5px;
                    }
                    .date {
                        color: #7f8c8d;
                        font-style: italic;
                        margin-bottom: 2em;
                    }
                    pre {
                        background-color: #f8f8f8;
                        border: 1px solid #ddd;
                        border-radius: 3px;
                        padding: 1em;
                        overflow-x: auto;
                    }
                    code {
                        font-family: monospace;
                        background-color: #f8f8f8;
                        padding: 2px 4px;
                        border-radius: 3px;
                    }
                    blockquote {
                        margin: 1em 0;
                        padding: 0.5em 1em;
                        border-left: 4px solid #ccc;
                        background-color: #f9f9f9;
                    }
                    .toc {
                        background-color: #f8f8f8;
                        padding: 1em;
                        border-radius: 5px;
                        margin-bottom: 2em;
                    }
                </style>
            </head>
            <body>
                <h1>{{ title }}</h1>
                <div class="date">{{ date }}</div>
                
                <div class="toc">
                    <h2>目錄</h2>
                    <ul>
                    {% for section in sections %}
                        <li><a href="#section-{{ loop.index }}">{{ section.title }}</a>
                        {% if section.subsections %}
                            <ul>
                            {% for subsection in section.subsections %}
                                <li><a href="#section-{{ loop.index }}-{{ loop.index }}">{{ subsection.title }}</a></li>
                            {% endfor %}
                            </ul>
                        {% endif %}
                        </li>
                    {% endfor %}
                    </ul>
                </div>
                
                {% for section in sections %}
                <div id="section-{{ loop.index }}">
                    <h{{ section.level }}>{{ section.title }}</h{{ section.level }}>
                    {{ section.content|markdown }}
                    
                    {% for figure in section.figures %}
                    <div class="figure">
                        <img src="data:image/png;base64,{{ figure.base64 }}" 
                             alt="{{ figure.caption }}"
                             {% if figure.width %}width="{{ figure.width }}"{% endif %}
                             {% if figure.height %}height="{{ figure.height }}"{% endif %}>
                        <figcaption>{{ figure.caption }}</figcaption>
                    </div>
                    {% endfor %}
                    
                    {% for subsection in section.subsections %}
                    <div id="section-{{ loop.parent.index }}-{{ loop.index }}">
                        <h{{ subsection.level }}>{{ subsection.title }}</h{{ subsection.level }}>
                        {{ subsection.content|markdown }}
                        
                        {% for figure in subsection.figures %}
                        <div class="figure">
                            <img src="data:image/png;base64,{{ figure.base64 }}" 
                                 alt="{{ figure.caption }}"
                                 {% if figure.width %}width="{{ figure.width }}"{% endif %}
                                 {% if figure.height %}height="{{ figure.height }}"{% endif %}>
                            <figcaption>{{ figure.caption }}</figcaption>
                        </div>
                        {% endfor %}
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
                
            </body>
            </html>
            """
        
        # 自定義Jinja2過濾器將Markdown轉換為HTML
        def markdown_filter(text):
            return markdown.markdown(text, extensions=['tables', 'fenced_code', 'codehilite'])
        
        # 建立Jinja2模板
        jinja_template = Template(template)
        jinja_template.environment.filters['markdown'] = markdown_filter
        
        # 渲染HTML
        html_content = jinja_template.render(**self.report_data)
        
        # 寫入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def save_report_data(self, output_path=None):
        """
        保存報告數據為JSON文件
        
        參數:
            output_path (str): 輸出文件路徑，如果為None則自動生成
        
        返回:
            str: 輸出文件路徑
        """
        if output_path is None:
            output_path = self.experiment_report_dir / f"{self.experiment_name}_report_data.json"
        
        # 轉換Base64數據以避免JSON文件過大
        report_data_copy = self._prepare_report_data_for_json()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data_copy, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _prepare_report_data_for_json(self):
        """準備報告數據以便序列化為JSON"""
        import copy
        report_data_copy = copy.deepcopy(self.report_data)
        
        # 處理所有章節中的圖像資料
        def process_section(section):
            if "figures" in section:
                for figure in section["figures"]:
                    # 移除Base64數據，僅保留路徑引用
                    if "base64" in figure:
                        figure["base64"] = "[圖像數據已從JSON中移除]"
            
            # 處理子章節
            for subsection in section.get("subsections", []):
                process_section(subsection)
        
        for section in report_data_copy["sections"]:
            process_section(section)
        
        return report_data_copy
    
    def generate_all_formats(self):
        """生成所有格式的報告"""
        md_path = self.generate_markdown()
        html_path = self.generate_html()
        json_path = self.save_report_data()
        
        return {
            "markdown": md_path,
            "html": html_path,
            "json": json_path
        } 