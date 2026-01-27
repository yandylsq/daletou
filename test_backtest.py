
import os
import pandas as pd
from model_engine import DaletouPredictor

def run_test():
    with open('daletou_history_full.txt', 'r', encoding='utf-8') as f:
        data = f.read()
    
    predictor = DaletouPredictor()
    print("[*] 正在加载历史数据并训练模型...")
    predictor.train(data)
    
    # 验证最后 10 期
    history_df = predictor.history_df
    last_periods = history_df.tail(10)['period'].tolist()
    
    print(f"[*] 开始回测最后 {len(last_periods)} 期: {last_periods}")
    
    # 我们直接调用 validate_model 进行 10 期回测
    start_p = last_periods[0]
    end_p = last_periods[-1]
    
    results = predictor.validate_model(str(start_p), str(end_p))
    
    print("\n" + "="*50)
    print(f"回测汇总: {results['total_periods']} 期")
    print(f"平均前区命中: {results['avg_red_hits']}")
    print(f"平均后区命中: {results['avg_blue_hits']}")
    print("命中分布:")
    for hit, count in sorted(results['hit_distribution'].items(), reverse=True):
        print(f"  {hit}: {count} 次")
    print("="*50 + "\n")
    
    # 打印前 3 期的详细情况
    for res in results['results'][:3]:
        print(f"期号: {res['period']}")
        print(f"  实际: {res['actual_red']} + {res['actual_blue']}")
        print(f"  预测: {res['predicted_red']} + {res['predicted_blue']}")
        print(f"  命中: 前区 {res['red_hits']} | 后区 {res['blue_hits']}")
        print("-" * 20)

if __name__ == "__main__":
    run_test()
