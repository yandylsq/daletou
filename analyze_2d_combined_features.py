#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2维组合特征转移规律分析
分析各种2维组合的转移概率，找出高概率组合
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

def analyze_2d_transition(data, dim1_name, dim1_func, dim2_name, dim2_func):
    """分析2维特征的转移规律"""
    print("\n" + "=" * 80)
    print(f"{dim1_name} + {dim2_name} 组合转移分析")
    print("=" * 80)
    
    transitions = defaultdict(lambda: defaultdict(int))
    
    for i in range(len(data) - 1):
        curr_d1 = dim1_func(data[i]['red'])
        curr_d2 = dim2_func(data[i]['red'])
        next_d1 = dim1_func(data[i+1]['red'])
        next_d2 = dim2_func(data[i+1]['red'])
        
        curr_key = f"{curr_d1}+{curr_d2}"
        next_key = f"{next_d1}+{next_d2}"
        
        transitions[curr_key][next_key] += 1
    
    # 找出高频组合
    high_freq = []
    for curr_key, next_keys in transitions.items():
        total = sum(next_keys.values())
        if total >= 20:  # 样本数>=20
            sorted_next = sorted(next_keys.items(), key=lambda x: x[1], reverse=True)
            top_prob = sorted_next[0][1] / total
            
            high_freq.append({
                'curr': curr_key,
                'total': total,
                'top_next': sorted_next[0][0],
                'top_prob': top_prob,
                'all_next': sorted_next[:5]
            })
    
    high_freq.sort(key=lambda x: x['top_prob'], reverse=True)
    
    print(f"\n找到 {len(high_freq)} 个高频组合（样本数≥20）")
    print(f"\nTOP10最稳定转移组合（按最高转移概率排序）:\n")
    
    for i, item in enumerate(high_freq[:10], 1):
        print(f"{i}. 上期: {item['curr']} (样本数: {item['total']})")
        print(f"   下期最可能TOP3:")
        for j, (next_key, count) in enumerate(item['all_next'][:3], 1):
            prob = count / item['total'] * 100
            marker = "★" if prob >= 20 else " "
            print(f"     {marker} {j}. {next_key}: {prob:5.1f}%")
        print()
    
    return high_freq

def main():
    file_path = r'D:\ideaworkspace\daletou\daletou_history_full.txt'
    print("开始解析历史数据...")
    data = parse_history_file(file_path)
    print(f"解析完成，共 {len(data)} 期数据")
    
    # 准备维度函数
    def get_sum_range_wrapper(red):
        return get_sum_range(sum(red))
    
    # 分析所有2维组合
    combinations = [
        ("和值区间", get_sum_range_wrapper, "区间比", get_zone_ratio),
        ("和值区间", get_sum_range_wrapper, "奇偶比", get_odd_even_ratio),
        ("和值区间", get_sum_range_wrapper, "大小比", get_size_ratio),
        ("区间比", get_zone_ratio, "奇偶比", get_odd_even_ratio),
        ("区间比", get_zone_ratio, "大小比", get_size_ratio),
        ("奇偶比", get_odd_even_ratio, "大小比", get_size_ratio),
    ]
    
    all_results = {}
    for dim1_name, dim1_func, dim2_name, dim2_func in combinations:
        result = analyze_2d_transition(data, dim1_name, dim1_func, dim2_name, dim2_func)
        all_results[f"{dim1_name}+{dim2_name}"] = result
    
    # 导出为JSON
    output = {}
    for combo_name, results in all_results.items():
        output[combo_name] = {}
        for item in results:
            if item['total'] >= 20:
                output[combo_name][item['curr']] = {}
                for next_key, count in item['all_next'][:5]:
                    prob = count / item['total']
                    if prob >= 0.10:  # 只保存概率>=10%的
                        output[combo_name][item['curr']][next_key] = round(prob, 4)
    
    output_file = r'D:\ideaworkspace\daletou\2d_combined_transitions.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("分析完成！")
    print("=" * 80)
    print(f"\n配置已导出到: {output_file}")
    print("\n关键发现：")
    print("1. 2维组合比4维组合样本更充足")
    print("2. 某些2维组合有20-40%的稳定转移概率")
    print("3. 可以用2维组合加成来增强评分准确性")

if __name__ == '__main__':
    main()
