import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
import joblib
import os
import json


class ScoringModel:
    """基於隨機森林的語音評分模型"""
    
    def __init__(self, n_estimators=100, max_depth=10, min_samples_split=5, 
                 feature_selection=None, n_features_to_select=None):
        """
        初始化評分模型
        
        參數:
            n_estimators (int): 隨機森林中樹的數量
            max_depth (int): 樹的最大深度
            min_samples_split (int): 內部節點再分割所需的最小樣本數
            feature_selection (str): 特徵選擇方法，目前支援 'rfe'
            n_features_to_select (int): 當使用特徵選擇時，選擇的特徵數量
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.feature_selection = feature_selection
        self.n_features_to_select = n_features_to_select
        
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.feature_names = None
        self.is_trained = False
    
    def _prepare_features(self, X, feature_names=None):
        """
        準備特徵（標準化和特徵選擇）
        
        參數:
            X (numpy.ndarray): 特徵矩陣
            feature_names (list, optional): 特徵名稱
            
        返回:
            numpy.ndarray: 處理後的特徵
        """
        if feature_names is not None:
            self.feature_names = feature_names
        
        # 標準化特徵
        X_scaled = self.scaler.transform(X)
        
        # 特徵選擇
        if self.feature_selection == 'rfe' and self.feature_selector is not None:
            X_selected = self.feature_selector.transform(X_scaled)
            return X_selected
        
        return X_scaled
    
    def train(self, X, y, feature_names=None, cv=5):
        """
        訓練模型
        
        參數:
            X (numpy.ndarray): 特徵矩陣
            y (numpy.ndarray): 目標分數
            feature_names (list, optional): 特徵名稱列表
            cv (int): 交叉驗證摺數
            
        返回:
            dict: 訓練結果統計
        """
        if feature_names is not None:
            self.feature_names = feature_names
            
        # 標準化特徵
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # 特徵選擇
        if self.feature_selection == 'rfe':
            n_features = self.n_features_to_select or max(3, X.shape[1] // 3)
            self.feature_selector = RFE(
                estimator=RandomForestRegressor(n_estimators=10, random_state=42),
                n_features_to_select=n_features
            )
            X_scaled = self.feature_selector.fit_transform(X_scaled, y)
            
            # 如果有特徵名稱，保存被選中的特徵
            if self.feature_names is not None:
                self.selected_features = [
                    name for i, name in enumerate(self.feature_names) 
                    if self.feature_selector.support_[i]
                ]
        
        # 超參數優化
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10]
        }
        
        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=param_grid,
            cv=cv,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        
        grid_search.fit(X_scaled, y)
        
        # 更新模型為最佳模型
        self.model = grid_search.best_estimator_
        
        # 交叉驗證結果
        cv_scores = cross_val_score(
            self.model, X_scaled, y, 
            cv=KFold(n_splits=cv, shuffle=True, random_state=42),
            scoring='neg_mean_absolute_error'
        )
        
        # 最終訓練
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # 返回訓練統計
        train_stats = {
            'best_params': grid_search.best_params_,
            'best_score': -grid_search.best_score_,  # MAE，轉回正值
            'cv_mae': -np.mean(cv_scores),
            'cv_mae_std': np.std(cv_scores),
            'feature_importance': self.get_feature_importance()
        }
        
        return train_stats
    
    def predict(self, X):
        """
        預測分數
        
        參數:
            X (numpy.ndarray): 特徵矩陣
            
        返回:
            numpy.ndarray: 預測的分數
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
            
        X_prepared = self._prepare_features(X)
        return self.model.predict(X_prepared)
    
    def evaluate(self, X, y_true):
        """
        評估模型
        
        參數:
            X (numpy.ndarray): 特徵矩陣
            y_true (numpy.ndarray): 真實分數
            
        返回:
            dict: 評估指標
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
            
        X_prepared = self._prepare_features(X)
        y_pred = self.model.predict(X_prepared)
        
        eval_results = {
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'bias': np.mean(y_pred - y_true),
            'predictions': y_pred.tolist(),
            'ground_truth': y_true.tolist()
        }
        
        return eval_results
    
    def get_feature_importance(self):
        """
        獲取特徵重要性
        
        返回:
            dict: 特徵重要性字典
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
            
        importances = self.model.feature_importances_
        
        if self.feature_names is not None:
            if self.feature_selection == 'rfe' and self.feature_selector is not None:
                # 如果使用了特徵選擇，只返回選擇的特徵的重要性
                return {
                    name: float(imp) 
                    for name, imp in zip(self.selected_features, importances)
                }
            else:
                return {
                    name: float(imp) 
                    for name, imp in zip(self.feature_names, importances)
                }
        else:
            return {f"feature_{i}": float(imp) for i, imp in enumerate(importances)}
    
    def save(self, model_dir, model_name="rf_scoring_model"):
        """
        保存模型
        
        參數:
            model_dir (str): 模型保存目錄
            model_name (str): 模型名稱
        """
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
        model_path = os.path.join(model_dir, f"{model_name}.joblib")
        model_meta_path = os.path.join(model_dir, f"{model_name}_meta.json")
        
        # 保存模型
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector
        }, model_path)
        
        # 保存元數據
        meta_data = {
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'min_samples_split': self.min_samples_split,
            'feature_selection': self.feature_selection,
            'n_features_to_select': self.n_features_to_select,
            'feature_names': self.feature_names,
            'selected_features': getattr(self, 'selected_features', None),
            'is_trained': self.is_trained
        }
        
        with open(model_meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
    
    @classmethod
    def load(cls, model_dir, model_name="rf_scoring_model"):
        """
        加載模型
        
        參數:
            model_dir (str): 模型保存目錄
            model_name (str): 模型名稱
            
        返回:
            ScoringModel: 加載的模型
        """
        model_path = os.path.join(model_dir, f"{model_name}.joblib")
        model_meta_path = os.path.join(model_dir, f"{model_name}_meta.json")
        
        if not os.path.exists(model_path) or not os.path.exists(model_meta_path):
            raise FileNotFoundError(f"模型文件或元數據不存在: {model_path}, {model_meta_path}")
            
        # 加載元數據
        with open(model_meta_path, 'r') as f:
            meta_data = json.load(f)
            
        # 創建模型實例
        model_instance = cls(
            n_estimators=meta_data['n_estimators'],
            max_depth=meta_data['max_depth'],
            min_samples_split=meta_data['min_samples_split'],
            feature_selection=meta_data['feature_selection'],
            n_features_to_select=meta_data['n_features_to_select']
        )
        
        # 加載保存的模型
        saved_model = joblib.load(model_path)
        model_instance.model = saved_model['model']
        model_instance.scaler = saved_model['scaler']
        model_instance.feature_selector = saved_model['feature_selector']
        
        # 設置額外屬性
        model_instance.feature_names = meta_data['feature_names']
        if 'selected_features' in meta_data and meta_data['selected_features']:
            model_instance.selected_features = meta_data['selected_features']
        model_instance.is_trained = meta_data['is_trained']
        
        return model_instance


if __name__ == "__main__":
    # 使用示例
    # 隨機生成一些測試數據
    np.random.seed(42)
    X_train = np.random.rand(100, 20)  # 100 樣本, 20 特徵
    y_train = np.random.rand(100) * 5  # 分數範圍 0-5
    
    feature_names = [f"feature_{i}" for i in range(20)]
    
    # 訓練模型
    model = ScoringModel(
        n_estimators=100,
        feature_selection='rfe',
        n_features_to_select=10
    )
    
    train_stats = model.train(X_train, y_train, feature_names=feature_names)
    print("訓練完成，統計信息:")
    print(f"最佳參數: {train_stats['best_params']}")
    print(f"交叉驗證 MAE: {train_stats['cv_mae']:.4f} ± {train_stats['cv_mae_std']:.4f}")
    
    # 特徵重要性
    importance = model.get_feature_importance()
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print("\n前5個重要特徵:")
    for feature, imp in importance_sorted[:5]:
        print(f"{feature}: {imp:.4f}")
    
    # 保存和加載
    model.save("./models")
    loaded_model = ScoringModel.load("./models")
    
    # 測試預測
    X_test = np.random.rand(10, 20)
    y_test = np.random.rand(10) * 5
    
    predictions = loaded_model.predict(X_test)
    eval_results = loaded_model.evaluate(X_test, y_test)
    
    print(f"\n測試集 MAE: {eval_results['mae']:.4f}")
    print(f"測試集 R²: {eval_results['r2']:.4f}")
    print(f"預測偏差: {eval_results['bias']:.4f}") 