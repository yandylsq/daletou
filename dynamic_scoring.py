"""
基于特征预测的动态评分系统 - V10核心模块

核心思想：
1. 先预测"下期应该是什么样"（特征预测）
2. 再评估"哪些组合最接近预测"（匹配度评分）
3. 评分权重由历史概率决定，而非固定阈值

Author: Daletou Team
Version: V10.0
Date: 2026-01-22
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from feature_statistics import FeatureStatistics


class DynamicScorer:
    """基于特征预测的动态评分器"""
    
    def __init__(self, feature_stats: FeatureStatistics, 
                 predicted_features: Dict[str, Dict[str, float]]):
        """
        Args:
            feature_stats: 特征统计对象
            predicted_features: 下期特征的概率分布预测
        """
        self.stats = feature_stats
        self.predictions = predicted_features
        
        # 各特征的评分权重（可调整）
        self.feature_weights = {
            'red_sum_range': 250,      # 和值匹配
            'odd_even_ratio': 200,     # 奇偶比匹配
            'big_small_ratio': 180,    # 大小比匹配
            'consecutive': 150,        # 连号匹配
            'ac_value': 120,           # AC值匹配
            'prime_count': 100,        # 质数个数匹配
            'blue_sum': 150,           # 蓝球和值匹配
        }
    
    def score_combination_v10(self, red: List[int], blue: List[int], 
                             return_details: bool = False) -> Tuple[float, str]:
        """
        V10动态评分：基于预测特征的匹配度
        
        Args:
            red: 前区5个号码
            blue: 后区2个号码
            return_details: 是否返回详细理由
            
        Returns:
            (score, details_string)
        """
        red = sorted(red)
        blue = sorted(blue)
        
        # 计算该组合的特征
        combo_features = self.stats.calculate_single_period_features(red, blue)
        
        total_score = 0
        details = []
        
        # 1. 和值匹配度得分
        sum_range = combo_features['red_sum_range']
        sum_pred = self.predictions.get('red_sum_range', {})
        if sum_range in sum_pred:
            match_prob = sum_pred[sum_range]
            score_add = self.feature_weights['red_sum_range'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"和值{sum_range}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            # 不在预测范围内，给予小分
            total_score += 30
            if return_details:
                details.append(f"和值{sum_range}(非主流)")
        
        # 2. 奇偶比匹配度得分
        odd_even = combo_features['odd_even_ratio']
        odd_even_pred = self.predictions.get('odd_even_ratio', {})
        if odd_even in odd_even_pred:
            match_prob = odd_even_pred[odd_even]
            score_add = self.feature_weights['odd_even_ratio'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"奇偶比{odd_even}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            total_score += 20
        
        # 3. 大小比匹配度得分
        big_small = combo_features['big_small_ratio']
        big_small_pred = self.predictions.get('big_small_ratio', {})
        if big_small in big_small_pred:
            match_prob = big_small_pred[big_small]
            score_add = self.feature_weights['big_small_ratio'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"大小比{big_small}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            total_score += 20
        
        # 4. 连号匹配度得分
        consecutive = combo_features['consecutive']
        consecutive_pred = self.predictions.get('consecutive', {})
        if consecutive in consecutive_pred:
            match_prob = consecutive_pred[consecutive]
            score_add = self.feature_weights['consecutive'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"连号{consecutive}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            total_score += 15
        
        # 5. AC值匹配度得分
        ac_value = combo_features['ac_value']
        ac_pred = self.predictions.get('ac_value', {})
        if ac_value in ac_pred:
            match_prob = ac_pred[ac_value]
            score_add = self.feature_weights['ac_value'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"AC值{ac_value}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            total_score += 10
        
        # 6. 质数个数匹配度得分
        prime_count = combo_features['prime_count']
        prime_pred = self.predictions.get('prime_count', {})
        if prime_count in prime_pred:
            match_prob = prime_pred[prime_count]
            score_add = self.feature_weights['prime_count'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"质数{prime_count}个(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        
        # 7. 蓝球和值匹配度得分
        blue_sum = combo_features['blue_sum']
        blue_sum_pred = self.predictions.get('blue_sum', {})
        if blue_sum in blue_sum_pred:
            match_prob = blue_sum_pred[blue_sum]
            score_add = self.feature_weights['blue_sum'] * match_prob
            total_score += score_add
            if return_details:
                details.append(f"蓝球和值{blue_sum}(预测概率{match_prob*100:.1f}%,+{score_add:.0f})")
        else:
            total_score += 15
        
        # 8. 区间分布相似度（额外加成）
        zone_dist = combo_features['zone_distribution']
        # 理想分布为1-2-2或2-2-1（根据历史统计）
        if zone_dist in ['1-2-2', '2-2-1', '2-1-2', '1-3-1']:
            total_score += 80
            if return_details:
                details.append(f"区间分布合理{zone_dist}(+80)")
        
        # 9. 尾号多样性加分
        tail_diversity = combo_features['tail_diversity']
        if tail_diversity >= 4:
            total_score += 60
            if return_details:
                details.append(f"尾号多样性{tail_diversity}(+60)")
        
        if return_details:
            return total_score, " | ".join(details)
        return total_score, ""


def test_dynamic_scoring():
    """测试动态评分系统"""
    from model_engine import DaletouPredictor
    from feature_predictor import FeaturePredictor
    
    print("="*80)
    print("V10 动态评分系统测试")
    print("="*80)
    
    # 加载数据
    print("\n[1/4] 加载历史数据...")
    predictor = DaletouPredictor()
    
    # 构建统计
    print("[2/4] 构建统计模型...")
    stats = FeatureStatistics()
    stats.update_statistics(predictor.history_df)
    
    # 预测下期特征
    print("[3/4] 预测下期特征...")
    feature_predictor = FeaturePredictor(stats)
    last_period = predictor.history_df.iloc[-1]
    recent_10 = predictor.history_df.tail(10)
    
    predictions = feature_predictor.predict_next_period(
        last_period, recent_10, predictor.history_df
    )
    
    feature_predictor.print_predictions(predictions)
    
    # 初始化动态评分器
    print("[4/4] 测试动态评分...")
    scorer = DynamicScorer(stats, predictions)
    
    # 测试几个典型组合
    test_cases = [
        {
            'name': '高匹配度组合（符合预测）',
            'red': [5, 12, 18, 25, 33],  # 和值93，3奇2偶，2大3小
            'blue': [5, 8]  # 和值13
        },
        {
            'name': '低匹配度组合（不符合预测）',
            'red': [1, 2, 3, 4, 5],  # 和值15，5奇0偶，全小
            'blue': [1, 2]  # 和值3
        },
        {
            'name': '26009期实际开奖',
            'red': [5, 12, 13, 14, 33],  # 和值77，3奇2偶，三连号
            'blue': [5, 8]  # 和值13
        }
    ]
    
    print("\n" + "="*80)
    print("评分对比")
    print("="*80)
    
    for case in test_cases:
        score, details = scorer.score_combination_v10(
            case['red'], case['blue'], return_details=True
        )
        print(f"\n{case['name']}")
        print(f"  号码: {case['red']} - {case['blue']}")
        print(f"  得分: {score:.1f}")
        print(f"  详情: {details}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    test_dynamic_scoring()
