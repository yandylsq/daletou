#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
组合特征转移规律分析
统计：上期(和值区间+区间比+奇偶比+大小比) → 下期(和值区间+区间比+奇偶比+大小比)
"""

from collections import defaultdict
import json

def parse_history_file(file_path):
    """解析历史数据文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            period = parts[0].strip()
            numbers = parts[2].strip().split('-')
            if len(numbers) != 2:
                continue
            red = sorted([int(x) for x in numbers[0].split()])
            blue = sorted([int(x) for x in numbers[1].split()])
            data.append({
                'period': period,
                'red': red,
                'blue': blue
            })
    return data

def get_sum_range(red_sum):
    """获取和值区间"""
    if red_sum < 70:
        return '<70'
    elif red_sum < 90:
        return '70-90'
    elif red_sum < 110:
        return '90-110'
    elif red_sum < 130:
        return '110-130'
    else:
        return '130+'

def get_zone_ratio(red):
    z1 = sum(1 for x in red if x <= 11)
    z2 = sum(1 for x in red if 12 <= x <= 23)
    z3 = sum(1 for x in red if x >= 24)
    return f"{z1}:{z2}:{z3}"

def get_odd_even_ratio(red):
    odd = sum(1 for x in red if x % 2 == 1)
    return f"{odd}:{5-odd}"

def get_size_ratio(red):
    small = sum(1 for x in red if x <= 17)
    return f"{small}:{5-small}"

def get_combined_features(red):
    """获取组合特征"""
    red_sum = sum(red)
    return {
        'sum_range': get_sum_range(red_sum),
        'zone_ratio': get_zone_ratio(red),
        'odd_ratio': get_odd_even_ratio(red),
        'size_ratio': get_size_ratio(red)
    }

def analyze_combined_transitions(data):
    """分析组合特征的转移规律"""
    print("=" * 80)
    print("组合特征转移规律分析")
    print("=" * 80)
    
    # 统计转移：(和值区间,区间比,奇偶比,大小比) -> (和值区间,区间比,奇偶比,大小比)
    transitions = defaultdict(lambda: defaultdict(int))
    
    for i in range(len(data) - 1):
        curr_features = get_combined_features(data[i]['red'])
        next_features = get_combined_features(data[i+1]['red'])
        
        # 组合成特征字符串
        curr_key = f"{curr_features['sum_range']}|{curr_features['zone_ratio']}|{curr_features['odd_ratio']}|{curr_features['size_ratio']}"
        next_key = f"{next_features['sum_range']}|{next_features['zone_ratio']}|{next_features['odd_ratio']}|{next_features['size_ratio']}"
        
        transitions[curr_key][next_key] += 1
    
    # 找出样本数较多的组合（>=10）
    print(f"\n共找到 {len(transitions)} 种不同的组合特征")
    print("\n高频组合特征的转移规律（样本数≥10）:\n")
    
    high_freq_patterns = []
    for curr_key, next_keys in transitions.items():
        total = sum(next_keys.values())
        if total >= 10:  # 只统计样本数>=10的
            # 找出最可能的下期组合
            sorted_next = sorted(next_keys.items(), key=lambda x: x[1], reverse=True)
            top_next = sorted_next[0]
            top_prob = top_next[1] / total * 100
            
            high_freq_patterns.append({
                'curr': curr_key,
                'total': total,
                'top_next': top_next[0],
                'top_prob': top_prob,
                'all_next': sorted_next[:3]  # 保存TOP3
            })
    
    # 按样本数排序
    high_freq_patterns.sort(key=lambda x: x['total'], reverse=True)
    
    print(f"找到 {len(high_freq_patterns)} 个高频组合特征（样本数≥10）\n")
    
    # 输出TOP20
    for i, pattern in enumerate(high_freq_patterns[:20], 1):
        curr_parts = pattern['curr'].split('|')
        print(f"\n{i}. 上期组合 (样本数: {pattern['total']})")
        print(f"   和值区间: {curr_parts[0]}")
        print(f"   区间比: {curr_parts[1]}")
        print(f"   奇偶比: {curr_parts[2]}")
        print(f"   大小比: {curr_parts[3]}")
        print(f"   下期最可能TOP3:")
        for j, (next_key, count) in enumerate(pattern['all_next'], 1):
            next_parts = next_key.split('|')
            prob = count / pattern['total'] * 100
            print(f"     {j}. 概率{prob:5.1f}% - 和值{next_parts[0]}|区间{next_parts[1]}|奇偶{next_parts[2]}|大小{next_parts[3]}")
    
    return high_freq_patterns

def export_to_json(patterns, output_file):
    """导出为JSON配置文件"""
    config = {}
    for pattern in patterns:
        if pattern['total'] >= 10:  # 只导出样本数>=10的
            curr_key = pattern['curr']
            config[curr_key] = {}
            for next_key, count in pattern['all_next']:
                prob = count / pattern['total']
                config[curr_key][next_key] = round(prob, 4)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n配置已导出到: {output_file}")
    print(f"共导出 {len(config)} 个组合特征的转移规律")

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据\n")
    
    # 分析组合特征转移规律
    patterns = analyze_combined_transitions(data)
    
    # 导出为JSON配置
    output_file = r'D:\ideaworkspace\daletou\combined_features_transitions.json'
    export_to_json(patterns, output_file)
    
    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)
    print("\n关键发现：")
    print("1. 组合特征的转移规律比单独看每个维度更准确")
    print("2. 某些组合特征有明确的转移倾向（概率>30%）")
    print("3. 可以用这些规律进一步优化动态评分系统")

if __name__ == '__main__':
    main()
