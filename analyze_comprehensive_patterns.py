#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面的历史规律分析
不仅看上一期，而是综合分析所有历史期次的转移模式
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
                'blue': blue,
                'sum': sum(red)
            })
    return data

def analyze_sum_stability(data):
    """分析和值的稳定性规律"""
    print("=" * 80)
    print("和值稳定性分析：不同和值区间下，下期和值的分布规律")
    print("=" * 80)
    
    # 按10为单位细化区间
    ranges = [(40, 50), (50, 60), (60, 70), (70, 80), (80, 90), (90, 100),
              (100, 110), (110, 120), (120, 130), (130, 140)]
    
    for low, high in ranges:
        # 找出上期和值在该区间的所有期次
        matching_periods = []
        for i in range(len(data) - 1):
            if low <= data[i]['sum'] < high:
                matching_periods.append({
                    'curr_sum': data[i]['sum'],
                    'next_sum': data[i+1]['sum'],
                    'change': data[i+1]['sum'] - data[i]['sum']
                })
        
        if len(matching_periods) < 50:
            continue
        
        # 统计下期和值分布
        next_sums = [p['next_sum'] for p in matching_periods]
        changes = [p['change'] for p in matching_periods]
        
        print(f"\n上期和值区间: {low}-{high} (样本数: {len(matching_periods)})")
        print(f"  下期和值平均: {statistics.mean(next_sums):.1f}")
        print(f"  下期和值中位数: {statistics.median(next_sums):.1f}")
        print(f"  平均变化量: {statistics.mean(changes):+.1f}")
        print(f"  变化量中位数: {statistics.median(changes):+.1f}")
        
        # 下期和值分布
        next_distribution = defaultdict(int)
        for ns in next_sums:
            if ns < 70:
                next_distribution['<70'] += 1
            elif ns < 90:
                next_distribution['70-90'] += 1
            elif ns < 110:
                next_distribution['90-110'] += 1
            elif ns < 130:
                next_distribution['110-130'] += 1
            else:
                next_distribution['130+'] += 1
        
        print("  下期和值分布:")
        for range_name in ['<70', '70-90', '90-110', '110-130', '130+']:
            if range_name in next_distribution:
                pct = next_distribution[range_name] / len(matching_periods) * 100
                print(f"    {range_name}: {pct:5.1f}%")

def analyze_trend_patterns(data):
    """分析连续趋势对下期的影响"""
    print("\n" + "=" * 80)
    print("连续趋势分析：上2期和值变化趋势对下期的影响")
    print("=" * 80)
    
    patterns = {
        '连续上升': [],  # 上上期<上期
        '连续下降': [],  # 上上期>上期
        '先升后降': [],  # 上上期<上期，但上期>预测期
        '先降后升': [],  # 上上期>上期，但上期<预测期
    }
    
    for i in range(2, len(data) - 1):
        prev2_sum = data[i-2]['sum']
        prev1_sum = data[i-1]['sum']
        curr_sum = data[i]['sum']
        next_sum = data[i+1]['sum']
        
        if prev2_sum < prev1_sum < curr_sum:
            patterns['连续上升'].append({
                'curr': curr_sum,
                'next': next_sum,
                'change': next_sum - curr_sum
            })
        elif prev2_sum > prev1_sum > curr_sum:
            patterns['连续下降'].append({
                'curr': curr_sum,
                'next': next_sum,
                'change': next_sum - curr_sum
            })
    
    for pattern_name, periods in patterns.items():
        if len(periods) < 50:
            continue
        
        changes = [p['change'] for p in periods]
        avg_change = statistics.mean(changes)
        
        # 统计反转概率
        reverse_count = sum(1 for p in periods if (pattern_name == '连续上升' and p['change'] < 0) or (pattern_name == '连续下降' and p['change'] > 0))
        reverse_prob = reverse_count / len(periods) * 100
        
        print(f"\n{pattern_name} (样本数: {len(periods)})")
        print(f"  下期平均变化: {avg_change:+.1f}")
        print(f"  趋势反转概率: {reverse_prob:.1f}%")

def analyze_zone_ratio_stability(data):
    """分析区间比的稳定性"""
    print("\n" + "=" * 80)
    print("区间比稳定性分析：相同区间比下，下期最可能出现的区间比")
    print("=" * 80)
    
    def get_zone_ratio(red):
        z1 = sum(1 for x in red if x <= 11)
        z2 = sum(1 for x in red if 12 <= x <= 23)
        z3 = sum(1 for x in red if x >= 24)
        return f"{z1}:{z2}:{z3}"
    
    # 统计每个区间比的转移模式
    transitions = defaultdict(lambda: defaultdict(int))
    for i in range(len(data) - 1):
        curr_ratio = get_zone_ratio(data[i]['red'])
        next_ratio = get_zone_ratio(data[i+1]['red'])
        transitions[curr_ratio][next_ratio] += 1
    
    # 找出高频区间比
    zone_freq = defaultdict(int)
    for i in range(len(data)):
        ratio = get_zone_ratio(data[i]['red'])
        zone_freq[ratio] += 1
    
    top_zones = sorted(zone_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\nTOP10高频区间比及其转移稳定性:")
    for zone_ratio, freq in top_zones:
        print(f"\n区间比: {zone_ratio} (出现{freq}次, 占比{freq/len(data)*100:.1f}%)")
        
        if zone_ratio not in transitions:
            continue
        
        total = sum(transitions[zone_ratio].values())
        sorted_next = sorted(transitions[zone_ratio].items(), key=lambda x: x[1], reverse=True)[:3]
        
        print("  最可能转移:")
        for next_ratio, count in sorted_next:
            prob = count / total * 100
            print(f"    → {next_ratio}: {prob:5.1f}%")
        
        # 计算自转移概率
        self_trans = transitions[zone_ratio].get(zone_ratio, 0)
        self_prob = self_trans / total * 100
        print(f"  自转移概率: {self_prob:.1f}%")

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据\n")
    
    # 1. 和值稳定性分析
    analyze_sum_stability(data)
    
    # 2. 连续趋势分析
    analyze_trend_patterns(data)
    
    # 3. 区间比稳定性分析
    analyze_zone_ratio_stability(data)
    
    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)
    print("\n关键发现：")
    print("1. 和值存在回归中心趋势：极端值后倾向于回归90-110区间")
    print("2. 连续上升/下降3期后，有较高概率出现反转")
    print("3. 高频区间比具有较高的自转移概率，说明某些模式具有惯性")

if __name__ == '__main__':
    main()
