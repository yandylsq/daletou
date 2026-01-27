"""
V11激进优化版 - 50期回测验证脚本
验证标准：4+2命中（4个红球+2个蓝球）
目标准确率：95%
"""
import sys
sys.path.insert(0, 'D:\\ideaworkspace\\daletou')

from model_engine import DaletouPredictor
import pandas as pd
from datetime import datetime

print("=" * 100)
print("V11激进优化版 - 50期回测验证")
print("命中标准：4+2（4个红球+2个蓝球）")
print("目标准确率：95%")
print("=" * 100)

# 加载历史数据
predictor = DaletouPredictor()
history_df = predictor.history_df

# 获取最近50期用于回测
if len(history_df) < 51:
    print(f"[ERROR] 历史数据不足50期！当前只有{len(history_df)}期")
    sys.exit(1)

# 获取最近50期
recent_50 = history_df.tail(50).copy()
print(f"\n[*] 准备回测最近50期：{recent_50['period'].min()} - {recent_50['period'].max()}")
print(f"[*] 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 统计结果
results = []
hit_count_4_2 = 0  # 4+2命中次数

for idx, row in recent_50.iterrows():
    period = row['period']
    actual_red = sorted(row['red'])
    actual_blue = sorted(row['blue'])
    
    print(f"\n{'='*80}")
    print(f"回测期号：{period}")
    print(f"实际开奖：{actual_red} + {actual_blue}")
    
    # 使用该期之前的数据训练
    train_data = history_df[history_df['period'] < period].copy()
    
    if len(train_data) < 10:
        print(f"[SKIP] 训练数据不足10期，跳过")
        continue
    
    # 创建子预测器
    sub_predictor = DaletouPredictor()
    sub_predictor.history_df = train_data
    
    # 训练模型
    print(f"[*] 使用前{len(train_data)}期训练...")
    # 不需要调用train，模型会在predict时自动训练
    # sub_predictor.train()
    
    # 预测Top 20
    print(f"[*] 生成预测...")
    predictions = []
    
    for pred in sub_predictor.predict(
        period=period,
        n_combinations=20,
        is_backtest=True,
        kill_red=[],
        kill_blue=[]
    ):
        if pred and pred.get('type') == 'single':
            predictions.append(pred)
    
    if len(predictions) == 0:
        print(f"[ERROR] 预测失败！")
        results.append({
            'period': period,
            'hit_red': 0,
            'hit_blue': 0,
            'best_rank': -1,
            'hit_4_2': False
        })
        continue
    
    # 检查命中情况
    best_red_hit = 0
    best_blue_hit = 0
    best_rank = -1
    hit_4_2_found = False
    
    for i, pred in enumerate(predictions):
        pred_red = set(pred['red'])
        pred_blue = set(pred['blue'])
        
        red_hits = len(pred_red & set(actual_red))
        blue_hits = len(pred_blue & set(actual_blue))
        
        # 记录最佳命中
        if red_hits > best_red_hit or (red_hits == best_red_hit and blue_hits > best_blue_hit):
            best_red_hit = red_hits
            best_blue_hit = blue_hits
            best_rank = i + 1
        
        # 检查是否达到4+2
        if red_hits >= 4 and blue_hits >= 2:
            hit_4_2_found = True
            print(f"✅ 命中4+2！排名：Top {i+1}")
            print(f"   预测：{sorted(pred['red'])} + {sorted(pred['blue'])}")
            print(f"   命中：前区{red_hits}个，后区{blue_hits}个")
            break
    
    if hit_4_2_found:
        hit_count_4_2 += 1
    else:
        print(f"❌ 未命中4+2，最佳：{best_red_hit}+{best_blue_hit}（Top {best_rank}）")
        # 显示Top 3预测
        print(f"\n   Top 3预测：")
        for i in range(min(3, len(predictions))):
            pred = predictions[i]
            print(f"   {i+1}. {sorted(pred['red'])} + {sorted(pred['blue'])}")
    
    results.append({
        'period': period,
        'hit_red': best_red_hit,
        'hit_blue': best_blue_hit,
        'best_rank': best_rank,
        'hit_4_2': hit_4_2_found
    })

# 统计汇总
print(f"\n{'='*100}")
print("回测结果汇总")
print(f"{'='*100}")

total_periods = len(results)
accuracy_4_2 = (hit_count_4_2 / total_periods * 100) if total_periods > 0 else 0

print(f"\n总回测期数：{total_periods}期")
print(f"4+2命中次数：{hit_count_4_2}次")
print(f"4+2命中率：{accuracy_4_2:.2f}%")

if accuracy_4_2 >= 95:
    print(f"\n🎉 恭喜！已达到95%的目标准确率！")
else:
    print(f"\n⚠️  当前准确率{accuracy_4_2:.2f}%，距离目标95%还差{95-accuracy_4_2:.2f}%")

# 详细统计
print(f"\n命中分布统计：")
hit_dist = {}
for r in results:
    key = f"{r['hit_red']}+{r['hit_blue']}"
    hit_dist[key] = hit_dist.get(key, 0) + 1

for key in sorted(hit_dist.keys(), reverse=True):
    count = hit_dist[key]
    pct = count / total_periods * 100
    print(f"  {key}: {count}次 ({pct:.1f}%)")

print(f"\n结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
