"""
测试V10确定性：验证两次运行是否产生相同结果
"""
import sys
sys.path.insert(0, 'D:\\ideaworkspace\\daletou')

from model_engine import DaletouPredictor
from feature_statistics import FeatureStatistics
from feature_predictor import FeaturePredictor
from dynamic_scoring import DynamicScorer
import numpy as np
import random

def test_determinism():
    """测试确定性"""
    print("=" * 80)
    print("测试V10确定性（两次运行应产生相同结果）")
    print("=" * 80)
    
    predictor = DaletouPredictor()
    stats = FeatureStatistics()
    
    # 尝试加载缓存的统计
    if not stats.load_statistics('model_assets/feature_statistics_v10.json'):
        print("重新构建统计...")
        stats.update_statistics(predictor.history_df)
    
    # 预测
    feature_predictor = FeaturePredictor(stats)
    last_period = predictor.history_df.iloc[-1]
    recent_10 = predictor.history_df.tail(10)
    
    predictions = feature_predictor.predict_next_period(
        last_period, recent_10, predictor.history_df
    )
    
    scorer = DynamicScorer(stats, predictions)
    
    # 运行两次，检查是否相同
    results = []
    for run in range(2):
        print(f"\n第 {run+1} 次运行:")
        print("-" * 80)
        
        # 设置随机种子
        latest_period = int(predictor.history_df.iloc[-1]['period'])
        random.seed(latest_period)
        np.random.seed(latest_period)
        print(f"随机种子: {latest_period}")
        
        # 生成候选组合
        all_red = list(range(1, 36))
        all_blue = list(range(1, 13))
        
        candidates = []
        for _ in range(100):
            red = sorted(random.sample(all_red, 5))
            blue = sorted(random.sample(all_blue, 2))
            score, _ = scorer.score_combination_v10(red, blue)
            candidates.append({'red': red, 'blue': blue, 'score': score})
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # 显示Top 5
        print("Top 5 推荐组合:")
        for i, c in enumerate(candidates[:5], 1):
            print(f"  {i}. {c['red']} - {c['blue']}  得分:{c['score']:.1f}")
        
        results.append(candidates[:10])
    
    # 验证两次结果是否完全相同
    print("\n" + "=" * 80)
    print("确定性验证结果:")
    print("=" * 80)
    
    all_same = True
    for i in range(10):
        if (results[0][i]['red'] != results[1][i]['red'] or 
            results[0][i]['blue'] != results[1][i]['blue']):
            all_same = False
            print(f"✗ 第 {i+1} 名不同:")
            print(f"  第1次: {results[0][i]['red']} - {results[0][i]['blue']}")
            print(f"  第2次: {results[1][i]['red']} - {results[1][i]['blue']}")
    
    if all_same:
        print("✓ 确定性测试通过：两次运行产生完全相同的结果！")
        print("\n这意味着：")
        print("  1. 相同的历史数据 → 相同的特征预测")
        print("  2. 相同的随机种子 → 相同的候选组合")
        print("  3. 相同的评分标准 → 相同的排序结果")
    else:
        print("✗ 确定性测试失败：两次运行产生了不同的结果")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_determinism()
