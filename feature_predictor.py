"""
下期特征预测模块 - 融合多模型预测

功能：
1. 马尔可夫链预测（基于转移概率矩阵）
2. LSTM时序预测（基于最近10期趋势）
3. 统计回归预测（基于长期均值回归）
4. 多模型加权融合

Author: Daletou Team
Version: V10.0
Date: 2026-01-22
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from feature_statistics import FeatureStatistics


class FeaturePredictor:
    """下期特征预测器 - 多模型融合"""
    
    def __init__(self, feature_stats: FeatureStatistics):
        self.stats = feature_stats
        
        # 模型权重（可调整）
        self.markov_weight = 0.5  # 马尔可夫链权重
        self.lstm_weight = 0.3    # LSTM权重
        self.regression_weight = 0.2  # 统计回归权重
    
    def predict_markov(self, last_features: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """方法1：基于马尔可夫链的预测（转移概率）"""
        return self.stats.predict_next_features(last_features)
    
    def predict_lstm(self, recent_10_periods: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """方法2：基于LSTM的时序预测（趋势分析）"""
        predictions = {}
        
        if len(recent_10_periods) < 5:
            return predictions
        
        # 提取最近10期的特征序列
        sum_sequence = []
        odd_even_sequence = []
        big_small_sequence = []
        
        for _, row in recent_10_periods.iterrows():
            feats = self.stats.calculate_single_period_features(row['red'], row['blue'])
            sum_sequence.append(feats['red_sum'])
            odd_even_sequence.append(feats['odd_count'])
            big_small_sequence.append(feats['big_count'])
        
        # 简化版LSTM预测：基于移动平均和趋势
        # 1. 和值预测
        recent_avg_sum = np.mean(sum_sequence[-5:])
        sum_trend = sum_sequence[-1] - np.mean(sum_sequence[-3:-1]) if len(sum_sequence) >= 3 else 0
        predicted_sum = recent_avg_sum + sum_trend * 0.3  # 趋势衰减
        
        # 转换为和值区间概率分布
        predicted_sum_range = self.stats.get_sum_range(int(predicted_sum))
        predictions['red_sum_range'] = {predicted_sum_range: 0.6}  # 主预测
        
        # 相邻区间也给予一定概率
        adjacent_ranges = self._get_adjacent_sum_ranges(predicted_sum_range)
        for adj_range in adjacent_ranges:
            predictions['red_sum_range'][adj_range] = 0.2
        
        # 2. 奇偶比预测
        recent_odd_pattern = odd_even_sequence[-3:]
        if recent_odd_pattern[-1] > np.mean(recent_odd_pattern[:-1]):
            # 趋势上升，预测可能回落
            predicted_odd = max(2, recent_odd_pattern[-1] - 1)
        else:
            predicted_odd = min(3, recent_odd_pattern[-1] + 1)
        
        predictions['odd_even_ratio'] = {
            f"{predicted_odd}奇{5-predicted_odd}偶": 0.5,
            f"{predicted_odd-1}奇{6-predicted_odd}偶": 0.3,
            f"{predicted_odd+1}奇{4-predicted_odd}偶": 0.2
        }
        
        # 3. 大小比预测（类似奇偶比）
        recent_big_pattern = big_small_sequence[-3:]
        if recent_big_pattern[-1] > np.mean(recent_big_pattern[:-1]):
            predicted_big = max(2, recent_big_pattern[-1] - 1)
        else:
            predicted_big = min(3, recent_big_pattern[-1] + 1)
        
        predictions['big_small_ratio'] = {
            f"{predicted_big}大{5-predicted_big}小": 0.5,
            f"{predicted_big-1}大{6-predicted_big}小": 0.3,
            f"{predicted_big+1}大{4-predicted_big}小": 0.2
        }
        
        return predictions
    
    def predict_regression(self, history_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """方法3：基于统计回归的预测（均值回归）"""
        predictions = {}
        
        # 基于长期分布，给出最高频的特征值
        # 1. 和值回归到最常见区间
        top_sum_ranges = sorted(self.stats.sum_distribution.items(), 
                               key=lambda x: x[1], reverse=True)[:3]
        total_sum = sum([v for _, v in top_sum_ranges])
        predictions['red_sum_range'] = {
            k: v / total_sum for k, v in top_sum_ranges
        }
        
        # 2. 奇偶比回归
        top_odd_even = sorted(self.stats.odd_even_distribution.items(), 
                             key=lambda x: x[1], reverse=True)[:3]
        total_oe = sum([v for _, v in top_odd_even])
        predictions['odd_even_ratio'] = {
            k: v / total_oe for k, v in top_odd_even
        }
        
        # 3. 大小比回归
        top_big_small = sorted(self.stats.big_small_distribution.items(), 
                              key=lambda x: x[1], reverse=True)[:3]
        total_bs = sum([v for _, v in top_big_small])
        predictions['big_small_ratio'] = {
            k: v / total_bs for k, v in top_big_small
        }
        
        # 4. 连号回归
        top_consecutive = sorted(self.stats.consecutive_distribution.items(), 
                                key=lambda x: x[1], reverse=True)[:3]
        total_con = sum([v for _, v in top_consecutive])
        predictions['consecutive'] = {
            k: v / total_con for k, v in top_consecutive
        }
        
        return predictions
    
    def fuse_predictions(self, markov_pred: Dict, lstm_pred: Dict, 
                        regression_pred: Dict) -> Dict[str, Dict[str, float]]:
        """融合三种预测结果"""
        fused = {}
        
        # 获取所有特征名
        all_features = set(markov_pred.keys()) | set(lstm_pred.keys()) | set(regression_pred.keys())
        
        for feature in all_features:
            fused[feature] = {}
            
            # 获取三个模型的预测
            markov_dist = markov_pred.get(feature, {})
            lstm_dist = lstm_pred.get(feature, {})
            regression_dist = regression_pred.get(feature, {})
            
            # 获取所有可能的值
            all_values = set(markov_dist.keys()) | set(lstm_dist.keys()) | set(regression_dist.keys())
            
            for value in all_values:
                # 加权融合
                weighted_prob = (
                    markov_dist.get(value, 0) * self.markov_weight +
                    lstm_dist.get(value, 0) * self.lstm_weight +
                    regression_dist.get(value, 0) * self.regression_weight
                )
                
                if weighted_prob > 0:
                    fused[feature][value] = weighted_prob
            
            # 归一化
            total_prob = sum(fused[feature].values())
            if total_prob > 0:
                fused[feature] = {k: v / total_prob for k, v in fused[feature].items()}
        
        return fused
    
    def predict_next_period(self, last_period: pd.Series, 
                           recent_10_periods: pd.DataFrame,
                           full_history: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """完整预测流程：融合三种模型"""
        
        print("[特征预测] 开始预测下期特征...")
        
        # 1. 计算上期特征
        last_features = self.stats.calculate_single_period_features(
            last_period['red'], 
            last_period['blue']
        )
        
        print(f"[特征预测] 上期特征: 和值={last_features['red_sum']}, "
              f"奇偶={last_features['odd_even_ratio']}, "
              f"连号={last_features['consecutive']}")
        
        # 2. 马尔可夫链预测
        markov_pred = self.predict_markov(last_features)
        print(f"[特征预测] [OK] 马尔可夫链预测完成")
        
        # 3. LSTM时序预测
        lstm_pred = self.predict_lstm(recent_10_periods)
        print(f"[特征预测] [OK] LSTM时序预测完成")
        
        # 4. 统计回归预测
        regression_pred = self.predict_regression(full_history)
        print(f"[特征预测] [OK] 统计回归预测完成")
        
        # 5. 融合预测
        fused_pred = self.fuse_predictions(markov_pred, lstm_pred, regression_pred)
        print(f"[特征预测] [OK] 多模型融合完成")
        
        return fused_pred
    
    def _get_adjacent_sum_ranges(self, sum_range: str) -> List[str]:
        """获取相邻的和值区间"""
        ranges = [
            "40-50", "51-60", "61-70", "71-80", "81-90",
            "91-100", "101-110", "111-120", "121-130", "131-165"
        ]
        
        if sum_range not in ranges:
            return []
        
        idx = ranges.index(sum_range)
        adjacent = []
        if idx > 0:
            adjacent.append(ranges[idx - 1])
        if idx < len(ranges) - 1:
            adjacent.append(ranges[idx + 1])
        
        return adjacent
    
    def print_predictions(self, predictions: Dict[str, Dict[str, float]]):
        """打印预测结果"""
        print("\n" + "="*80)
        print("[下期特征预测] 多模型融合结果")
        print("="*80)
        
        for feature, probs in predictions.items():
            if not probs:
                continue
            
            print(f"\n【{feature}】")
            sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:5]
            for value, prob in sorted_probs:
                bar = "#" * int(prob * 50)
                print(f"  {str(value):20s} {prob*100:5.1f}% {bar}")
        
        print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    # 测试代码
    from model_engine import DaletouPredictor
    
    print("正在加载历史数据...")
    predictor = DaletouPredictor()
    
    print("正在构建统计模型...")
    stats = FeatureStatistics()
    stats.update_statistics(predictor.history_df)
    
    print("正在初始化预测器...")
    feature_predictor = FeaturePredictor(stats)
    
    # 获取最后一期和最近10期
    last_period = predictor.history_df.iloc[-1]
    recent_10 = predictor.history_df.tail(10)
    full_history = predictor.history_df
    
    # 执行预测
    predictions = feature_predictor.predict_next_period(
        last_period, 
        recent_10, 
        full_history
    )
    
    # 打印预测结果
    feature_predictor.print_predictions(predictions)
