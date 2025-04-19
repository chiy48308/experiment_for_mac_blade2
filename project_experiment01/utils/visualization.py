#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非互動式後端
import seaborn as sns
from sklearn.metrics import mean_absolute_error, r2_score
import os


class PlotResults:
    """生成實驗結果可視化的類"""
    
    def __init__(self):
        """初始化繪圖樣式"""
        # 設置繪圖樣式
        sns.set_style("whitegrid")
        plt.rcParams.update({
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.figsize': (10, 6)
        })
    
    def plot_scatter(self, system_scores, azure_scores, output_path, title=None):
        """
        繪製系統分數與Azure分數的散點圖
        
        參數:
            system_scores (numpy.ndarray): 系統產生的分數
            azure_scores (numpy.ndarray): Azure參考分數
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
        """
        # 計算相關指標
        mae = mean_absolute_error(azure_scores, system_scores)
        r2 = r2_score(azure_scores, system_scores)
        corr = np.corrcoef(system_scores, azure_scores)[0, 1]
        
        # 創建散點圖
        plt.figure(figsize=(10, 8))
        
        # 散點圖
        sns.scatterplot(x=azure_scores, y=system_scores, alpha=0.6)
        
        # 添加回歸線
        sns.regplot(x=azure_scores, y=system_scores, scatter=False, 
                   line_kws={"color": "red", "lw": 2})
        
        # 添加對角線（理想情況）
        min_val = min(min(azure_scores), min(system_scores))
        max_val = max(max(azure_scores), max(system_scores))
        plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='理想情況')
        
        # 設置標題和標籤
        plt.title(title or '系統分數 vs Azure分數比較')
        plt.xlabel('Azure分數')
        plt.ylabel('系統分數')
        
        # 添加統計信息
        plt.annotate(f'MAE: {mae:.4f}\nR²: {r2:.4f}\nCorr: {corr:.4f}',
                    xy=(0.05, 0.95), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                    ha='left', va='top')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        return output_path
    
    def plot_residuals(self, system_scores, azure_scores, output_path, title=None):
        """
        繪製殘差圖
        
        參數:
            system_scores (numpy.ndarray): 系統產生的分數
            azure_scores (numpy.ndarray): Azure參考分數
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
        """
        # 計算殘差
        residuals = system_scores - azure_scores
        
        # 創建殘差圖
        plt.figure(figsize=(10, 8))
        
        # 散點圖
        sns.scatterplot(x=azure_scores, y=residuals, alpha=0.6)
        
        # 添加水平線 (y=0)
        plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        
        # 添加趨勢線
        sns.regplot(x=azure_scores, y=residuals, scatter=False, 
                    line_kws={"color": "green", "lw": 2})
        
        # 設置標題和標籤
        plt.title(title or '分數殘差分析')
        plt.xlabel('Azure分數')
        plt.ylabel('殘差 (系統分數 - Azure分數)')
        
        # 計算統計數據
        mean_residual = np.mean(residuals)
        std_residual = np.std(residuals)
        
        # 添加統計信息
        plt.annotate(f'平均殘差: {mean_residual:.4f}\n標準差: {std_residual:.4f}',
                    xy=(0.05, 0.95), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                    ha='left', va='top')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        return output_path
    
    def plot_feature_importance(self, feature_importance, output_path, 
                               title=None, top_n=20):
        """
        繪製特徵重要性圖
        
        參數:
            feature_importance (dict): 特徵重要性字典 {feature_name: importance}
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
            top_n (int): 顯示前n個重要特徵
        """
        # 將字典轉換為排序列表
        importance_items = sorted(feature_importance.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        # 取前N個重要特徵
        if top_n and len(importance_items) > top_n:
            importance_items = importance_items[:top_n]
        
        # 分離特徵名稱和重要性值
        features = [item[0] for item in importance_items]
        importances = [item[1] for item in importance_items]
        
        # 創建水平條形圖
        plt.figure(figsize=(12, max(6, len(features) * 0.3)))
        
        # 繪製條形圖
        bars = plt.barh(features, importances, alpha=0.8)
        
        # 設置漸變顏色
        colors = plt.cm.viridis(np.linspace(0, 1, len(features)))
        for i, bar in enumerate(bars):
            bar.set_color(colors[i])
        
        # 設置標題和標籤
        plt.title(title or '特徵重要性分析')
        plt.xlabel('重要性')
        plt.ylabel('特徵')
        
        # 調整圖的格式
        plt.gca().invert_yaxis()  # 從上到下顯示重要性降序
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_bland_altman(self, system_scores, azure_scores, output_path, title=None):
        """
        繪製Bland-Altman圖（一致性分析）
        
        參數:
            system_scores (numpy.ndarray): 系統產生的分數
            azure_scores (numpy.ndarray): Azure參考分數
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
        """
        # 計算差異和平均值
        diff = system_scores - azure_scores
        mean = np.mean([system_scores, azure_scores], axis=0)
        
        # 計算平均差異和標準差
        md = np.mean(diff)
        sd = np.std(diff)
        
        # 創建圖形
        plt.figure(figsize=(10, 8))
        
        # 散點圖
        plt.scatter(mean, diff, alpha=0.6)
        
        # 添加平均線和±1.96SD線
        plt.axhline(md, color='blue', linestyle='-', label=f'平均差異: {md:.4f}')
        plt.axhline(md + 1.96 * sd, color='red', linestyle='--', 
                   label=f'+1.96 SD: {md + 1.96*sd:.4f}')
        plt.axhline(md - 1.96 * sd, color='red', linestyle='--', 
                   label=f'-1.96 SD: {md - 1.96*sd:.4f}')
        
        # 設置標題和標籤
        plt.title(title or 'Bland-Altman 一致性分析')
        plt.xlabel('測量平均值 ((系統 + Azure) / 2)')
        plt.ylabel('測量差異 (系統 - Azure)')
        plt.legend(loc='best')
        
        # 計算落在±1.96SD範圍內的百分比
        within_limits = ((diff >= md - 1.96 * sd) & (diff <= md + 1.96 * sd)).sum()
        percentage = (within_limits / len(diff)) * 100
        
        # 添加統計信息
        plt.annotate(f'95%置信區間內: {percentage:.1f}%\n'
                    f'平均差異: {md:.4f}\n'
                    f'標準差: {sd:.4f}',
                    xy=(0.05, 0.05), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                    ha='left', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        return output_path
    
    def plot_segmentation_comparison(self, vad_segments, reference_segments, 
                                    audio_length, output_path, title=None):
        """
        繪製VAD分割與參考分割比較圖
        
        參數:
            vad_segments (list): VAD產生的分割 [(start1, end1), ...]
            reference_segments (list): 參考分割 [(start1, end1), ...]
            audio_length (float): 音頻總長度（秒）
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
        """
        plt.figure(figsize=(12, 6))
        
        # 繪製參考分割
        for i, (start, end) in enumerate(reference_segments):
            plt.plot([start, end], [1, 1], 'g-', linewidth=5, solid_capstyle='butt', 
                     label='參考分割' if i == 0 else "")
        
        # 繪製VAD分割
        for i, (start, end) in enumerate(vad_segments):
            plt.plot([start, end], [0.5, 0.5], 'r-', linewidth=5, solid_capstyle='butt', 
                     label='VAD分割' if i == 0 else "")
        
        # 計算重疊區域
        overlaps = []
        for ref_start, ref_end in reference_segments:
            for vad_start, vad_end in vad_segments:
                overlap_start = max(ref_start, vad_start)
                overlap_end = min(ref_end, vad_end)
                
                if overlap_end > overlap_start:
                    overlaps.append((overlap_start, overlap_end))
        
        # 繪製重疊區域
        for i, (start, end) in enumerate(overlaps):
            plt.plot([start, end], [0.75, 0.75], 'b-', linewidth=5, solid_capstyle='butt', 
                    label='重疊區域' if i == 0 else "")
        
        # 設置圖形參數
        plt.yticks([0.5, 0.75, 1], ['VAD', '重疊', '參考'])
        plt.xlim(0, audio_length)
        plt.ylim(0, 1.5)
        plt.xlabel('時間 (秒)')
        plt.title(title or 'VAD分割與參考分割比較')
        plt.legend(loc='upper right')
        
        # 計算覆蓋率
        ref_total = sum(end - start for start, end in reference_segments)
        overlap_total = sum(end - start for start, end in overlaps)
        coverage = overlap_total / ref_total * 100 if ref_total > 0 else 0
        
        # 添加統計信息
        plt.annotate(f'參考區段: {len(reference_segments)}\n'
                    f'VAD區段: {len(vad_segments)}\n'
                    f'重疊覆蓋率: {coverage:.1f}%',
                    xy=(0.02, 0.95), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
                    ha='left', va='top')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        return output_path
    
    def plot_metrics_comparison(self, metrics_dict, output_path, title=None, 
                              sort_by=None, ascending=False):
        """
        繪製不同Stack的評估指標比較圖
        
        參數:
            metrics_dict (dict): 指標字典 {stack_name: {metric1: value1, ...}}
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
            sort_by (str, optional): 排序依據的指標名稱
            ascending (bool): 是否升序排序
        """
        # 轉換為DataFrame
        df = pd.DataFrame.from_dict(metrics_dict, orient='index')
        
        # 排序（如果指定）
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=ascending)
        
        # 為每個指標創建子圖
        n_metrics = len(df.columns)
        fig, axes = plt.subplots(n_metrics, 1, figsize=(12, n_metrics * 3), sharex=True)
        
        # 確保軸是列表
        if n_metrics == 1:
            axes = [axes]
        
        # 繪製每個指標的條形圖
        for i, metric in enumerate(df.columns):
            ax = axes[i]
            colors = plt.cm.viridis(np.linspace(0, 1, len(df)))
            bars = ax.bar(df.index, df[metric], alpha=0.7)
            
            # 為每個條形設置顏色
            for j, bar in enumerate(bars):
                bar.set_color(colors[j])
                
            # 在條形上方添加數值標籤
            for j, value in enumerate(df[metric]):
                ax.text(j, value, f'{value:.3f}', ha='center', va='bottom')
            
            ax.set_title(f'{metric} 比較')
            ax.set_ylabel(metric)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 設置整體標題
        fig.suptitle(title or 'Stack評估指標比較', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # 為整體標題留出空間
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_correlation_matrix(self, features, labels, feature_names, output_path, title=None):
        """
        繪製特徵與目標的相關矩陣
        
        參數:
            features (numpy.ndarray): 特徵矩陣
            labels (numpy.ndarray): 標籤向量
            feature_names (list): 特徵名稱列表
            output_path (str): 輸出圖片路徑
            title (str, optional): 圖片標題
        """
        # 將特徵和標籤合併為一個矩陣
        data = np.column_stack([features, labels])
        
        # 創建列名，添加目標列
        columns = feature_names + ['目標分數']
        
        # 計算相關矩陣
        corr_matrix = np.corrcoef(data, rowvar=False)
        
        # 創建熱力圖
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        # 創建自定義顏色映射
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        
        # 繪製熱力圖
        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                   square=True, linewidths=.5, cbar_kws={"shrink": .5}, 
                   annot=False)
        
        # 設置標題和標籤
        plt.title(title or '特徵相關性矩陣')
        
        # 保存圖片
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 另外創建一個與目標分數的相關性圖
        target_corr = corr_matrix[-1, :-1]  # 目標與所有特徵的相關性
        
        # 將特徵名稱和相關性組合並排序
        corr_pairs = list(zip(feature_names, target_corr))
        corr_pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        
        # 分離排序後的名稱和相關性
        sorted_names = [pair[0] for pair in corr_pairs]
        sorted_corrs = [pair[1] for pair in corr_pairs]
        
        # 取前20個相關性最強的特徵
        if len(sorted_names) > 20:
            sorted_names = sorted_names[:20]
            sorted_corrs = sorted_corrs[:20]
        
        # 創建條形圖
        plt.figure(figsize=(12, 8))
        colors = plt.cm.RdBu_r(np.linspace(0, 1, len(sorted_corrs)))
        bars = plt.barh(sorted_names, sorted_corrs, alpha=0.7)
        
        # 為每個條形設置顏色
        for i, bar in enumerate(bars):
            bar.set_color(colors[i])
        
        # 添加垂直線（零相關性）
        plt.axvline(x=0, color='k', linestyle='-', alpha=.3)
        
        # 設置標題和標籤
        plt.title('特徵與目標分數的相關性')
        plt.xlabel('相關係數')
        
        # 保存第二張圖
        base_name, ext = os.path.splitext(output_path)
        second_output = f"{base_name}_target_corr{ext}"
        plt.tight_layout()
        plt.savefig(second_output, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path, second_output


# 全局變數，在import時初始化
plot_results = PlotResults()


if __name__ == "__main__":
    # 測試代碼
    np.random.seed(42)
    
    # 生成隨機數據
    system_scores = np.random.rand(100) * 5
    azure_scores = system_scores + np.random.randn(100) * 0.5
    
    # 測試各種圖形
    plot_results.plot_scatter(system_scores, azure_scores, "scatter_test.png")
    plot_results.plot_residuals(system_scores, azure_scores, "residuals_test.png")
    plot_results.plot_bland_altman(system_scores, azure_scores, "bland_altman_test.png")
    
    # 生成假特徵重要性
    feature_importance = {f"feature_{i}": np.random.rand() for i in range(30)}
    plot_results.plot_feature_importance(feature_importance, "feature_importance_test.png")
    
    # 生成假分割數據
    vad_segments = [(0.5, 1.5), (2.0, 3.5), (4.0, 5.5)]
    reference_segments = [(0.6, 1.6), (2.1, 3.6), (4.1, 5.6), (6.0, 7.0)]
    plot_results.plot_segmentation_comparison(vad_segments, reference_segments, 8.0, 
                                            "segmentation_test.png")
    
    # 生成假指標比較數據
    metrics_dict = {
        'Stack1': {'MAE': 0.45, 'R2': 0.85, 'Corr': 0.92},
        'Stack2': {'MAE': 0.38, 'R2': 0.89, 'Corr': 0.94},
        'Stack3': {'MAE': 0.42, 'R2': 0.86, 'Corr': 0.93},
        'Stack4': {'MAE': 0.35, 'R2': 0.90, 'Corr': 0.95}
    }
    plot_results.plot_metrics_comparison(metrics_dict, "metrics_comparison_test.png", 
                                      sort_by='MAE', ascending=True)
    
    print("測試圖形已生成!") 