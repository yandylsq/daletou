#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
和值上下期关联分析
"""

from collections import defaultdict

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
    if 40 <= red_sum <= 60:
        return '40-60'
    elif 61 <= red_sum <= 80:
        return '61-80'
    elif 81 <= red_sum <= 100:
        return '81-100'
    elif 101 <= red_sum <= 120:
        return '101-120'
    elif 121 <= red_sum <= 140:
        return '121-140'
    elif 141 <= red_sum <= 160:
        return '141-160'
    else:
        return 'other'

def analyze_sum_transitions(data):
    """分析和值上下期转移规律"""
    sum_to_sum = defaultdict(lambda: defaultdict(int))
    
    for i in range(len(data) - 1):
        curr_sum = sum(data[i]['red'])
        next_sum = sum(data[i + 1]['red'])
        
        curr_range = get_sum_range(curr_sum)
        next_range = get_sum_range(next_sum)
        
        sum_to_sum[curr_range][next_range] += 1
    
    print("=" * 80)
    print("和值区间上下期转移规律详细分析")
    print("=" * 80)
    
    for curr_range in ['40-60', '61-80', '81-100', '101-120', '121-140', '141-160']:
        if curr_range not in sum_to_sum:
            continue
        
        total = sum(sum_to_sum[curr_range].values())
        if total < 50:
            continue
        
        print(f"\n本期和值区间: {curr_range} (样本数: {total})")
        print(f"{'下期和值区间':<15} | {'出现次数':<10} | {'概率':<10}")
        print("-" * 50)
        
        sorted_next = sorted(sum_to_sum[curr_range].items(), key=lambda x: x[1], reverse=True)
        for next_range, count in sorted_next[:6]:
            prob = count / total * 100
            print(f"{next_range:<15} | {count:<10} | {prob:>6.2f}%")

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据\n")
    
    analyze_sum_transitions(data)
    
    print("\n" + "=" * 80)
    print("统计完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
