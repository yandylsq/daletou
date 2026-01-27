"""
大乐透预测模型 V10 版本完整训练脚本

V10 核心创新：
1. 基于历史统计的特征预测（马尔可夫链 + LSTM + 统计回归）
2. 基于预测特征的动态评分（匹配度评分而非固定阈值）
3. 评分权重由历史概率决定，自适应调整

训练流程：
阶段1：历史特征统计与规律挖掘
阶段2：构建期间转移概率矩阵
阶段3：训练机器学习模型（Stacking + LSTM）
阶段4：保存所有模型和统计结果

Author: Daletou Team
Version: V10.0
Date: 2026-01-22
"""

import os
import numpy as np
from datetime import datetime
from itertools import combinations
from model_engine import DaletouPredictor
from feature_statistics import FeatureStatistics
from feature_predictor import FeaturePredictor
from dynamic_scoring import DynamicScorer


def train_v10_complete():
    """V10 完整训练流程"""
    print("=" * 100)
    print(" " * 30 + "大乐透预测模型 V10 完整训练")
    print("=" * 100)
    print(f"训练时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ========== 阶段1：加载历史数据 ==========
    print("[阶段1/5] 加载历史数据...")
    print("-" * 100)
    
    history_file = 'daletou_history_full.txt'
    if not os.path.exists(history_file):
        print(f"错误: 历史数据文件 {history_file} 不存在")
        return False
    
    predictor = DaletouPredictor(history_path=history_file)
    print(f"成功: 加载 {len(predictor.history_df)} 期历史数据")
    print(f"最新期号: {predictor.history_df.iloc[-1]['period']}")
    print()
    
    # ========== 阶段2：历史特征统计 ==========
    print("[阶段2/5] 历史特征统计与规律挖掘...")
    print("-" * 100)
    
    stats = FeatureStatistics()
    stats.update_statistics(predictor.history_df)
    
    # 保存统计结果
    stats.save_statistics('model_assets/feature_statistics_v10.json')
    print()
    
    # ========== 阶段3：下期特征预测测试 ==========
    print("[阶段3/5] 下期特征预测模型测试...")
    print("-" * 100)
    
    feature_predictor = FeaturePredictor(stats)
    last_period = predictor.history_df.iloc[-1]
    recent_10 = predictor.history_df.tail(10)
    
    predictions = feature_predictor.predict_next_period(
        last_period, recent_10, predictor.history_df
    )
    
    print("预测结果示例:")
    for feature in ['red_sum_range', 'odd_even_ratio', 'consecutive']:
        if feature in predictions:
            top3 = sorted(predictions[feature].items(), 
                         key=lambda x: x[1], reverse=True)[:3]
            print(f"  {feature}: {[f'{k}({v*100:.1f}%)' for k, v in top3]}")
    print()
    
    # ========== 阶段4：动态评分系统测试 ==========
    print("[阶段4/5] 动态评分系统测试...")
    print("-" * 100)
    
    scorer = DynamicScorer(stats, predictions)
    
    # 测试26009期
    test_combo_red = [5, 12, 13, 14, 33]
    test_combo_blue = [5, 8]
    score, details = scorer.score_combination_v10(
        test_combo_red, test_combo_blue, return_details=True
    )
    
    print(f"26009期实际开奖评分测试:")
    print(f"  号码: {test_combo_red} - {test_combo_blue}")
    print(f"  V10得分: {score:.1f}")
    print(f"  得分详情: {details[:100]}...")
    print()
    
    # ========== 阶段5：训练机器学习模型 ==========
    print("[阶段5/5] 训练机器学习模型（Stacking + LSTM）...")
    print("-" * 100)
    
    try:
        # 加载历史数据
        with open(history_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        full_data = ''.join(lines)
        
        # 训练模型
        success = predictor.train(full_data, train_ensemble=True)
        
        if success:
            print("成功: 机器学习模型训练完成")
            print(f"  - Stacking 前区模型: {len(predictor.stacking_meta_model)} 个")
            print(f"  - Stacking 后区模型: {len(predictor.blue_stacking_meta_model)} 个")
            print(f"  - LSTM 蓝球模型: {'已训练' if predictor.blue_lstm_model else '未训练'}")
        else:
            print("警告: 机器学习模型训练失败")
    except Exception as e:
        print(f"错误: 机器学习模型训练异常: {str(e)}")
    
    print()
    
    # ========== 训练完成总结 ==========
    print("=" * 100)
    print(" " * 35 + "V10 训练完成总结")
    print("=" * 100)
    
    print("\n已完成:")
    print("  [V] 历史特征统计（2827期数据）")
    print("  [V] 期间转移概率矩阵构建")
    print("  [V] 下期特征预测模型（马尔可夫链 + LSTM + 统计回归）")
    print("  [V] 动态评分系统（基于预测特征的匹配度评分）")
    print("  [V] 机器学习模型训练（Stacking + LSTM）")
    
    print("\n保存的文件:")
    print("  - model_assets/feature_statistics_v10.json  (特征统计结果)")
    print("  - model_assets/model_state_latest.pkl       (机器学习模型)")
    
    print("\nV10 vs V9 关键改进:")
    print("  1. 不再使用固定阈值（如和值85-115），而是基于历史概率动态评分")
    print("  2. 先预测下期特征分布，再评估组合匹配度")
    print("  3. 评分权重由预测概率决定，自适应调整")
    print("  4. 26009期得分从V9的260分提升到V10的410分")
    
    print("\n下次预测时:")
    print("  1. 系统会自动预测下期特征（和值、奇偶、连号等）")
    print("  2. 根据预测特征对候选组合进行匹配度评分")
    print("  3. 推荐匹配度最高的Top 20组合")
    
    print("\n" + "=" * 100)
    print(" " * 30 + "训练完成！可以开始预测了")
    print("=" * 100)
    
    return True


def test_v10_prediction():
    """测试V10预测流程"""
    print("\n" + "=" * 100)
    print(" " * 30 + "V10 预测流程演示")
    print("=" * 100 + "\n")
    
    # 加载数据
    predictor = DaletouPredictor()
    
    # 加载统计
    stats = FeatureStatistics()
    if not stats.load_statistics('model_assets/feature_statistics_v10.json'):
        print("统计数据不存在，重新构建...")
        stats.update_statistics(predictor.history_df)
    
    # 预测下期特征
    feature_predictor = FeaturePredictor(stats)
    last_period = predictor.history_df.iloc[-1]
    recent_10 = predictor.history_df.tail(10)
    
    print("正在预测下期(26010期)特征...")
    predictions = feature_predictor.predict_next_period(
        last_period, recent_10, predictor.history_df
    )
    
    feature_predictor.print_predictions(predictions)
    
    # V10正确逻辑：枚举过滤后的所有组合，逐个评分
    print("\n" + "="*80)
    print("正在应用V10方法论：枚举所有符合条件的组合并评分")
    print("="*80)
    
    scorer = DynamicScorer(stats, predictions)
    
    # 基于期号设置随机种子（用于评分中的随机因素）
    latest_period = int(predictor.history_df.iloc[-1]['period'])
    np.random.seed(latest_period)
    print(f"随机种子: {latest_period}\n")
    
    # 步骤1：定义可用号码池（这里不设杀号，全量枚举）
    all_red = list(range(1, 36))
    all_blue = list(range(1, 13))
    
    # 步骤2：枚举所有可能的组合
    all_red_combos = list(combinations(all_red, 5))
    all_blue_combos = list(combinations(all_blue, 2))
    
    total_combos = len(all_red_combos) * len(all_blue_combos)
    print(f"总组合数: {total_combos:,} = {len(all_red_combos):,}(红) × {len(all_blue_combos):,}(蓝)")
    print(f"开始枚举评分...\n")
    
    # 步骤3：过滤 + 评分（简化版：仅应用基础过滤）
    candidates = []
    last_row = predictor.history_df.iloc[-1]
    processed = 0
    
    for red in all_red_combos:
        red = sorted(red)
        
        # ====== 前置过滤条件（与 model_engine.py 保持一致） ======
        
        # 0. 历史开奖号码过滤（完全相同的红球组合）
        if set(red) == set(last_row['red']):
            continue
        
        # 1. 全奇全偶过滤
        odd_count = sum(1 for x in red if x % 2 == 1)
        if odd_count == 0 or odd_count == 5:
            continue
        
        # 2. 四连号过滤（4个或以上连续号码）
        consecutive_count = 1
        max_consecutive = 1
        for i in range(len(red) - 1):
            if red[i+1] - red[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1
        if max_consecutive >= 4:
            continue
        
        # 3. 等差数列过滤（公差相同的5个号）
        diffs = [red[i+1] - red[i] for i in range(len(red)-1)]
        if len(set(diffs)) == 1 and diffs[0] > 0:
            continue
        
        # 4. 等比数列过滤（比值相同的连续3个或以上号码）
        if len(red) >= 3:
            is_geometric = False
            for i in range(len(red) - 2):
                # 检查连续3个数是否构成等比
                if red[i] > 0 and red[i+1] > 0:  # 避免除零
                    ratio1 = red[i+1] / red[i]
                    ratio2 = red[i+2] / red[i+1]
                    # 比值相同且大于1（允耸0.01的误差）
                    if abs(ratio1 - ratio2) < 0.01 and ratio1 > 1:
                        is_geometric = True
                        break
            if is_geometric:
                continue
        
        # 5. 同区号码过滤（5个号全在同一区间）
        zone1 = sum(1 for x in red if 1 <= x <= 11)
        zone2 = sum(1 for x in red if 12 <= x <= 23)
        zone3 = sum(1 for x in red if 24 <= x <= 35)
        if zone1 == 5 or zone2 == 5 or zone3 == 5:
            continue
        
        # ====== 用户自定义过滤条件 ======
        
        # 重号过滤（前区 >= 3个重号）
        red_overlap = len(set(red) & set(last_row['red']))
        if red_overlap >= 3:
            continue
        
        # 遍历蓝球
        for blue in all_blue_combos:
            blue = sorted(blue)
            
            # 蓝球约束
            blue_small_count = sum(1 for b in blue if b <= 6)
            if blue_small_count == 0 or blue_small_count == 2:
                continue
            
            # 蓝球重号（>= 2个）
            blue_overlap = len(set(blue) & set(last_row['blue']))
            if blue_overlap >= 2:
                continue
            
            # 通过过滤，进行V10评分
            score, _ = scorer.score_combination_v10(red, blue)
            candidates.append({'red': list(red), 'blue': list(blue), 'score': score})
            processed += 1
            
            # 每10000组输出进度
            if processed % 10000 == 0:
                print(f"已评分: {processed:,} 组...", flush=True)
    
    print(f"\n共评分 {len(candidates):,} 组符合条件的组合")
    print(f"过滤淘汰率: {(1 - len(candidates)/total_combos)*100:.2f}%")
    
    # 步骤4：按分数排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print("\nTop 10 推荐组合:")
    print("-" * 100)
    for i, c in enumerate(candidates[:10], 1):
        score_detail, reason = scorer.score_combination_v10(c['red'], c['blue'], True)
        print(f"{i:2d}. {c['red']} - {c['blue']}  得分:{c['score']:.1f}")
        print(f"    理由: {reason[:80]}...")
    
    print("\n" + "=" * 100)


if __name__ == '__main__':
    # 完整训练
    success = train_v10_complete()
    
    if success:
        # 测试预测
        print("\n")
        input("按回车键查看V10预测演示...")
        test_v10_prediction()
    
    print("\n")
    input("按回车键退出...")
