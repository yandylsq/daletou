"""
大乐透历史特征统计与规律挖掘模块

功能：
1. 单期内部特征统计（和值、奇偶、大小、连号、区间、尾号、AC值、质数等）
2. 期间转移规律统计（条件概率矩阵）
3. 多维联合分布统计

Author: Daletou Team
Version: V10.0
Date: 2026-01-22
"""

import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import json
import os


class FeatureStatistics:
    """历史特征统计分析器"""
    
    def __init__(self):
        # 单期特征分布
        self.sum_distribution = defaultdict(int)  # 和值分布
        self.odd_even_distribution = defaultdict(int)  # 奇偶比分布
        self.big_small_distribution = defaultdict(int)  # 大小比分布
        self.consecutive_distribution = defaultdict(int)  # 连号分布
        self.zone_distribution = defaultdict(int)  # 区间分布
        self.tail_distribution = defaultdict(int)  # 尾号分布
        self.ac_distribution = defaultdict(int)  # AC值分布
        self.prime_distribution = defaultdict(int)  # 质数个数分布
        self.span_distribution = defaultdict(int)  # 跨度分布
        self.blue_sum_distribution = defaultdict(int)  # 蓝球和值分布
        self.blue_span_distribution = defaultdict(int)  # 蓝球跨度分布
        
        # 期间转移规律（条件概率矩阵）
        self.sum_transition = defaultdict(lambda: defaultdict(int))  # P(下期和值区间|上期和值区间)
        self.odd_even_transition = defaultdict(lambda: defaultdict(int))  # P(下期奇偶比|上期奇偶比)
        self.big_small_transition = defaultdict(lambda: defaultdict(int))  # P(下期大小比|上期大小比)
        self.consecutive_transition = defaultdict(lambda: defaultdict(int))  # P(下期连号|上期连号)
        self.zone_transition = defaultdict(lambda: defaultdict(int))  # P(下期区间|上期区间)
        self.ac_transition = defaultdict(lambda: defaultdict(int))  # P(下期AC值|上期AC值)
        self.prime_transition = defaultdict(lambda: defaultdict(int))  # P(下期质数个数|上期质数个数)
        self.blue_sum_transition = defaultdict(lambda: defaultdict(int))  # P(下期蓝球和值|上期蓝球和值)
        
        # 多维联合分布
        self.odd_even_given_sum = defaultdict(lambda: defaultdict(int))  # P(奇偶比|和值区间)
        self.big_small_given_sum = defaultdict(lambda: defaultdict(int))  # P(大小比|和值区间)
        self.consecutive_given_sum = defaultdict(lambda: defaultdict(int))  # P(连号|和值区间)
        self.blue_sum_given_red_sum = defaultdict(lambda: defaultdict(int))  # P(蓝球和值|前区和值区间)
        self.ac_given_sum_span = defaultdict(lambda: defaultdict(int))  # P(AC值|和值区间,跨度)
        
        # 质数集合
        self.primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
        
        # 统计总期数
        self.total_periods = 0
    
    def get_sum_range(self, red_sum: int) -> str:
        """获取和值所属区间"""
        ranges = [
            (40, 50), (51, 60), (61, 70), (71, 80), (81, 90),
            (91, 100), (101, 110), (111, 120), (121, 130), (131, 165)
        ]
        for low, high in ranges:
            if low <= red_sum <= high:
                return f"{low}-{high}"
        return "other"
    
    def get_span_range(self, span: int) -> str:
        """获取跨度所属区间"""
        if span < 20:
            return "15-19"
        elif span < 25:
            return "20-24"
        elif span < 30:
            return "25-29"
        else:
            return "30-34"
    
    def calculate_single_period_features(self, red: List[int], blue: List[int]) -> Dict[str, Any]:
        """计算单期的所有特征"""
        red = sorted(red)
        blue = sorted(blue)
        
        features = {}
        
        # 1. 和值
        red_sum = sum(red)
        features['red_sum'] = red_sum
        features['red_sum_range'] = self.get_sum_range(red_sum)
        
        # 2. 奇偶比
        odd_count = sum(1 for x in red if x % 2 == 1)
        features['odd_count'] = odd_count
        features['odd_even_ratio'] = f"{odd_count}奇{5-odd_count}偶"
        
        # 3. 大小比（界限18）
        big_count = sum(1 for x in red if x >= 18)
        features['big_count'] = big_count
        features['big_small_ratio'] = f"{big_count}大{5-big_count}小"
        
        # 4. 连号情况
        consecutive_pairs = sum(1 for i in range(len(red)-1) if red[i+1] - red[i] == 1)
        if consecutive_pairs == 0:
            features['consecutive'] = "0连"
        elif consecutive_pairs == 1:
            features['consecutive'] = "2连"
        elif consecutive_pairs == 2:
            features['consecutive'] = "3连"
        else:
            features['consecutive'] = "4连+"
        
        # 5. 区间分布（1-11, 12-23, 24-35）
        zone1 = sum(1 for x in red if 1 <= x <= 11)
        zone2 = sum(1 for x in red if 12 <= x <= 23)
        zone3 = sum(1 for x in red if 24 <= x <= 35)
        features['zone_distribution'] = f"{zone1}-{zone2}-{zone3}"
        
        # 6. 尾号分布
        tails = [x % 10 for x in red]
        features['tail_diversity'] = len(set(tails))
        features['tail_distribution'] = ','.join(map(str, sorted(set(tails))))
        
        # 7. AC值（号码离散度）
        diffs = set()
        for i in range(len(red)):
            for j in range(i + 1, len(red)):
                diffs.add(abs(red[i] - red[j]))
        features['ac_value'] = len(diffs) - 4
        
        # 8. 质数个数
        prime_count = sum(1 for x in red if x in self.primes)
        features['prime_count'] = prime_count
        
        # 9. 跨度
        red_span = red[-1] - red[0]
        features['red_span'] = red_span
        features['red_span_range'] = self.get_span_range(red_span)
        
        # 10. 蓝球和值
        blue_sum = sum(blue)
        features['blue_sum'] = blue_sum
        
        # 11. 蓝球跨度
        blue_span = blue[1] - blue[0] if len(blue) == 2 else 0
        features['blue_span'] = blue_span
        
        # 12. 蓝球奇偶
        blue_odd_count = sum(1 for x in blue if x % 2 == 1)
        features['blue_odd_even'] = f"{blue_odd_count}奇{2-blue_odd_count}偶"
        
        return features
    
    def update_statistics(self, history_df: pd.DataFrame):
        """更新所有统计信息"""
        print(f"[统计分析] 开始分析 {len(history_df)} 期历史数据...")
        
        self.total_periods = len(history_df)
        prev_features = None
        
        for idx, row in history_df.iterrows():
            # 计算当前期特征
            features = self.calculate_single_period_features(row['red'], row['blue'])
            
            # 更新单期特征分布
            self.sum_distribution[features['red_sum_range']] += 1
            self.odd_even_distribution[features['odd_even_ratio']] += 1
            self.big_small_distribution[features['big_small_ratio']] += 1
            self.consecutive_distribution[features['consecutive']] += 1
            self.zone_distribution[features['zone_distribution']] += 1
            self.ac_distribution[features['ac_value']] += 1
            self.prime_distribution[features['prime_count']] += 1
            self.span_distribution[features['red_span_range']] += 1
            self.blue_sum_distribution[features['blue_sum']] += 1
            self.blue_span_distribution[features['blue_span']] += 1
            
            # 更新多维联合分布
            sum_range = features['red_sum_range']
            self.odd_even_given_sum[sum_range][features['odd_even_ratio']] += 1
            self.big_small_given_sum[sum_range][features['big_small_ratio']] += 1
            self.consecutive_given_sum[sum_range][features['consecutive']] += 1
            self.blue_sum_given_red_sum[sum_range][features['blue_sum']] += 1
            
            key = f"{sum_range}_{features['red_span_range']}"
            self.ac_given_sum_span[key][features['ac_value']] += 1
            
            # 更新期间转移规律
            if prev_features is not None:
                self.sum_transition[prev_features['red_sum_range']][features['red_sum_range']] += 1
                self.odd_even_transition[prev_features['odd_even_ratio']][features['odd_even_ratio']] += 1
                self.big_small_transition[prev_features['big_small_ratio']][features['big_small_ratio']] += 1
                self.consecutive_transition[prev_features['consecutive']][features['consecutive']] += 1
                self.zone_transition[prev_features['zone_distribution']][features['zone_distribution']] += 1
                self.ac_transition[prev_features['ac_value']][features['ac_value']] += 1
                self.prime_transition[prev_features['prime_count']][features['prime_count']] += 1
                self.blue_sum_transition[prev_features['blue_sum']][features['blue_sum']] += 1
            
            prev_features = features
        
        print(f"[统计分析] [OK] 统计完成")
        self._print_summary()
    
    def _print_summary(self):
        """打印统计摘要"""
        print("\n" + "="*80)
        print("📊 历史特征统计摘要")
        print("="*80)
        
        print("\n【单期特征分布 Top 5】")
        print(f"  和值区间: {self._get_top_n(self.sum_distribution, 5)}")
        print(f"  奇偶比: {self._get_top_n(self.odd_even_distribution, 5)}")
        print(f"  大小比: {self._get_top_n(self.big_small_distribution, 5)}")
        print(f"  连号情况: {dict(self.consecutive_distribution)}")
        print(f"  AC值: {self._get_top_n(self.ac_distribution, 5)}")
        
        print("\n【期间转移规律样例】")
        # 和值转移
        if self.sum_transition:
            sample_sum = list(self.sum_transition.keys())[0]
            print(f"  当上期和值在 {sample_sum} 时，下期和值分布:")
            for next_sum, count in sorted(self.sum_transition[sample_sum].items(), 
                                         key=lambda x: x[1], reverse=True)[:3]:
                prob = count / sum(self.sum_transition[sample_sum].values())
                print(f"    {next_sum}: {prob*100:.1f}%")
        
        print("\n" + "="*80 + "\n")
    
    def _get_top_n(self, distribution: Dict, n: int) -> str:
        """获取分布的前N项"""
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:n]
        return ", ".join([f"{k}({v}期)" for k, v in sorted_items])
    
    def get_transition_probabilities(self, prev_feature_key: str, 
                                     transition_matrix: Dict) -> Dict[str, float]:
        """获取转移概率分布"""
        if prev_feature_key not in transition_matrix:
            return {}
        
        counts = transition_matrix[prev_feature_key]
        total = sum(counts.values())
        
        if total == 0:
            return {}
        
        return {k: v / total for k, v in counts.items()}
    
    def predict_next_features(self, last_period_features: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """基于上期特征预测下期特征的概率分布"""
        predictions = {}
        
        # 1. 预测下期和值区间
        predictions['red_sum_range'] = self.get_transition_probabilities(
            last_period_features['red_sum_range'], 
            self.sum_transition
        )
        
        # 2. 预测下期奇偶比
        predictions['odd_even_ratio'] = self.get_transition_probabilities(
            last_period_features['odd_even_ratio'],
            self.odd_even_transition
        )
        
        # 3. 预测下期大小比
        predictions['big_small_ratio'] = self.get_transition_probabilities(
            last_period_features['big_small_ratio'],
            self.big_small_transition
        )
        
        # 4. 预测下期连号情况
        predictions['consecutive'] = self.get_transition_probabilities(
            last_period_features['consecutive'],
            self.consecutive_transition
        )
        
        # 5. 预测下期AC值
        predictions['ac_value'] = self.get_transition_probabilities(
            last_period_features['ac_value'],
            self.ac_transition
        )
        
        # 6. 预测下期质数个数
        predictions['prime_count'] = self.get_transition_probabilities(
            last_period_features['prime_count'],
            self.prime_transition
        )
        
        # 7. 预测下期蓝球和值
        predictions['blue_sum'] = self.get_transition_probabilities(
            last_period_features['blue_sum'],
            self.blue_sum_transition
        )
        
        return predictions
    
    def save_statistics(self, filepath: str = 'model_assets/feature_statistics.json'):
        """保存统计结果到文件"""
        data = {
            'total_periods': self.total_periods,
            'sum_distribution': dict(self.sum_distribution),
            'odd_even_distribution': dict(self.odd_even_distribution),
            'big_small_distribution': dict(self.big_small_distribution),
            'consecutive_distribution': dict(self.consecutive_distribution),
            'ac_distribution': dict(self.ac_distribution),
            'sum_transition': {k: dict(v) for k, v in self.sum_transition.items()},
            'odd_even_transition': {k: dict(v) for k, v in self.odd_even_transition.items()},
            # ... 其他统计数据
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[统计分析] 统计结果已保存到: {filepath}")
    
    def load_statistics(self, filepath: str = 'model_assets/feature_statistics.json'):
        """从文件加载统计结果"""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.total_periods = data.get('total_periods', 0)
        self.sum_distribution = defaultdict(int, data.get('sum_distribution', {}))
        self.odd_even_distribution = defaultdict(int, data.get('odd_even_distribution', {}))
        # ... 加载其他统计数据
        
        print(f"[统计分析] 成功加载统计结果: {filepath}")
        return True


if __name__ == '__main__':
    # 测试代码
    from model_engine import DaletouPredictor
    
    predictor = DaletouPredictor()
    stats = FeatureStatistics()
    stats.update_statistics(predictor.history_df)
    
    # 测试预测功能
    last_period = predictor.history_df.iloc[-1]
    last_features = stats.calculate_single_period_features(
        last_period['red'], 
        last_period['blue']
    )
    
    print("\n最后一期特征:")
    for k, v in last_features.items():
        print(f"  {k}: {v}")
    
    predictions = stats.predict_next_features(last_features)
    print("\n下期特征预测:")
    for feature, probs in predictions.items():
        if probs:
            top3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  {feature}:")
            for val, prob in top3:
                print(f"    {val}: {prob*100:.1f}%")
