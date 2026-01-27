"""
测试开始预测API
"""
import requests
import json

# API地址
url = "http://127.0.0.1:5000/api/predict"

# 请求参数
data = {
    "task_id": "test_26010",
    "period": "26010",
    "n_combinations": 20
}

print("=" * 100)
print("调用开始预测API - 预测26010期")
print("=" * 100)
print(f"\n请求参数: {json.dumps(data, indent=2, ensure_ascii=False)}")
print("\n正在调用API...")
print("-" * 100)

try:
    response = requests.post(url, json=data, timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            predictions = result.get('predictions', [])
            
            print(f"\n✓ 预测成功！生成 {len(predictions)} 组号码")
            print("=" * 100)
            
            for i, pred in enumerate(predictions, 1):
                print(f"\n推荐度 #{i}")
                print(f"  号码: {' '.join([f'{n:02d}' for n in pred['red']])} + {' '.join([f'{n:02d}' for n in pred['blue']])}")
                print(f"  评分: {pred['score']:.2f}")
                
                # 显示选号理由
                if 'reason' in pred:
                    reason = pred['reason']
                    # 截取前150字符
                    if len(reason) > 150:
                        reason = reason[:150] + "..."
                    print(f"  理由: {reason}")
                
                print("-" * 100)
            
            # 验证实际开奖
            print("\n对比26010期实际开奖:")
            print("  实际: 02 03 13 18 26 + 02 09")
            
            actual_red = {2, 3, 13, 18, 26}
            actual_blue = {2, 9}
            
            print("\n命中情况:")
            best_hit = {'red': 0, 'blue': 0, 'rank': -1}
            
            for i, pred in enumerate(predictions, 1):
                pred_red = set(pred['red'])
                pred_blue = set(pred['blue'])
                
                red_hits = len(pred_red & actual_red)
                blue_hits = len(pred_blue & actual_blue)
                
                if red_hits > 0 or blue_hits > 0:
                    print(f"  #{i}: 前区{red_hits}个 后区{blue_hits}个")
                    
                    if red_hits > best_hit['red'] or (red_hits == best_hit['red'] and blue_hits > best_hit['blue']):
                        best_hit = {'red': red_hits, 'blue': blue_hits, 'rank': i}
            
            if best_hit['rank'] > 0:
                print(f"\n最佳命中: 前区{best_hit['red']}个 后区{best_hit['blue']}个 (排名#{best_hit['rank']})")
            else:
                print("\n无命中")
                
        else:
            print(f"\n✗ 预测失败: {result.get('error')}")
    else:
        print(f"\n✗ API调用失败: HTTP {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("\n✗ 请求超时（>300秒）")
except Exception as e:
    print(f"\n✗ 调用失败: {str(e)}")

print("\n" + "=" * 100)
