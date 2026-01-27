# -*- coding: utf-8 -*-
"""
大乐透号码导出工具 - 修复版
用于导出所有符合条件的号码组合，并排除不符合预期的组合类型
"""
import pandas as pd
from itertools import combinations
import os
from datetime import datetime

class DaletouExporter:
    """大乐透号码导出器"""
    
    def __init__(self):
        # 大乐透号码范围：红球35个，蓝球12个
        self.red_range = range(1, 36)  # 1-35
        self.blue_range = range(1, 13)  # 1-12
        
        # 区间定义
        self.zone1 = range(1, 12)   # 1-11
        self.zone2 = range(12, 24)  # 12-23
        self.zone3 = range(24, 36)  # 24-35
        
    def get_all_combinations(self):
        """获取所有可能的大乐透号码组合（约2143万组）"""
        print("开始生成所有可能的大乐透号码组合...")
        
        all_combos = set()
        red_combos = list(combinations(self.red_range, 5))
        blue_combos = list(combinations(self.blue_range, 2))
        
        total = len(red_combos) * len(blue_combos)
        print(f"红球组合数: {len(red_combos):,}")
        print(f"蓝球组合数: {len(blue_combos):,}")
        print(f"总组合数: {total:,}")
        
        for red in red_combos:
            for blue in blue_combos:
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                all_combos.add(combo)
        
        return all_combos
    
    def get_historical_combinations(self):
        """获取历史开奖号码组合"""
        print("\n开始获取历史开奖数据...")
        
        historical_combos = set()
        
        # 优先从本地文件加载完整历史数据
        local_file = 'daletou_history_full.txt'
        
        if os.path.exists(local_file):
            print(f"找到本地历史数据文件: {local_file}")
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    historical_data = f.read()
                    historical_combos = self._parse_historical_data(historical_data)
                    
                    if len(historical_combos) > 0:
                        print(f"成功加载历史开奖数据: {len(historical_combos)} 组")
                        
                        # 验证数据完整性
                        if len(historical_combos) >= 1500:
                            print(f"数据完整性验证通过，包含 {len(historical_combos)} 期")
                        else:
                            print(f"警告: 数据可能不完整，仅包含 {len(historical_combos)} 期，建议包含1500+期")
                        
                        return historical_combos
            except Exception as e:
                print(f"读取本地历史数据文件失败: {e}")
                print("将使用默认数据...")
        else:
            print(f"警告: 未找到本地历史数据文件: {local_file}")
            print("请运行 python download_history.py 下载完整历史数据")
        
        # 回退方案：使用内置的部分历史数据
        print("使用内置历史数据（最近70期）...")
        
        historical_data = """25150	2025-12-31 13 14 15 28 31-01 05
25149	2025-12-29	24 26 30 31 32-05 12
25148	2025-12-27	03 04 14 30 32-08 12
25147	2025-12-24	06 16 21 25 33-07 08
25146	2025-12-22	06 11 13 16 22-02 03
25145	2025-12-20	05 07 20 22 25-04 05
25144	2025-12-17	02 05 13 15 28-05 08
25143	2025-12-15	03 04 18 24 29-07 12
25142	2025-12-13	09 10 14 27 29-02 09
25141	2025-12-10	04 09 24 28 29-02 10
25140	2025-12-08	04 05 13 18 34-02 08
25139	2025-12-06	08 18 22 30 35-01 04
25138	2025-12-03	01 	03 19 21 23-07 11
25137	2025-11-29	07	08	09	11	22-05	11
25136	2025-11-29	07	11	15	16	23-09	11
25135	2025-11-26	02	10	16	28	32-01	07
25134	2025-11-24	07	12	18	27	33-09	10
25133	2025-11-22	04	11	23	27	35-07	11
25132	2025-11-19	01	09	10	12	19-06	07
25131	2025-11-17	03	08	25	29	32-09	12
25130	2025-11-15	01	13	16	27	29-02	11
25129	2025-11-12	03	09	14	28	35-02	04
25128	2025-11-10	03	06	26	30	33-11	12
25127	2025-11-08	04	05	19	28	29-05	08
25126	2025-11-05	01	08	18	27	30-06	07
25125	2025-11-03	10	11	13	19	35-04	11
25124	2025-11-01	06	09	14	26	27-08	09
25123	2025-10-29	08	13	24	25	31-04	10
25122	2025-10-27	02	03	06	16	17-04	05
25121	2025-10-25	02	03	08	13	21-07	12
25120	2025-10-22	11	13	22	26	35-02	08
25119	2025-10-20	08	15	27	29	31-01	07
25118	2025-10-18	02	08	09	12	21-04	05
25117	2025-10-15	05	10	18	21	29-05	07
25116	2025-10-13	02	06	16	22	29-08	12
25115	2025-10-11	03	12	14	21	35-01	05
25114	2025-10-08	03	08	09	12	16-01	05
25113	2025-10-06	01	14	18	28	35-02	03
25112	2025-09-29	03	04	21	23	24-09	12
25111	2025-09-27	02	09	14	21	26-02	12
25110	2025-09-24	01	15	22	30	31-02	08
25109	2025-09-22	04	08	10	13	26-09	10
25108	2025-09-20	14	18	21	24	29-03	06
25107	2025-09-17	05	07	08	15	33-06	10
25106	2025-09-15	05	06	11	26	29-05	10
25105	2025-09-13	15	16	25	28	34-10	12
25104	2025-09-10	02	06	09	22	34-02	08
25103	2025-09-08	05	08	19	32	34-04	05
25102	2025-09-06	09	10	13	26	28-02	04
25101	2025-09-03	05	07	19	26	32-08	09
25100	2025-09-01	26 	28	32 	34	35-02	07
25099	2025-08-30	06	12	20	26	31-02	04
25098	2025-08-27	01	07	09	10	23-10	12
25097	2025-08-25	05	24	25	32	34-01	09
25096	2025-08-23	02	11	17	22	24-07	09
25095	2025-08-20	07	13	14	19	27-06	10
25094	2025-08-18	04	09	17	30	33-05	09
25093	2025-08-16	01	07	09	16	30-02	05
25092	2025-08-13	04	10	17	25	32-05	07
25091	2025-08-11	01	19	22	25	27-03	10
25090	2025-08-09	06	14	19	22	27-01	04
25089	2025-08-06	02	11	12	32	34-03	10	
25088	2025-08-04	08	09	10	11	35-05	11	
25087	2025-08-02	05	13	14	16	20-03	08	
25086	2025-07-30	02	06	23	24	33-01	10	
25085	2025-07-28	02	05	09	14	33-04	09	
25084	2025-07-26	09	11	13	18	29-04	11	
25083	2025-07-23	12	17	18	20	34-02	05	
25082	2025-07-21	02	03	04	12	26-01	08	
25081	2025-07-19	01	04	06	15	18-02	03	
25080	2025-07-16	09	10	18	22	24-03	12"""
        
        historical_combos = set()
        for line in historical_data.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                numbers_str = ' '.join(parts[2:])
                if '-' in numbers_str:
                    red_part, blue_part = numbers_str.split('-')
                    red = sorted([int(x) for x in red_part.split() if x.isdigit()])
                    blue = sorted([int(x) for x in blue_part.split() if x.isdigit()])
                    
                    if len(red) == 5 and len(blue) == 2:
                        combo = tuple(red) + tuple(blue)
                        historical_combos.add(combo)
        
        print(f"加载历史数据完成: {len(historical_combos)}")
        return historical_combos
    
    def _parse_historical_data(self, historical_data):
        """解析历史数据文本，提取号码组合"""
        historical_combos = set()
        
        for line in historical_data.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                numbers_str = ' '.join(parts[2:])
                if '-' in numbers_str:
                    red_part, blue_part = numbers_str.split('-')
                    red = sorted([int(x) for x in red_part.split() if x.isdigit()])
                    blue = sorted([int(x) for x in blue_part.split() if x.isdigit()])
                    
                    if len(red) == 5 and len(blue) == 2:
                        combo = tuple(red) + tuple(blue)
                        historical_combos.add(combo)
        
        return historical_combos
    
    def get_consecutive_combinations(self):
        """获取包含四连号的组合（例如：1,2,3,4或5,6,7,8）"""
        print("\n开始生成四连号组合...")
        
        consecutive_combos = set()
        
        # 遍历所有5个红球组合，检查是否包含4个或以上连续号码
        for red in combinations(self.red_range, 5):
            red_sorted = sorted(red)
            
            # 检查是否有4个连续号码
            has_four_consecutive = False
            for i in range(len(red_sorted) - 3):  # 检查每4个连续位置
                if (red_sorted[i+1] == red_sorted[i] + 1 and 
                    red_sorted[i+2] == red_sorted[i] + 2 and 
                    red_sorted[i+3] == red_sorted[i] + 3):
                    has_four_consecutive = True
                    break
            
            if has_four_consecutive:
                # 与所有蓝球组合配对
                for blue in combinations(self.blue_range, 2):
                    combo = tuple(red_sorted) + tuple(sorted(blue))
                    consecutive_combos.add(combo)
        
        print(f"四连号组合数: {len(consecutive_combos):,}")
        return consecutive_combos
    
    def get_arithmetic_combinations(self):
        """获取等差数列/等比数列组合"""
        print("\n开始生成等差/等比数列组合...")
        
        arithmetic_combos = set()
        
        # 等差数列：公差从1到6
        for diff in range(1, 7):
            for start in range(1, 36):
                seq = [start + i * diff for i in range(5)]
                if all(1 <= x <= 35 for x in seq):
                    red = tuple(sorted(seq))
                    # 与所有蓝球组合配对
                    for blue in combinations(self.blue_range, 2):
                        combo = red + tuple(sorted(blue))
                        arithmetic_combos.add(combo)
        
        # 等比数列：公比为2（例如：2,4,8,16 或 2,4,8,16,32等）
        for start in range(1, 18):
            seq = [start * (2 ** i) for i in range(5)]
            if all(1 <= x <= 35 for x in seq):
                red = tuple(sorted(seq))
                for blue in combinations(self.blue_range, 2):
                    combo = red + tuple(sorted(blue))
                    arithmetic_combos.add(combo)
        
        print(f"等差/等比数列组合数: {len(arithmetic_combos)}")
        return arithmetic_combos
    
    def get_odd_even_combinations(self):
        """获取全奇或全偶组合"""
        print("\n开始生成全奇/全偶组合...")
        
        odd_even_combos = set()
        
        # 红球奇数：1,3,5,...,35
        odd_numbers = [x for x in range(1, 36) if x % 2 == 1]
        # 红球偶数：2,4,6,...,34
        even_numbers = [x for x in range(2, 36) if x % 2 == 0]
        
        # 全奇组合
        for red in combinations(odd_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        # 全偶组合
        for red in combinations(even_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        print(f"全奇/全偶组合数: {len(odd_even_combos)}")
        return odd_even_combos
    
    def get_same_zone_combinations(self):
        """获取同区号码组合"""
        print("\n开始生成同区号码组合...")
        
        same_zone_combos = set()
        
        # 第一区：1-11
        for red in combinations(self.zone1, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # 第二区：12-23
        for red in combinations(self.zone2, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # 第三区：24-35
        for red in combinations(self.zone3, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        print(f"同区号码组合数: {len(same_zone_combos)}")
        return same_zone_combos
    
    def export_filtered_combinations(self, output_dir='exports', kill_red=None, kill_blue=None):
        """导出过滤后的可用组合"""
        print("\n" + "="*60)
        print("开始导出大乐透可用号码组合")
        print("="*60)
        
        # 处理杀号参数
        kill_red = kill_red or []
        kill_blue = kill_blue or []
        kill_red_set = set(kill_red)
        kill_blue_set = set(kill_blue)
        
        if kill_red:
            print(f"\n杀红球: {', '.join([f'{n:02d}' for n in sorted(kill_red)])}")
        if kill_blue:
            print(f"杀蓝球: {', '.join([f'{n:02d}' for n in sorted(kill_blue)])}")
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 1. 生成所有组合
        all_combos = self.get_all_combinations()
        total_count = len(all_combos)
        
        # 2-6. 获取各类需排除的组合
        historical = self.get_historical_combinations()
        consecutive = self.get_consecutive_combinations()
        arithmetic = self.get_arithmetic_combinations()
        odd_even = self.get_odd_even_combinations()
        same_zone = self.get_same_zone_combinations()
        
        # 6. 杀号过滤
        kill_combos = set()
        if kill_red_set or kill_blue_set:
            print("\n开始处理杀号过滤...")
            for combo in all_combos:
                red = set(combo[:5])
                blue = set(combo[5:])
                
                # 如果包含被杀红球或被杀蓝球，则排除
                if (kill_red_set and red & kill_red_set) or (kill_blue_set and blue & kill_blue_set):
                    kill_combos.add(combo)
            
            print(f"杀号过滤组合数: {len(kill_combos):,}")
        
        # 合并所有需排除的组合
        print("\n" + "="*60)
        print("开始合并排除条件...")
        excluded = historical | consecutive | arithmetic | odd_even | same_zone | kill_combos
        
        print(f"\n各类排除组合统计:")
        print(f"  1. 历史开奖: {len(historical):,}")
        print(f"  2. 四连号: {len(consecutive):,}")
        print(f"  3. 等差/等比: {len(arithmetic):,}")
        print(f"  4. 全奇/全偶: {len(odd_even):,}")
        print(f"  5. 同区号码: {len(same_zone):,}")
        if kill_combos:
            print(f"  6. 杀号过滤: {len(kill_combos):,}")
        print(f"  合并后排除总数: {len(excluded):,}")
        
        # 7. 导出过滤后的组合
        print("\n开始导出可用组合...")
        filtered_combos = all_combos - excluded
        
        print(f"\n" + "="*60)
        print(f"导出结果统计:")
        print(f"  总组合数: {total_count:,}")
        print(f"  排除组合数: {len(excluded):,}")
        print(f"  可用组合数: {len(filtered_combos):,}")
        print(f"  可用占比: {len(filtered_combos)/total_count*100:.2f}%")
        print("="*60)
        
        # 导出到Excel文件（分批，每个sheet最多100万行）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 将组合列表分批处理
        batch_size = 1000000  # 每批100万
        filtered_list = sorted(list(filtered_combos))
        total_batches = (len(filtered_list) + batch_size - 1) // batch_size
        
        print(f"\n开始导出Excel文件，共分{total_batches}批...")
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(filtered_list))
            batch_data = filtered_list[start_idx:end_idx]
            
            # 构建DataFrame
            data = []
            for combo in batch_data:
                red = combo[:5]
                blue = combo[5:]
                data.append({
                    '红球1': red[0],
                    '红球2': red[1],
                    '红球3': red[2],
                    '红球4': red[3],
                    '红球5': red[4],
                    '蓝球1': blue[0],
                    '蓝球2': blue[1],
                    '组合': f"{red[0]:02d} {red[1]:02d} {red[2]:02d} {red[3]:02d} {red[4]:02d}-{blue[0]:02d} {blue[1]:02d}"
                })
            
            df = pd.DataFrame(data)
            
            # 导出文件
            filename = f'{output_dir}/大乐透可用号码组合_第{batch_idx+1}批共{total_batches}批_{timestamp}.xlsx'
            df.to_excel(filename, index=False, sheet_name=f'批次{batch_idx+1}')
            
            print(f"  已导出批次{batch_idx+1}/{total_batches}：{len(batch_data):,}组 -> {filename}")
        
        # 生成统计报告
        report_data = {
            '项目': [
                '总组合数',
                '历史开奖排除',
                '四连号排除',
                '等差等比排除',
                '全奇全偶排除',
                '同区号码排除',
                '排除组合总计',
                '可用组合数',
                '可用占比'
            ],
            '数量': [
                f"{total_count:,}",
                f"{len(historical):,}",
                f"{len(consecutive):,}",
                f"{len(arithmetic):,}",
                f"{len(odd_even):,}",
                f"{len(same_zone):,}",
                f"{len(excluded):,}",
                f"{len(filtered_combos):,}",
                f"{len(filtered_combos)/total_count*100:.2f}%"
            ]
        }
        
        report_df = pd.DataFrame(report_data)
        report_filename = f'{output_dir}/统计报告_{timestamp}.xlsx'
        report_df.to_excel(report_filename, index=False, sheet_name='统计报告')
        
        print(f"\n统计报告已导出: {report_filename}")
        print("\n" + "="*60)
        print("导出完成!")
        print("="*60)
        
        return len(filtered_combos)


if __name__ == '__main__':
    exporter = DaletouExporter()
    exporter.export_filtered_combinations()
