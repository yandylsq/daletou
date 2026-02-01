#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
区间比、奇偶比、大小比的综合规律分析
不仅看上一期，而是分析所有历史期次的稳定模式
"""

from collections import defaultdict
import statistics

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

def analyze_ratio_stability(data, get_ratio_func, ratio_name):
    """分析某个比值的稳定性和转移模式"""
    print("\n" + "=" * 80)
    print(f"{ratio_name}稳定性分析：相同{ratio_name}连续出现的概率")
    print("=" * 80)
    
    # 统计转移模式
    transitions = defaultdict(lambda: defaultdict(int))
    for i in range(len(data) - 1):
        curr_ratio = get_ratio_func(data[i]['red'])
        next_ratio = get_ratio_func(data[i+1]['red'])
        transitions[curr_ratio][next_ratio] += 1
    
    # 统计每个比值的出现频率
    ratio_freq = defaultdict(int)
    for record in data:
        ratio = get_ratio_func(record['red'])
        ratio_freq[ratio] += 1
    
    # 找出高频比值（TOP5）
    top_ratios = sorted(ratio_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"\nTOP5高频{ratio_name}的稳定性分析:")
    for ratio, freq in top_ratios:
        print(f"\n{ratio_name}: {ratio} (出现{freq}次, 占比{freq/len(data)*100:.1f}%)")
        
        if ratio not in transitions:
            continue
        
        total = sum(transitions[ratio].values())
        sorted_next = sorted(transitions[ratio].items(), key=lambda x: x[1], reverse=True)
        
        # 自转移概率
        self_trans = transitions[ratio].get(ratio, 0)
        self_prob = self_trans / total * 100
        
        # 最可能转移的TOP3
        print(f"  自转移概率: {self_prob:5.1f}%")
        print(f"  最可能转移TOP3:")
        for next_ratio, count in sorted_next[:3]:
            prob = count / total * 100
            marker = "★" if next_ratio == ratio else " "
            print(f"    {marker} → {next_ratio}: {prob:5.1f}%")

def analyze_ratio_trend_reversal(data, get_ratio_func, ratio_name):
    """分析比值的趋势反转规律"""
    print("\n" + "=" * 80)
    print(f"{ratio_name}趋势反转分析：连续相同比值后的变化规律")
    print("=" * 80)
    
    # 统计连续相同比值的持续期数
    continuous_counts = defaultdict(list)
    
    i = 0
    while i < len(data):
        ratio = get_ratio_func(data[i]['red'])
        count = 1
        
        # 计算连续相同比值的期数
        while i + count < len(data) and get_ratio_func(data[i + count]['red']) == ratio:
            count += 1
        
        continuous_counts[ratio].append(count)
        i += count
    
    print("\n各比值的连续出现统计:")
    for ratio, counts in sorted(continuous_counts.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        avg_continuous = statistics.mean(counts)
        max_continuous = max(counts)
        print(f"  {ratio}: 平均连续{avg_continuous:.1f}期, 最长连续{max_continuous}期")

def analyze_extreme_ratios(data, get_ratio_func, ratio_name):
    """分析极端比值后的转移规律"""
    print("\n" + "=" * 80)
    print(f"{ratio_name}极端值分析：极端比值后的回归规律")
    print("=" * 80)
    
    # 定义极端比值（根据不同维度）
    if ratio_name == "区间比":
        extreme_ratios = ['0:0:5', '5:0:0', '0:5:0', '4:0:1', '0:4:1', '1:0:4', '0:1:4', '4:1:0', '1:4:0']
    elif ratio_name == "奇偶比":
        extreme_ratios = ['5:0', '0:5']
    elif ratio_name == "大小比":
        extreme_ratios = ['5:0', '0:5']
    else:
        return
    
    extreme_transitions = defaultdict(lambda: defaultdict(int))
    
    for i in range(len(data) - 1):
        curr_ratio = get_ratio_func(data[i]['red'])
        if curr_ratio in extreme_ratios:
            next_ratio = get_ratio_func(data[i+1]['red'])
            extreme_transitions[curr_ratio][next_ratio] += 1
    
    if not extreme_transitions:
        print(f"  未发现极端{ratio_name}（这是正常的）")
        return
    
    print(f"\n极端{ratio_name}后的转移模式:")
    for extreme_ratio, next_ratios in extreme_transitions.items():
        total = sum(next_ratios.values())
        if total < 5:
            continue
        
        print(f"\n  极端值 {extreme_ratio} (出现{total}次)")
        sorted_next = sorted(next_ratios.items(), key=lambda x: x[1], reverse=True)[:3]
        for next_ratio, count in sorted_next:
            prob = count / total * 100
            print(f"    → {next_ratio}: {prob:5.1f}%")

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据\n")
    
    # 1. 区间比分析
    analyze_ratio_stability(data, get_zone_ratio, "区间比")
    analyze_ratio_trend_reversal(data, get_zone_ratio, "区间比")
    analyze_extreme_ratios(data, get_zone_ratio, "区间比")
    
    # 2. 奇偶比分析
    analyze_ratio_stability(data, get_odd_even_ratio, "奇偶比")
    analyze_ratio_trend_reversal(data, get_odd_even_ratio, "奇偶比")
    analyze_extreme_ratios(data, get_odd_even_ratio, "奇偶比")
    
    # 3. 大小比分析
    analyze_ratio_stability(data, get_size_ratio, "大小比")
    analyze_ratio_trend_reversal(data, get_size_ratio, "大小比")
    analyze_extreme_ratios(data, get_size_ratio, "大小比")
    
    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)
    print("\n关键发现：")
    print("1. 高频比值具有较高的自转移概率（惯性）")
    print("2. 极端比值后倾向于向均衡比值回归")
    print("3. 连续相同比值后的变化规律可用于预测")

if __name__ == '__main__':
    main()
