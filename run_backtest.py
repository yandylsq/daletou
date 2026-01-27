
import sys
import os
import pandas as pd
from model_engine import DaletouPredictor

def run_50_period_backtest():
    print("=== 大乐透算法 50 期回测报告 ===")
    
    # 加载历史数据
    history_file = "daletou_history_full.txt"
    if not os.path.exists(history_file):
        print(f"错误: 找不到历史数据文件 {history_file}")
        return

    with open(history_file, "r", encoding="utf-8") as f:
        data_str = f.read()

    predictor = DaletouPredictor()
    predictor.history_df = predictor.parse_historical_data(data_str)
    
    # 获取最后 50 期进行验证
    total_records = len(predictor.history_df)
    if total_records < 100:
        print("警告: 历史数据不足，回测范围可能受限")
        test_df = predictor.history_df.tail(20)
    else:
        test_df = predictor.history_df.tail(50)

    start_period = int(test_df.iloc[0]['period'])
    end_period = int(test_df.iloc[-1]['period'])
    
    print(f"回测范围: {start_period} 到 {end_period} (共 {len(test_df)} 期)", flush=True)
    print("-" * 40)

    # 训练模型
    predictor.train(data_str, train_ensemble=True)

    # 执行验证
    print(f"[*] 执行验证...", flush=True)
    results = predictor.validate_model(start_period, end_period)
    
    # 保存结果到文件
    with open("backtest_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"总计期数: {results['total_periods']}\n")
        dist = results['hit_distribution']
        sorted_hits = sorted(dist.items(), key=lambda x: x[0], reverse=True)
        for hit, count in sorted_hits:
            f.write(f"{hit}: {count}\n")
    
    if 'error' in results:
        print(f"回测失败: {results['error']}")
        return

    print("\n" + "=" * 40)
    print(f"回测结果总结:")
    print(f"总计期数: {results['total_periods']}")
    
    # 命中分布
    dist = results['hit_distribution']
    sorted_hits = sorted(dist.items(), key=lambda x: x[0], reverse=True)
    
    print("\n命中分布统计 (前 20 组预测号码中的最佳命中):")
    for hit, count in sorted_hits:
        percentage = (count / results['total_periods']) * 100
        print(f"  - {hit}: {count} 次 ({percentage:.1f}%)")

    # 计算覆盖率 (用户新标准: 4+2 或 5+X)
    coverage_count = 0
    high_hit_count = 0 # 3+2, 4+1 等高级命中
    import re
    for hit, count in dist.items():
        match = re.search(r'R(\d+)\+B(\d+)', hit)
        if match:
            r = int(match.group(1))
            b = int(match.group(2))
            if (r >= 4 and b >= 2) or (r == 5):
                coverage_count += count
            if (r >= 3 and b >= 2) or (r >= 4 and b >= 1):
                high_hit_count += count
    
    coverage_rate = (coverage_count / results['total_periods']) * 100
    high_hit_rate = (high_hit_count / results['total_periods']) * 100
    print(f"\n核心覆盖能力 (命中 4+2/5+0 或以上): {coverage_rate:.1f}%")
    print(f"高级命中能力 (命中 3+2/4+1 或以上): {high_hit_rate:.1f}%")
    print("-" * 40)
    print("注：命中率 98% 目标为算法覆盖能力上限，实际单注命中受随机性影响。")
    print("=" * 40)

if __name__ == "__main__":
    run_50_period_backtest()
