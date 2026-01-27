"""
大乐透预测模型 V9 版本训练脚本

V9 更新说明:
1. 修复三连号过度惩罚问题
2. 放宽 AC 值容忍度
3. 扩大和值接受范围
4. 增加连号特征维度 (consecutive_2, consecutive_3, consecutive_4plus)
5. 优化评分策略
6. 增强模型对罕见模式的学习能力

针对 26009 期预测失败原因:
- 开奖号码: 05 12 13 14 33 - 05 08
- 包含三连号 12-13-14，旧算法过度惩罚
- 和值 77 偏小但合理
- AC 值可能偏低但不应完全过滤

训练后会自动保存到: model_assets/model_state_v9_latest.pkl
"""

import os
import sys
from datetime import datetime
from model_engine import DaletouPredictor

def train_v9_model():
    """训练 V9 版本模型"""
    print("="*80)
    print("🚀 大乐透预测模型 V9 版本训练")
    print("="*80)
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
    print("🔧 初始化预测引擎...")
    predictor = DaletouPredictor(history_path=history_file)
    
    print("🎯 开始训练模型...")
    print("-" * 80)
    
    try:
        # 加载数据并训练
        full_data = '\n'.join(lines)
        success = predictor.train(full_data, train_ensemble=True)
        
        if success:
            print("-" * 80)
            print()
            print("✅ V9 模型训练完成!")
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
            model_file = 'model_assets/model_state_v9_latest.pkl'
            if os.path.exists(model_file):
                file_size = os.path.getsize(model_file) / 1024 / 1024  # MB
                print(f"💾 模型文件: {model_file}")
                print(f"📦 文件大小: {file_size:.2f} MB")
            else:
                print(f"⚠️  警告: 模型文件未找到 {model_file}")
            
            print()
            print("=" * 80)
            print("🎉 训练完成！模型已持久化，可以开始预测了")
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

def test_v9_model():
    """测试 V9 模型对三连号的处理"""
    print()
    print("=" * 80)
    print("🧪 测试 V9 模型对连号的处理")
    print("=" * 80)
    
    predictor = DaletouPredictor(history_path='daletou_history_full.txt')
    
    # 尝试加载 V9 模型
    if predictor.load_state(tag='v9_latest'):
        print("✅ 成功加载 V9 模型")
    else:
        print("⚠️  未找到 V9 模型，使用默认模型")
    
    # 测试不同连号情况的评分
    test_cases = [
        {
            'name': '无连号',
            'red': [5, 12, 18, 25, 33],
            'blue': [5, 8]
        },
        {
            'name': '两连号 (12-13)',
            'red': [5, 12, 13, 20, 33],
            'blue': [5, 8]
        },
        {
            'name': '三连号 (12-13-14) - 类似26009期',
            'red': [5, 12, 13, 14, 33],
            'blue': [5, 8]
        },
        {
            'name': '四连号 (12-13-14-15)',
            'red': [5, 12, 13, 14, 15],
            'blue': [5, 8]
        }
    ]
    
    print()
    print("评分对比:")
    print("-" * 80)
    
    # 获取必要信息
    hc = predictor.calculate_hot_cold(predictor.history_df)
    last_record = predictor.history_df.iloc[-1] if len(predictor.history_df) > 0 else None
    
    for case in test_cases:
        score, details = predictor.score_combination(
            case['red'], 
            case['blue'], 
            hc, 
            last_record=last_record,
            return_details=True
        )
        print(f"\n{case['name']}")
        print(f"  号码: {case['red']} - {case['blue']}")
        print(f"  得分: {score:.2f}")
        print(f"  详情: {details}")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    # 训练模型
    success = train_v9_model()
    
    if success:
        # 测试模型
        test_v9_model()
    
    print()
    input("按回车键退出...")
