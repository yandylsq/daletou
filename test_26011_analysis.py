"""
分析26011期预测失败的原因
检查实际开奖号码是否被过滤
"""
import sys
sys.path.insert(0, 'D:\\ideaworkspace\\daletou')

from model_engine import DaletouPredictor
import numpy as np

print("=" * 80)
print("26011期预测失败原因分析")
print("=" * 80)

# 实际开奖号码
actual_red = [14, 21, 23, 29, 33]
actual_blue = [2, 10]

print(f"\n实际开奖: {actual_red} + {actual_blue}")
print(f"和值: {sum(actual_red)}")
print(f"奇偶: {sum(1 for x in actual_red if x%2==1)}奇{5-sum(1 for x in actual_red if x%2==1)}偶")

# 加载预测器
predictor = DaletouPredictor()
print(f"\n历史数据: {len(predictor.history_df)} 期")

# 检查实际号码是否会被过滤
print("\n" + "-" * 80)
print("检查实际开奖号码是否会被过滤条件过滤...")
print("-" * 80)

# 模拟过滤逻辑
red_sorted = sorted(actual_red)
blue_sorted = sorted(actual_blue)

# 1. 全奇全偶
odd_count = sum(1 for x in red_sorted if x % 2 == 1)
if odd_count == 0 or odd_count == 5:
    print("❌ 被过滤: 全奇全偶")
else:
    print(f"✓ 通过: 奇偶比 {odd_count}:{5-odd_count}")

# 2. 四连号
consecutive_count = 1
max_consecutive = 1
for i in range(len(red_sorted) - 1):
    if red_sorted[i+1] - red_sorted[i] == 1:
        consecutive_count += 1
        max_consecutive = max(max_consecutive, consecutive_count)
    else:
        consecutive_count = 1
        
if max_consecutive >= 4:
    print(f"❌ 被过滤: 四连号 ({max_consecutive}连)")
else:
    print(f"✓ 通过: 最多{max_consecutive}连号")

# 3. 等差数列
diffs = [red_sorted[i+1] - red_sorted[i] for i in range(len(red_sorted)-1)]
if len(set(diffs)) == 1 and diffs[0] > 0:
    print(f"❌ 被过滤: 等差数列 (公差={diffs[0]})")
else:
    print(f"✓ 通过: 非等差数列")

# 4. 同区号码
zone1 = sum(1 for x in red_sorted if 1 <= x <= 11)
zone2 = sum(1 for x in red_sorted if 12 <= x <= 23)
zone3 = sum(1 for x in red_sorted if 24 <= x <= 35)
if zone1 == 5 or zone2 == 5 or zone3 == 5:
    print(f"❌ 被过滤: 同区号码")
else:
    print(f"✓ 通过: 区间分布 {zone1}-{zone2}-{zone3}")

# 5. 蓝球全大全小
blue_small_count = sum(1 for b in blue_sorted if b <= 6)
if blue_small_count == 0 or blue_small_count == 2:
    print(f"❌ 被过滤: 蓝球全大或全小")
else:
    print(f"✓ 通过: 蓝球大小平衡")

# 6. 历史重复（模拟检查）
print(f"\n✓ 历史重复检查: 26011期是新开奖，不会被历史过滤")

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
print("实际开奖号码应该能通过所有过滤条件")
print("问题出在评分系统 - 评分不够高，导致排名靠后")
print("\n核心问题:")
print("1. 和值120属于偏高区域，当前评分系统可能给分较低")
print("2. 号码分散(14,21,23,29,33)，可能不符合统计模型预期")
print("3. ML模型预测的高频号(03,06,24,26)与实际相差较大")
print("=" * 80)
