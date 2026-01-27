"""
模拟用户实际使用场景：多次运行完整训练后预测流程
"""
import sys
sys.path.insert(0, 'D:\\ideaworkspace\\daletou')

from train_v10_model import test_v10_prediction

def simulate_user_runs():
    """模拟用户多次运行"""
    print("=" * 80)
    print("模拟用户场景：训练完V10后，多次查看推荐组合")
    print("=" * 80)
    
    for i in range(3):
        print(f"\n\n{'#' * 80}")
        print(f"第 {i+1} 次运行 - 用户执行: python train_v10_model.py")
        print('#' * 80)
        
        try:
            test_v10_prediction()
        except Exception as e:
            print(f"运行出错: {e}")
            import traceback
            traceback.print_exc()
        
        if i < 2:
            print("\n[用户操作] 关闭程序...")
            print("[用户操作] 再次运行程序...")


if __name__ == '__main__':
    simulate_user_runs()
