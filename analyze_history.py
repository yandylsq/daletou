#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史数据统计分析脚本
分析2828期历史数据，为评分权重优化提供数据支撑
"""

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

def analyze_small_count(data):
    """分析小号数量分布"""
    print("=" * 60)
    print("小号数量分布统计（小号定义：1-12）")
    print("=" * 60)
    small_counts = {}
    for record in data:
        count = sum(1 for x in record['red'] if x <= 12)
        small_counts[count] = small_counts.get(count, 0) + 1
    
    total = len(data)
    print(f"总期数: {total}")
    print(f"\n小号数量 | 出现次数 | 占比")
    print("-" * 40)
    for count in sorted(small_counts.keys()):
        freq = small_counts[count]
        pct = freq / total * 100
        print(f"  {count}个   |   {freq:4d}   | {pct:6.2f}%")
    
    return small_counts

def analyze_neighbor_count(data):
    """分析邻号数量分布"""
    print("\n" + "=" * 60)
    print("邻号数量分布统计（邻号定义：与上期红球相差±1）")
    print("=" * 60)
    neighbor_counts = {}
    
    for i in range(1, len(data)):
        curr_red = set(data[i]['red'])
        last_red = set(data[i-1]['red'])
        
        count = 0
        for r in curr_red:
            if (r-1 in last_red) or (r+1 in last_red):
                count += 1
        
        neighbor_counts[count] = neighbor_counts.get(count, 0) + 1
    
    total = len(data) - 1
    print(f"总期数: {total}")
    print(f"\n邻号数量 | 出现次数 | 占比")
    print("-" * 40)
    for count in sorted(neighbor_counts.keys()):
        freq = neighbor_counts[count]
        pct = freq / total * 100
        print(f"  {count}个   |   {freq:4d}   | {pct:6.2f}%")
    
    return neighbor_counts

def analyze_sum_range(data):
    """分析和值区间分布"""
    print("\n" + "=" * 60)
    print("红球和值区间分布统计")
    print("=" * 60)
    ranges = {
        '40-60': (40, 60),
        '61-80': (61, 80),
        '81-100': (81, 100),
        '101-120': (101, 120),
        '121-140': (121, 140),
        '141-160': (141, 160)
    }
    
    range_counts = {k: 0 for k in ranges.keys()}
    
    for record in data:
        red_sum = sum(record['red'])
        for range_name, (low, high) in ranges.items():
            if low <= red_sum <= high:
                range_counts[range_name] += 1
                break
    
    total = len(data)
    print(f"总期数: {total}")
    print(f"\n和值区间  | 出现次数 | 占比")
    print("-" * 40)
    for range_name in sorted(ranges.keys()):
        freq = range_counts[range_name]
        pct = freq / total * 100
        print(f"{range_name:>9} |   {freq:4d}   | {pct:6.2f}%")
    
    return range_counts

def analyze_consecutive_pairs(data):
    """分析连号对数分布"""
    print("\n" + "=" * 60)
    print("连号对数分布统计（连号定义：红球中相差为1的数对）")
    print("=" * 60)
    consecutive_counts = {}
    
    for record in data:
        red = sorted(record['red'])
        count = 0
        for i in range(len(red) - 1):
            if red[i+1] - red[i] == 1:
                count += 1
        
        consecutive_counts[count] = consecutive_counts.get(count, 0) + 1
    
    total = len(data)
    print(f"总期数: {total}")
    print(f"\n连号对数 | 出现次数 | 占比")
    print("-" * 40)
    for count in sorted(consecutive_counts.keys()):
        freq = consecutive_counts[count]
        pct = freq / total * 100
        print(f"  {count}对   |   {freq:4d}   | {pct:6.2f}%")
    
    return consecutive_counts

def analyze_odd_even_ratio(data):
    """分析奇偶比分布"""
    print("\n" + "=" * 60)
    print("红球奇偶比分布统计")
    print("=" * 60)
    ratio_counts = {}
    
    for record in data:
        odd_count = sum(1 for x in record['red'] if x % 2 == 1)
        ratio = f"{odd_count}:{5-odd_count}"
        ratio_counts[ratio] = ratio_counts.get(ratio, 0) + 1
    
    total = len(data)
    print(f"总期数: {total}")
    print(f"\n奇偶比 | 出现次数 | 占比")
    print("-" * 40)
    for ratio in sorted(ratio_counts.keys(), key=lambda x: int(x.split(':')[0]), reverse=True):
        freq = ratio_counts[ratio]
        pct = freq / total * 100
        print(f" {ratio}  |   {freq:4d}   | {pct:6.2f}%")
    
    return ratio_counts

def analyze_similar_period_overlap(data):
    """分析历史相似期次预测准确性"""
    print("\n" + "=" * 60)
    print("历史相似期重叠号码数量分布（预测准确性验证）")
    print("=" * 60)
    print("说明：统计基于和值相似的历史期次，其下期红球与实际下期的重叠数")
    
    overlap_counts = {}
    
    for i in range(200, len(data)):  # 从第200期开始，确保有足够历史数据
        curr_sum = sum(data[i]['red'])
        curr_next_red = set(data[i]['red']) if i < len(data) - 1 else set()
        
        if i >= len(data) - 1:
            continue
        
        actual_next_red = set(data[i+1]['red'])
        
        # 查找历史和值相似的期次（相差±10）
        similar_periods = []
        for j in range(i):
            hist_sum = sum(data[j]['red'])
            if abs(hist_sum - curr_sum) <= 10 and j < len(data) - 1:
                similar_periods.append(j)
        
        if not similar_periods:
            continue
        
        # 统计历史相似期的下期红球与实际下期的重叠
        for sp_idx in similar_periods[:5]:  # 取前5个最相似的
            sp_next_red = set(data[sp_idx + 1]['red'])
            overlap = len(sp_next_red & actual_next_red)
            overlap_counts[overlap] = overlap_counts.get(overlap, 0) + 1
    
    total = sum(overlap_counts.values())
    print(f"总样本数: {total}")
    print(f"\n重叠数量 | 出现次数 | 占比")
    print("-" * 40)
    for overlap in sorted(overlap_counts.keys()):
        freq = overlap_counts[overlap]
        pct = freq / total * 100 if total > 0 else 0
        print(f"  {overlap}个   |   {freq:4d}   | {pct:6.2f}%")
    
    return overlap_counts

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据\n")
    
    # 1. 小号数量分析
    small_counts = analyze_small_count(data)
    
    # 2. 邻号数量分析
    neighbor_counts = analyze_neighbor_count(data)
    
    # 3. 和值区间分析
    sum_ranges = analyze_sum_range(data)
    
    # 4. 连号对数分析
    consecutive_counts = analyze_consecutive_pairs(data)
    
    # 5. 奇偶比分析
    ratio_counts = analyze_odd_even_ratio(data)
    
    # 6. 历史相似期重叠分析
    overlap_counts = analyze_similar_period_overlap(data)
    
    print("\n" + "=" * 60)
    print("统计分析完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
