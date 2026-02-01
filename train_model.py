#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大乐透预测模型训练脚本（V12.4版本）

V12.4 动态评分系统：
1. 单维度动态评分（和值、区间比、奇偶比、大小比）
2. 2维组合加成（基于历史组合转移概率）
3. 全部基于2831期全量历史数据统计

本脚本只训练ML模型（Stacking + LSTM），评分逻辑已集成到model_engine.py中。
"""

import os
import sys
from datetime import datetime
from model_engine import DaletouPredictor

def train_model():
    """训练ML模型（Stacking + LSTM）"""
    print("=" * 80)
    print("🚀 大乐透预测模型训练（V12.4 动态评分系统）")
    print("=" * 80)
    print(f"训练时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查历史数据文件
    history_file = 'daletou_history_full.txt'
    if not os.path.exists(history_file):
        print(f"❌ 错误: 历史数据文件 {history_file} 不存在")
        return False
    
    # 读取历史数据
    print(f"📖 正在加载历史数据: {history_file}")
    with open(history_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 统计最新期号
    last_line = lines[-1].strip()
    if last_line:
        parts = last_line.split()
        if len(parts) >= 3:
            latest_period = parts[0]
            print(f"📊 历史数据期数: {len(lines)} 期")
            print(f"📅 最新期号: {latest_period}")
    print()
    
    # 创建预测器并训练
    print("🔧 初始化预测引擎（集成V12.4动态评分）...")
    predictor = DaletouPredictor(history_path=history_file)
    
    print("🎯 开始训练ML模型（Stacking + LSTM）...")
    print("-" * 80)
    
    try:
        # 加载数据并训练
        full_data = '\n'.join(lines)
        success = predictor.train(full_data, train_ensemble=True)
        
        if success:
            print("-" * 80)
            print()
            print("✅ ML模型训练完成!")
            print()
            
            # 显示模型信息
            print("📋 模型信息:")
            print(f"  - 历史数据期数: {len(predictor.history_df)}")
            print(f"  - 训练状态: {'已训练' if predictor.is_trained else '未训练'}")
            print(f"  - Stacking 前区模型: {len(predictor.stacking_meta_model)} 个号码")
            print(f"  - Stacking 后区模型: {len(predictor.blue_stacking_meta_model)} 个号码")
            print(f"  - LSTM 蓝球模型: {'已训练' if predictor.blue_lstm_model else '未训练'}")
            print()
            
            # 检查模型文件
            model_file = 'model_assets/model_state_latest.pkl'
            if os.path.exists(model_file):
                file_size = os.path.getsize(model_file) / 1024 / 1024  # MB
                print(f"💾 模型文件: {model_file}")
                print(f"📦 文件大小: {file_size:.2f} MB")
            else:
                print(f"⚠️  警告: 模型文件未找到 {model_file}")
            
            print()
            print("=" * 80)
            print("🎉 训练完成！")
            print("=" * 80)
            print()
            print("V12.4 动态评分系统说明:")
            print("  1. 评分逻辑已集成到 model_engine.py 中")
            print("  2. 动态评分配置文件: dynamic_scoring_rules.py")
            print("  3. 2维组合转移概率: 2d_combined_transitions.json")
            print("  4. 基于2831期全量历史数据统计")
            print()
            print("可以开始预测了！")
            print("=" * 80)
            
            return True
        else:
            print("❌ 训练失败")
            return False
            
    except Exception as e:
        print()
        print(f"❌ 训练过程中出现错误: {str(e)}")
        import traceback
        print()
        print("详细错误信息:")
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    # 训练模型
    success = train_model()
    
    if not success:
        print()
        print("训练失败，请检查错误信息")
    
    print()
    input("按回车键退出...")
