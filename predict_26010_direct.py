"""
直接调用预测功能预测26010期
"""
import sys
sys.path.insert(0, 'D:\\ideaworkspace\\daletou')

from model_engine import DaletouPredictor
import numpy as np

print("=" * 100)
print("直接调用预测功能 - 预测26010期")
print("=" * 100)

# 初始化预测器
print("\n正在加载模型...")
predictor = DaletouPredictor()
print(f"✓ 历史数据: {len(predictor.history_df)} 期")

# 设置随机种子
np.random.seed(26010)
print(f"✓ 设置随机种子: 26010")

# 开始预测
print("\n开始预测26010期...")
print("-" * 100)

predictions = []
for i, pred in enumerate(predictor.predict('26010', n_combinations=20), 1):
    predictions.append(pred)
    if len(predictions) >= 20:
        break

print(f"\n✓ 预测完成！生成 {len(predictions)} 组号码")
print("=" * 100)

# 显示预测结果
for i, pred in enumerate(predictions, 1):
    red_str = ' '.join([f'{n:02d}' for n in pred['red']])
    blue_str = ' '.join([f'{n:02d}' for n in pred['blue']])
    print(f"\n推荐度 #{i}")
    print(f"  号码: {red_str} + {blue_str}")
    print(f"  评分: {pred['score']:.2f}")
    
    # 显示选号理由（如果有）
    if 'reason' in pred:
        reason = pred['reason']
        if len(reason) > 150:
            reason = reason[:150] + "..."
        print(f"  理由: {reason}")
    
    print("-" * 100)

# 对比实际开奖
print("\n对比26010期实际开奖:")
print("  实际: 02 03 13 18 26 + 02 09")

actual_red = {2, 3, 13, 18, 26}
actual_blue = {2, 9}

print("\n命中情况:")
best_hit = {'red': 0, 'blue': 0, 'rank': -1, 'combo': None}

for i, pred in enumerate(predictions, 1):
    pred_red = set(pred['red'])
    pred_blue = set(pred['blue'])
    
    red_hits = len(pred_red & actual_red)
    blue_hits = len(pred_blue & actual_blue)
    
    if red_hits > 0 or blue_hits > 0:
        red_str = ' '.join([f'{n:02d}' for n in pred['red']])
        blue_str = ' '.join([f'{n:02d}' for n in pred['blue']])
        print(f"  #{i}: 前区{red_hits}个 后区{blue_hits}个 ({red_str} + {blue_str})")
        
        if red_hits > best_hit['red'] or (red_hits == best_hit['red'] and blue_hits > best_hit['blue']):
            best_hit = {
                'red': red_hits, 
                'blue': blue_hits, 
                'rank': i,
                'combo': f"{red_str} + {blue_str}"
            }

if best_hit['rank'] > 0:
    print(f"\n最佳命中: 前区{best_hit['red']}个 后区{best_hit['blue']}个 (排名#{best_hit['rank']})")
    print(f"  号码: {best_hit['combo']}")
else:
    print("\n✗ 无命中")

# 分析预测特征
print("\n" + "=" * 100)
print("预测特征分析:")
print("=" * 100)

pred_sums = [sum(p['red']) for p in predictions]
small_counts = [sum(1 for x in p['red'] if x <= 15) for p in predictions]

print(f"\n和值分布:")
print(f"  最小: {min(pred_sums)}")
print(f"  最大: {max(pred_sums)}")
print(f"  平均: {np.mean(pred_sums):.1f}")
print(f"  实际: {sum(actual_red)} (26010期)")

if min(pred_sums) <= 62 <= max(pred_sums):
    print(f"  ✓ 实际和值在预测范围内")
else:
    print(f"  ✗ 实际和值不在预测范围内")

print(f"\n小号分布 (≤15):")
print(f"  平均每组: {np.mean(small_counts):.1f}个")
print(f"  最少: {min(small_counts)}个")
print(f"  最多: {max(small_counts)}个")
actual_small = sum(1 for x in actual_red if x <= 15)
print(f"  实际: {actual_small}个 (26010期)")

print("\n" + "=" * 100)
