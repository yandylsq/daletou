#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态评分规则配置（V12.4）
1. V12.3：单维度动态评分（和值、区间比、奇偶比、大小比）
2. V12.4：增加2维组合加成（基于历史组合转移概率）
"""

import json
import os

# 加载2维组合转移概率配置
COMBINED_2D_TRANSITIONS = {}
try:
    config_path = os.path.join(os.path.dirname(__file__), '2d_combined_transitions.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        COMBINED_2D_TRANSITIONS = json.load(f)
except:
    pass  # 如果文件不存在，使用空字典

# 和值区间转移规律（基于2831期统计）
SUM_RANGE_TRANSITIONS = {
    '40-60': {
        '81-100': 0.3547,   # 最高概率
        '61-80': 0.2350,
        '101-120': 0.2222,
    },
    '61-80': {
        '81-100': 0.3388,   # 最高概率
        '61-80': 0.2345,
        '101-120': 0.2313,
    },
    '81-100': {
        '81-100': 0.3566,   # 最高概率（自转移）
        '101-120': 0.2401,
        '61-80': 0.2036,
    },
    '101-120': {
        '81-100': 0.3443,   # 最高概率
        '101-120': 0.2726,  # 自转移
        '61-80': 0.2123,
    },
    '121-140': {
        '81-100': 0.3388,   # 最高概率
        '101-120': 0.2612,
        '61-80': 0.2163,
    },
    '141-160': {
        '81-100': 0.3529,   # 最高概率
        '101-120': 0.2353,
        '61-80': 0.1765,
    }
}

# 区间比转移规律（基于2831期统计）
ZONE_RATIO_TRANSITIONS = {
    '2:1:2': {
        '1:2:2': 0.1520,
        '2:1:2': 0.1324,
        '2:2:1': 0.1029,
    },
    '1:2:2': {
        '2:1:2': 0.1328,
        '1:2:2': 0.1276,
        '2:2:1': 0.1172,
    },
    '2:2:1': {
        '2:2:1': 0.1360,
        '1:2:2': 0.1161,
        '2:1:2': 0.1020,
    },
    '1:1:3': {
        '2:1:2': 0.1507,
        '1:1:3': 0.1360,
        '2:2:1': 0.1176,
    },
    '1:3:1': {
        '2:2:1': 0.1681,
        '1:2:2': 0.1416,
        '2:1:2': 0.1327,
    },
    '3:1:1': {
        '2:1:2': 0.1774,
        '2:2:1': 0.1720,
        '1:2:2': 0.1398,
    },
    '0:2:3': {
        '1:2:2': 0.1806,
        '2:1:2': 0.1484,
        '2:2:1': 0.1419,
    },
    '2:0:3': {
        '1:2:2': 0.2045,
        '2:1:2': 0.1591,
        '2:2:1': 0.1136,
    },
    '0:3:2': {
        '2:1:2': 0.2149,
        '3:1:1': 0.1157,
        '1:2:2': 0.1074,
    },
    '3:2:0': {
        '2:1:2': 0.1782,
        '3:1:1': 0.1386,
        '1:1:3': 0.1188,
    },
}

# 奇偶比转移规律（基于2831期统计）
ODD_EVEN_TRANSITIONS = {
    '5:0': {
        '2:3': 0.3247,
        '3:2': 0.3117,
        '4:1': 0.1429,
    },
    '4:1': {
        '3:2': 0.3965,
        '2:3': 0.2941,
        '4:1': 0.1329,
    },
    '3:2': {
        '3:2': 0.3675,
        '2:3': 0.3027,
        '4:1': 0.1634,
    },
    '2:3': {
        '3:2': 0.3588,
        '2:3': 0.3009,
        '4:1': 0.1782,
    },
    '1:4': {
        '3:2': 0.3447,
        '2:3': 0.3305,
        '4:1': 0.1624,
    },
    '0:5': {
        '3:2': 0.3333,
        '2:3': 0.3111,
        '4:1': 0.1556,
    },
}

# 大小比转移规律（基于2831期统计）
SIZE_RATIO_TRANSITIONS = {
    '5:0': {
        '3:2': 0.3889,
        '2:3': 0.2593,
        '1:4': 0.2222,
    },
    '4:1': {
        '2:3': 0.3539,
        '3:2': 0.2837,
        '1:4': 0.1545,
    },
    '3:2': {
        '2:3': 0.3447,
        '3:2': 0.2934,
        '1:4': 0.1687,
    },
    '2:3': {
        '2:3': 0.3473,
        '3:2': 0.2880,
        '1:4': 0.1828,
    },
    '1:4': {
        '2:3': 0.3527,
        '3:2': 0.2849,
        '1:4': 0.2035,
    },
    '0:5': {
        '2:3': 0.3271,
        '3:2': 0.2617,
        '1:4': 0.2523,
    },
}


def get_dynamic_zone_score(zone_ratio, last_zone_ratio):
    """
    根据上期区间比动态计算当前区间比的评分
    
    Args:
        zone_ratio: 当前期区间比
        last_zone_ratio: 上期区间比
        
    Returns:
        (base_score, reason): 基础分数和理由
    """
    # 默认基础分（无上期信息时）
    default_scores = {
        '2:1:2': 300,
        '1:2:2': 285,
        '2:2:1': 270,
        '1:1:3': 200,
        '1:3:1': 200,
        '3:1:1': 200,
    }
    
    base_score = default_scores.get(zone_ratio, 150)
    reason = f"区间比({zone_ratio})"
    
    # 如果有上期信息，根据转移概率动态调整
    if last_zone_ratio and last_zone_ratio in ZONE_RATIO_TRANSITIONS:
        transitions = ZONE_RATIO_TRANSITIONS[last_zone_ratio]
        if zone_ratio in transitions:
            prob = transitions[zone_ratio]
            # 根据转移概率调整分数：概率越高，分数越高
            bonus = int(prob * 2000)  # 最高概率21.49%可获得429分加成
            base_score += bonus
            reason = f"区间比动态({last_zone_ratio}→{zone_ratio},概率{prob:.1%})"
    
    return base_score, reason


def get_dynamic_odd_score(odd_ratio, last_odd_ratio, prev2_odd_ratio=None):
    """
    根据上期奇偶比动态计算当前奇偶比的评分
    综合考虑：
    1. 极端奇偶比回归规律（5:0、0:5后倾向于3:2、2:3）
    2. 自转移惯性（3:2和2:3有超强的自转移概率36.8%、30.1%）
    3. 连续相同奇偶比后的保持概率
    4. 基本转移概率
    """
    # 默认基础分
    default_scores = {
        '3:2': 220,
        '2:3': 220,
        '4:1': 260,
        '1:4': 260,
        '5:0': 120,
        '0:5': 120,
    }
    
    base_score = default_scores.get(odd_ratio, 100)
    reason = f"奇偶比({odd_ratio})"
    
    # 动态调整
    if last_odd_ratio:
        # === 1. 极端奇偶比回归规律（最优先） ===
        if last_odd_ratio in ['5:0', '0:5'] and odd_ratio in ['3:2', '2:3']:
            base_score += 550  # 极端值回归均衡，大幅加分
            reason = f"奇偶比回归均衡({last_odd_ratio}→{odd_ratio})"
        
        # === 2. 自转移惯性（高频比值的特别处理） ===
        elif prev2_odd_ratio:  # 有上上期数据
            # 连续2期相同且当前期仍然保持 → 超强惯性
            if prev2_odd_ratio == last_odd_ratio == odd_ratio:
                if odd_ratio == '3:2':
                    base_score += 500  # 3:2连续3期，超强惯性（36.8%自转移）
                    reason = f"奇偶比超强惯性({odd_ratio}连续3期)"
                elif odd_ratio == '2:3':
                    base_score += 480  # 2:3连续3期（30.1%自转移）
                    reason = f"奇偶比强惯性({odd_ratio}连续3期)"
            # 连续2期相同但当前期变化 → 反转信号
            elif prev2_odd_ratio == last_odd_ratio and odd_ratio != last_odd_ratio:
                # 从高频比值反转到另一个高频比值
                if last_odd_ratio == '3:2' and odd_ratio == '2:3':
                    base_score += 420  # 3:2→2:3，常见转换（30.3%）
                    reason = f"奇偶比稳定转换({last_odd_ratio}连续2期→2:3)"
                elif last_odd_ratio == '2:3' and odd_ratio == '3:2':
                    base_score += 450  # 2:3→3:2，最常见转换（35.9%）
                    reason = f"奇偶比稳定转换({last_odd_ratio}连续2期→3:2)"
        
        # === 3. 如果以上都不命中，使用基本转移概率 ===
        if '回归' not in reason and '惯性' not in reason and '转换' not in reason:
            if last_odd_ratio in ODD_EVEN_TRANSITIONS:
                transitions = ODD_EVEN_TRANSITIONS[last_odd_ratio]
                if odd_ratio in transitions:
                    prob = transitions[odd_ratio]
                    bonus = int(prob * 1500)  # 最高概率39.65%可获得594分加成
                    base_score += bonus
                    reason = f"奇偶比转移({last_odd_ratio}→{odd_ratio},概率{prob:.1%})"
    
    return base_score, reason


def get_dynamic_size_score(size_ratio, last_size_ratio, prev2_size_ratio=None):
    """
    根据上期大小比动态计算当前大小比的评分
    综合考虑：
    1. 极端大小比回归规律（5:0、0:5后倾向于2:3、3:2）
    2. 自转移惯性（2:3和3:2有超强的自转移概率34.7%、29.3%）
    3. 连续相同大小比后的保持概率
    4. 基本转移概率
    """
    # 默认基础分
    default_scores = {
        '2:3': 200,
        '3:2': 200,
        '1:4': 180,
        '4:1': 180,
        '0:5': 120,
        '5:0': 120,
    }
    
    base_score = default_scores.get(size_ratio, 100)
    reason = f"大小比({size_ratio})"
    
    # 动态调整
    if last_size_ratio:
        # === 1. 极端大小比回归规律（最优先） ===
        if last_size_ratio in ['5:0', '0:5'] and size_ratio in ['2:3', '3:2']:
            base_score += 530  # 极端值回归均衡，大幅加分
            reason = f"大小比回归均衡({last_size_ratio}→{size_ratio})"
        
        # === 2. 自转移惯性（高频比值的特别处理） ===
        elif prev2_size_ratio:  # 有上上期数据
            # 连续2期相同且当前期仍然保持 → 超强惯性
            if prev2_size_ratio == last_size_ratio == size_ratio:
                if size_ratio == '2:3':
                    base_score += 480  # 2:3连续3期，超强惯性（34.7%自转移）
                    reason = f"大小比超强惯性({size_ratio}连续3期)"
                elif size_ratio == '3:2':
                    base_score += 460  # 3:2连续3期（29.3%自转移）
                    reason = f"大小比强惯性({size_ratio}连续3期)"
            # 连续2期相同但当前期变化 → 反转信号
            elif prev2_size_ratio == last_size_ratio and size_ratio != last_size_ratio:
                # 从高频比值反转到另一个高频比值
                if last_size_ratio == '2:3' and size_ratio == '3:2':
                    base_score += 410  # 2:3→3:2（28.8%）
                    reason = f"大小比稳定转换({last_size_ratio}连续2期→3:2)"
                elif last_size_ratio == '3:2' and size_ratio == '2:3':
                    base_score += 440  # 3:2→2:3（34.5%）
                    reason = f"大小比稳定转换({last_size_ratio}连续2期→2:3)"
        
        # === 3. 如果以上都不命中，使用基本转移概率 ===
        if '回归' not in reason and '惯性' not in reason and '转换' not in reason:
            if last_size_ratio in SIZE_RATIO_TRANSITIONS:
                transitions = SIZE_RATIO_TRANSITIONS[last_size_ratio]
                if size_ratio in transitions:
                    prob = transitions[size_ratio]
                    bonus = int(prob * 1500)  # 最高概率38.89%可获得583分加成
                    base_score += bonus
                    reason = f"大小比转移({last_size_ratio}→{size_ratio},概率{prob:.1%})"
    
    return base_score, reason


def get_dynamic_sum_score(red_sum, last_red_sum, prev2_red_sum=None):
    """
    根据上期和值动态计算当前和值的评分
    综合考虑：
    1. 上期和值的转移概率
    2. 和值回归中心趋势（极端值后倾向于回归90-110）
    3. 连续趋势反转规律（连续上升/下降后高概率反转）
    
    Args:
        red_sum: 当前期红球和值
        last_red_sum: 上期红球和值
        prev2_red_sum: 上上期红球和值（用于趋势判断）
        
    Returns:
        (base_score, reason): 基础分数和理由
    """
    # 确定当前和值区间
    if 40 <= red_sum <= 60:
        curr_range = '40-60'
    elif 61 <= red_sum <= 80:
        curr_range = '61-80'
    elif 81 <= red_sum <= 100:
        curr_range = '81-100'
    elif 101 <= red_sum <= 120:
        curr_range = '101-120'
    elif 121 <= red_sum <= 140:
        curr_range = '121-140'
    elif 141 <= red_sum <= 160:
        curr_range = '141-160'
    else:
        curr_range = 'other'
    
    # 默认基础分（无上期信息时）
    default_scores = {
        '81-100': 380,
        '101-120': 350,
        '61-80': 250,
        '121-140': 180,
        '40-60': 150,
        '141-160': 80,
    }
    
    base_score = default_scores.get(curr_range, 50)
    reason = f"和值区间({curr_range})"  
    
    # 如果有上期信息，应用动态调整
    if last_red_sum:
        # === 1. 和值回归中心趋势（最重要） ===
        # 上期在极端低值区，当前期向中心回归 → 大幅加分
        if last_red_sum < 60 and 80 <= red_sum <= 110:
            base_score += 600  # 极端低值回归，大幅加分
            reason = f"和值回归中心({last_red_sum:.0f}→{red_sum},极低回归)"
        elif 60 <= last_red_sum < 80 and 85 <= red_sum <= 110:
            base_score += 450  # 低值回归
            reason = f"和值回归中心({last_red_sum:.0f}→{red_sum},低值回归)"
        # 上期在极端高值区，当前期向中心回归 → 大幅加分
        elif last_red_sum > 120 and 80 <= red_sum <= 110:
            base_score += 600  # 极端高值回归
            reason = f"和值回归中心({last_red_sum:.0f}→{red_sum},极高回归)"
        elif 110 < last_red_sum <= 120 and 85 <= red_sum <= 105:
            base_score += 450  # 高值回归
            reason = f"和值回归中心({last_red_sum:.0f}→{red_sum},高值回归)"
        
        # === 2. 连续趋势反转规律 ===
        elif prev2_red_sum:  # 有上上期数据
            # 连续上升后反转（下降）
            if prev2_red_sum < last_red_sum and red_sum < last_red_sum:
                change = last_red_sum - red_sum
                if change >= 15:  # 大幅下降
                    base_score += 550
                    reason = f"趋势大幅反转({prev2_red_sum:.0f}→{last_red_sum:.0f}→{red_sum},反转{change:.0f})"
                elif change >= 5:  # 中幅下降
                    base_score += 400
                    reason = f"趋势反转({prev2_red_sum:.0f}→{last_red_sum:.0f}→{red_sum},反转{change:.0f})"
            # 连续下降后反转（上升）
            elif prev2_red_sum > last_red_sum and red_sum > last_red_sum:
                change = red_sum - last_red_sum
                if change >= 15:  # 大幅上升
                    base_score += 550
                    reason = f"趋势大幅反转({prev2_red_sum:.0f}→{last_red_sum:.0f}→{red_sum},反转+{change:.0f})"
                elif change >= 5:  # 中幅上升
                    base_score += 400
                    reason = f"趋势反转({prev2_red_sum:.0f}→{last_red_sum:.0f}→{red_sum},反转+{change:.0f})"
        
        # === 3. 如果以上都不命中，使用基本转移概率 ===
        if '回归' not in reason and '反转' not in reason:
            # 确定上期和值区间
            if 40 <= last_red_sum <= 60:
                last_range = '40-60'
            elif 61 <= last_red_sum <= 80:
                last_range = '61-80'
            elif 81 <= last_red_sum <= 100:
                last_range = '81-100'
            elif 101 <= last_red_sum <= 120:
                last_range = '101-120'
            elif 121 <= last_red_sum <= 140:
                last_range = '121-140'
            elif 141 <= last_red_sum <= 160:
                last_range = '141-160'
            else:
                last_range = 'other'
            
            if last_range in SUM_RANGE_TRANSITIONS:
                transitions = SUM_RANGE_TRANSITIONS[last_range]
                if curr_range in transitions:
                    prob = transitions[curr_range]
                    # 根据转移概率调整分数
                    bonus = int(prob * 1000)  # 最高概率35.66%可获得356分加成
                    base_score += bonus
                    reason = f"和值转移({last_range}→{curr_range},概率{prob:.1%})"
    
    return base_score, reason


def get_2d_combined_bonus(curr_features, last_features):
    """
    计算2维组合特征加成
    如果当前组合符合历史统计的高概率转移模式，给予额外加分
    
    Args:
        curr_features: 当前期特征字典 {'sum_range': '90-110', 'zone_ratio': '2:1:2', 'odd_ratio': '3:2', 'size_ratio': '2:3'}
        last_features: 上期特征字典
    
    Returns:
        (bonus_score, reason_list): 加分和理由列表
    """
    if not last_features or not COMBINED_2D_TRANSITIONS:
        return 0, []
    
    bonus_score = 0
    reasons = []
    
    # 1. 和值区间 + 区间比
    combo_name = "和值区间+区间比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['sum_range']}+{last_features['zone_ratio']}"
        curr_key = f"{curr_features['sum_range']}+{curr_features['zone_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:  # 只对高概率(>=15%)给加分
                    score = int(prob * 1500)  # 最高20%概率可获得300分
                    bonus_score += score
                    reasons.append(f"组合（和值+区间,{prob:.1%}）")
    
    # 2. 和值区间 + 奇偶比
    combo_name = "和值区间+奇偶比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['sum_range']}+{last_features['odd_ratio']}"
        curr_key = f"{curr_features['sum_range']}+{curr_features['odd_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:
                    score = int(prob * 1500)
                    bonus_score += score
                    reasons.append(f"组合（和值+奇偶,{prob:.1%}）")
    
    # 3. 和值区间 + 大小比
    combo_name = "和值区间+大小比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['sum_range']}+{last_features['size_ratio']}"
        curr_key = f"{curr_features['sum_range']}+{curr_features['size_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:
                    score = int(prob * 1500)
                    bonus_score += score
                    reasons.append(f"组合（和值+大小,{prob:.1%}）")
    
    # 4. 区间比 + 奇偶比
    combo_name = "区间比+奇偶比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['zone_ratio']}+{last_features['odd_ratio']}"
        curr_key = f"{curr_features['zone_ratio']}+{curr_features['odd_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:
                    score = int(prob * 1500)
                    bonus_score += score
                    reasons.append(f"组合（区间+奇偶,{prob:.1%}）")
    
    # 5. 区间比 + 大小比
    combo_name = "区间比+大小比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['zone_ratio']}+{last_features['size_ratio']}"
        curr_key = f"{curr_features['zone_ratio']}+{curr_features['size_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:
                    score = int(prob * 1500)
                    bonus_score += score
                    reasons.append(f"组合（区间+大小,{prob:.1%}）")
    
    # 6. 奇偶比 + 大小比
    combo_name = "奇偶比+大小比"
    if combo_name in COMBINED_2D_TRANSITIONS:
        last_key = f"{last_features['odd_ratio']}+{last_features['size_ratio']}"
        curr_key = f"{curr_features['odd_ratio']}+{curr_features['size_ratio']}"
        
        if last_key in COMBINED_2D_TRANSITIONS[combo_name]:
            transitions = COMBINED_2D_TRANSITIONS[combo_name][last_key]
            if curr_key in transitions:
                prob = transitions[curr_key]
                if prob >= 0.15:
                    score = int(prob * 1500)
                    bonus_score += score
                    reasons.append(f"组合（奇偶+大小,{prob:.1%}）")
    
    return bonus_score, reasons
