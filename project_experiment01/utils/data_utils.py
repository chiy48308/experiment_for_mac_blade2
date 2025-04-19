#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import numpy as np
import pandas as pd
from pathlib import Path


def load_dataset(config_path):
    """
    加載數據集配置文件
    
    參數:
        config_path (str): 配置文件路徑
        
    返回:
        dict: 數據集字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    dataset = {
        'audio_files': {},
        'azure_scores': {},
        'teacher_audio': {},
        'reference_segments': {}
    }
    
    # 加載音頻文件
    audio_dir = config.get('audio_dir', 'data/raw')
    for file_pattern in config.get('include_patterns', ['*.wav']):
        for file_path in Path(audio_dir).glob(file_pattern):
            file_id = file_path.stem
            dataset['audio_files'][file_id] = str(file_path)
    
    # 加載Azure分數
    azure_results_path = config.get('azure_results_path', 'data/azure_results')
    azure_file = os.path.join(azure_results_path, 'azure_scores.json')
    if os.path.exists(azure_file):
        with open(azure_file, 'r', encoding='utf-8') as f:
            azure_scores = json.load(f)
            dataset['azure_scores'] = azure_scores
    
    # 加載教師音頻（如果有）
    teacher_audio_dir = config.get('teacher_audio_dir')
    if teacher_audio_dir and os.path.exists(teacher_audio_dir):
        for file_path in Path(teacher_audio_dir).glob('*.wav'):
            file_id = file_path.stem.replace('_teacher', '')
            dataset['teacher_audio'][file_id] = str(file_path)
    
    # 加載參考分割（如果有）
    reference_segments_file = config.get('reference_segments_file')
    if reference_segments_file and os.path.exists(reference_segments_file):
        with open(reference_segments_file, 'r', encoding='utf-8') as f:
            dataset['reference_segments'] = json.load(f)
    
    return dataset


def prepare_features(features_dict, azure_scores):
    """
    準備用於訓練評分模型的特徵
    
    參數:
        features_dict (dict): 特徵字典 {file_id: {extractor_name: [(features, duration)]}}
        azure_scores (dict): Azure分數 {file_id: score}
        
    返回:
        tuple: (特徵矩陣, 目標分數, 特徵名稱)
    """
    X_list = []
    y_list = []
    feature_names = []
    
    # 檢查特徵維度
    first_file = next(iter(features_dict.values()))
    first_extractor = next(iter(first_file.values()))
    first_segment = first_extractor[0][0]  # 獲取第一個特徵矩陣
    
    # 遍歷每個文件
    for file_id, extractors in features_dict.items():
        if file_id not in azure_scores:
            continue
            
        file_score = azure_scores[file_id]
        
        # 對每個提取器的每個段落
        for extractor_name, segments in extractors.items():
            for i, (segment_features, duration) in enumerate(segments):
                # 計算段落級特徵（均值和標準差）
                segment_mean = np.mean(segment_features, axis=0)
                segment_std = np.std(segment_features, axis=0)
                
                # 如果是第一次遇到此提取器，添加特徵名稱
                if len(feature_names) == 0:
                    for j in range(segment_mean.shape[0]):
                        feature_names.append(f"{extractor_name}_mean_{j}")
                    for j in range(segment_std.shape[0]):
                        feature_names.append(f"{extractor_name}_std_{j}")
                
                # 組合特徵
                combined_features = np.concatenate([segment_mean, segment_std])
                
                # 添加到特徵和目標列表
                X_list.append(combined_features)
                y_list.append(file_score)
    
    # 轉換為numpy數組
    X = np.array(X_list)
    y = np.array(y_list)
    
    return X, y, feature_names


def normalize_features(features):
    """
    標準化特徵
    
    參數:
        features (numpy.ndarray): 特徵矩陣
        
    返回:
        numpy.ndarray: 標準化後的特徵
    """
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0] = 1  # 防止除零錯誤
    
    return (features - mean) / std


def split_train_test(features, labels, test_size=0.2, random_state=42):
    """
    分割訓練集和測試集
    
    參數:
        features (numpy.ndarray): 特徵矩陣
        labels (numpy.ndarray): 標籤向量
        test_size (float): 測試集比例
        random_state (int): 隨機種子
        
    返回:
        tuple: (X_train, X_test, y_train, y_test)
    """
    from sklearn.model_selection import train_test_split
    return train_test_split(features, labels, test_size=test_size, random_state=random_state)


def create_dataset_config_template(output_path='data/dataset_config.yaml'):
    """
    創建數據集配置模板
    
    參數:
        output_path (str): 輸出路徑
    """
    config = {
        'audio_dir': 'data/raw',
        'azure_results_path': 'data/azure_results',
        'teacher_audio_dir': 'data/teacher',
        'reference_segments_file': 'data/reference_segments.json',
        'include_patterns': ['*.wav'],
        'exclude_patterns': ['*noise*.wav', '*test*.wav'],
        'split': {
            'train_ratio': 0.8,
            'validation_ratio': 0.1,
            'test_ratio': 0.1,
            'random_seed': 42
        }
    }
    
    # 確保目錄存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"已創建數據集配置模板: {output_path}")


def generate_batch(features_dict, azure_scores, batch_size=32):
    """
    生成訓練批次
    
    參數:
        features_dict (dict): 特徵字典
        azure_scores (dict): Azure分數
        batch_size (int): 批次大小
        
    返回:
        generator: 生成 (X_batch, y_batch) 元組
    """
    file_ids = list(features_dict.keys())
    np.random.shuffle(file_ids)
    
    X_batch = []
    y_batch = []
    
    for file_id in file_ids:
        if file_id not in azure_scores:
            continue
            
        file_score = azure_scores[file_id]
        
        for extractor_name, segments in features_dict[file_id].items():
            for segment_features, duration in segments:
                # 計算段落級特徵
                segment_mean = np.mean(segment_features, axis=0)
                segment_std = np.std(segment_features, axis=0)
                combined_features = np.concatenate([segment_mean, segment_std])
                
                X_batch.append(combined_features)
                y_batch.append(file_score)
                
                if len(X_batch) == batch_size:
                    yield np.array(X_batch), np.array(y_batch)
                    X_batch = []
                    y_batch = []
    
    # 返回剩餘的樣本
    if X_batch:
        yield np.array(X_batch), np.array(y_batch)


if __name__ == "__main__":
    # 創建配置模板
    create_dataset_config_template()
    
    # 測試加載數據集
    dataset = load_dataset('data/dataset_config.yaml')
    print(f"加載了 {len(dataset['audio_files'])} 個音頻文件")
    
    # 假設我們有一些特徵和分數進行測試
    dummy_features = {
        'file1': {
            'MFCC': [(np.random.rand(100, 39), 2.5)]
        }
    }
    
    dummy_scores = {'file1': 4.5}
    
    X, y, feature_names = prepare_features(dummy_features, dummy_scores)
    print(f"特徵形狀: {X.shape}")
    print(f"標籤形狀: {y.shape}")
    print(f"特徵名稱數量: {len(feature_names)}") 