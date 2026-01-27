# -*- coding: utf-8 -*-
"""
Daletou Export Module
"""
import pandas as pd
from itertools import combinations
import os
from datetime import datetime

class DaletouExporter:
    """Daletou Exporter"""
    
    def __init__(self):
        # Daletou rules: front 35 choose 5, back 12 choose 2
        self.red_range = range(1, 36)  # 1-35
        self.blue_range = range(1, 13)  # 1-12
        
        # Zone division
        self.zone1 = range(1, 12)   # 1-11
        self.zone2 = range(12, 24)  # 12-23
        self.zone3 = range(24, 36)  # 24-35
        
        # Cache for historical data
        self._historical_combos = None
        
    def get_all_combinations(self, cancel_check=None):
        """Generate all possible combinations"""
        print("正在生成所有可能的号码组合...")
        
        all_combos = set()
        red_combos = list(combinations(self.red_range, 5))
        blue_combos = list(combinations(self.blue_range, 2))
        
        total = len(red_combos) * len(blue_combos)
        print(f"前区组合数: {len(red_combos):,}")
        print(f"后区组合数: {len(blue_combos):,}")
        print(f"总组合数: {total:,}")
        
        for i, red in enumerate(red_combos):
            if cancel_check and i % 5000 == 0:
                if cancel_check():
                    return None
            for blue in blue_combos:
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                all_combos.add(combo)
        
        return all_combos
    
    def get_historical_combinations(self):
        """Get historical winning combinations (with caching)"""
        if self._historical_combos is not None:
            return self._historical_combos
            
        print("\n正在获取历史开奖号码...")
        
        historical_combos = set()
        
        # Load from local file first
        local_file = 'daletou_history_full.txt'
        
        if os.path.exists(local_file):
            print(f"✓ 找到完整历史数据文件：{local_file}")
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    historical_data = f.read()
                    historical_combos = self._parse_historical_data(historical_data)
                    
                    if len(historical_combos) > 0:
                        print(f"✓ 从完整历史数据文件加载了 {len(historical_combos)} 期历史数据")
                        
                        # Verify data integrity
                        if len(historical_combos) >= 1500:
                            print(f"✓ 数据完整性验证通过（共{len(historical_combos)}期）")
                        else:
                            print(f"⚠️  数据可能不完整（当前{len(historical_combos)}期，期望至少1500+期）")
                        
                        return historical_combos
            except Exception as e:
                print(f"❌ 读取完整历史数据失败：{e}")
                print("回退到使用内置数据...")
        else:
            print(f"⚠️  未找到完整历史数据文件：{local_file}")
            print("请运行： python download_history.py 或手动下载")
        
        # Fallback to built-in data
        print("使用内置的部分数据（仅供测试）...")
        
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
25139	2025-12-06	08 18 22 30 35-01 04"""
        
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
        
        print(f"历史开奖组合数: {len(historical_combos)}")
        return historical_combos
    
    def _parse_historical_data(self, historical_data):
        """Parse historical data"""
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
        """Get four-consecutive combinations (4+ consecutive numbers)"""
        print("\n正在生成四连号组合...")
        
        consecutive_combos = set()
        
        # Check all combinations for 4 or more consecutive numbers in front area
        for red in combinations(self.red_range, 5):
            red_sorted = sorted(red)
            
            # Check if contains 4 or more consecutive numbers
            has_four_consecutive = False
            for i in range(len(red_sorted) - 3):  # Check 4 consecutive
                if (red_sorted[i+1] == red_sorted[i] + 1 and 
                    red_sorted[i+2] == red_sorted[i] + 2 and 
                    red_sorted[i+3] == red_sorted[i] + 3):
                    has_four_consecutive = True
                    break
            
            if has_four_consecutive:
                # Pair with all back combinations
                for blue in combinations(self.blue_range, 2):
                    combo = tuple(red_sorted) + tuple(sorted(blue))
                    consecutive_combos.add(combo)
        
        print(f"四连号组合数: {len(consecutive_combos):,}")
        return consecutive_combos
    
    def get_arithmetic_combinations(self):
        """Get arithmetic/geometric combinations"""
        print("\n正在生成等差/等比数列组合...")
        
        arithmetic_combos = set()
        
        # Arithmetic sequence: common difference from 1 to 6
        for diff in range(1, 7):
            for start in range(1, 36):
                seq = [start + i * diff for i in range(5)]
                if all(1 <= x <= 35 for x in seq):
                    red = tuple(sorted(seq))
                    # Pair with all back combinations
                    for blue in combinations(self.blue_range, 2):
                        combo = red + tuple(sorted(blue))
                        arithmetic_combos.add(combo)
        
        # Geometric sequence: common ratio of 2
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
        """Get all-odd or all-even combinations"""
        print("\n正在生成全奇/全偶组合...")
        
        odd_even_combos = set()
        
        # Front odd numbers: 1,3,5,...,35
        odd_numbers = [x for x in range(1, 36) if x % 2 == 1]
        # Front even numbers: 2,4,6,...,34
        even_numbers = [x for x in range(2, 36) if x % 2 == 0]
        
        # All odd combinations
        for red in combinations(odd_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        # All even combinations
        for red in combinations(even_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        print(f"全奇/全偶组合数: {len(odd_even_combos)}")
        return odd_even_combos
    
    def get_same_zone_combinations(self):
        """Get same-zone combinations"""
        print("\n正在生成同区组合...")
        
        same_zone_combos = set()
        
        # Zone 1 (1-11)
        for red in combinations(self.zone1, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # Zone 2 (12-23)
        for red in combinations(self.zone2, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # Zone 3 (24-35)
        for red in combinations(self.zone3, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        print(f"同区组合数: {len(same_zone_combos)}")
        return same_zone_combos

    def is_arithmetic_sequence(self, red_sorted):
        """Check if it's an arithmetic sequence with diff 1-6"""
        if len(red_sorted) < 5: return False
        diff = red_sorted[1] - red_sorted[0]
        if diff < 1 or diff > 6:
            return False
        for i in range(1, 4):
            if red_sorted[i+1] - red_sorted[i] != diff:
                return False
        return True
        
    def is_geometric_sequence(self, red_sorted):
        """Check if it's a geometric sequence with ratio 2"""
        if len(red_sorted) < 5 or red_sorted[0] == 0: return False
        if red_sorted[1] / red_sorted[0] != 2:
            return False
        for i in range(1, 4):
            if red_sorted[i+1] / red_sorted[i] != 2:
                return False
        return True

    def is_valid_combination(self, combo, kill_red_set=None, kill_blue_set=None, sum_range=None, odd_even_ratio=None):
        """
        Check if a single combination is valid according to all rules.
        combo is a tuple (r1, r2, r3, r4, r5, b1, b2)
        """
        red = combo[:5]
        blue = combo[5:]
        red_sorted = sorted(red)
        
        # 1. Historical
        if combo in self.get_historical_combinations():
            return False
            
        # 2. Four-consecutive
        for i in range(len(red_sorted) - 3):
            if (red_sorted[i+1] == red_sorted[i] + 1 and 
                red_sorted[i+2] == red_sorted[i] + 2 and 
                red_sorted[i+3] == red_sorted[i] + 3):
                return False
                
        # 3. Arithmetic/Geometric
        if self.is_arithmetic_sequence(red_sorted) or self.is_geometric_sequence(red_sorted):
            return False
            
        # 4. All odd/even
        odd_count = sum(1 for n in red if n % 2 == 1)
        if odd_count == 0 or odd_count == 5:
            return False
            
        # 5. Same zone
        zone1_count = sum(1 for n in red if n in self.zone1)
        zone2_count = sum(1 for n in red if n in self.zone2)
        zone3_count = sum(1 for n in red if n in self.zone3)
        if zone1_count == 5 or zone2_count == 5 or zone3_count == 5:
            return False
            
        # 6. Kill numbers
        if kill_red_set and any(n in kill_red_set for n in red):
            return False
        if kill_blue_set and any(n in kill_blue_set for n in blue):
            return False
            
        # 7. Sum range
        if sum_range:
            red_sum = sum(red)
            if red_sum < sum_range[0] or red_sum > sum_range[1]:
                return False
                
        # 8. Odd-even ratio
        if odd_even_ratio:
            ratio_str = f"{odd_count}:{5-odd_count}"
            if ratio_str != odd_even_ratio:
                return False
                
        return True
    
    def get_filtered_combinations(self, kill_red=None, kill_blue=None, sum_range=None, odd_even_ratio=None, cancel_check=None):
        """Get filtered combinations based on all criteria"""
        # Handle parameters
        kill_red = kill_red or []
        kill_blue = kill_blue or []
        kill_red_set = set(kill_red)
        kill_blue_set = set(kill_blue)
        
        # 1. Generate all combinations
        all_combos = self.get_all_combinations(cancel_check=cancel_check)
        if all_combos is None: return None
        
        # 2-6. Get combinations to exclude
        historical = self.get_historical_combinations()
        consecutive = self.get_consecutive_combinations()
        arithmetic = self.get_arithmetic_combinations()
        odd_even = self.get_odd_even_combinations()
        same_zone = self.get_same_zone_combinations()
        
        # 7. Kill number filter
        kill_combos = set()
        if kill_red_set or kill_blue_set:
            for i, combo in enumerate(all_combos):
                if cancel_check and i % 100000 == 0:
                    if cancel_check(): return None
                red = set(combo[:5])
                blue = set(combo[5:])
                if (kill_red_set and red & kill_red_set) or (kill_blue_set and blue & kill_blue_set):
                    kill_combos.add(combo)
        
        # 8. Sum range filter
        sum_combos = set()
        if sum_range and len(sum_range) == 2:
            min_sum, max_sum = sum_range
            for i, combo in enumerate(all_combos):
                if cancel_check and i % 100000 == 0:
                    if cancel_check(): return None
                red_sum = sum(combo[:5])
                if red_sum < min_sum or red_sum > max_sum:
                    sum_combos.add(combo)
        
        # 9. Odd-even ratio filter
        ratio_combos = set()
        if odd_even_ratio:
            for i, combo in enumerate(all_combos):
                if cancel_check and i % 100000 == 0:
                    if cancel_check(): return None
                red_numbers = combo[:5]
                odd_count = sum(1 for n in red_numbers if n % 2 == 1)
                even_count = 5 - odd_count
                ratio_str = f"{odd_count}:{even_count}"
                if ratio_str != odd_even_ratio:
                    ratio_combos.add(combo)
        
        # Merge all exclusions
        excluded = historical | consecutive | arithmetic | odd_even | same_zone | kill_combos | sum_combos | ratio_combos
        
        # Filter to get final combinations
        filtered_combos = all_combos - excluded
        
        return {
            'all_combos': all_combos,
            'filtered_combos': filtered_combos,
            'excluded': excluded,
            'stats': {
                'historical': len(historical),
                'consecutive': len(consecutive),
                'arithmetic': len(arithmetic),
                'odd_even': len(odd_even),
                'same_zone': len(same_zone),
                'kill_combos': len(kill_combos),
                'sum_combos': len(sum_combos),
                'ratio_combos': len(ratio_combos)
            }
        }
    
    def export_filtered_combinations(self, output_dir='exports', kill_red=None, kill_blue=None, sum_range=None, odd_even_ratio=None, cancel_check=None):
        """Export filtered combinations"""
        print("\n" + "="*60)
        print("开始生成和过滤大乐透号码组合")
        print("="*60)
        
        # Handle kill number parameters
        kill_red = kill_red or []
        kill_blue = kill_blue or []
        
        if kill_red:
            print(f"\n杀红球设置: {', '.join([f'{n:02d}' for n in sorted(kill_red)])}")
        if kill_blue:
            print(f"杀蓝球设置: {', '.join([f'{n:02d}' for n in sorted(kill_blue)])}")
        if sum_range and len(sum_range) == 2:
            print(f"和值范围设置: {sum_range[0]} - {sum_range[1]}")
        if odd_even_ratio:
            print(f"奇偶比设置: {odd_even_ratio}")
        
        # Create export directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get filtered combinations
        result = self.get_filtered_combinations(kill_red, kill_blue, sum_range, odd_even_ratio, cancel_check=cancel_check)
        if result is None: return None
        
        all_combos = result['all_combos']
        filtered_combos = result['filtered_combos']
        excluded = result['excluded']
        stats = result['stats']
        total_count = len(all_combos)
        
        # Print statistics
        print("\n" + "="*60)
        print("正在合并排除条件...")
        print(f"\n排除条件统计:")
        print(f"  1. 历史开奖: {stats['historical']:,}")
        print(f"  2. 四连号: {stats['consecutive']:,}")
        print(f"  3. 等差/等比: {stats['arithmetic']:,}")
        print(f"  4. 全奇/全偶: {stats['odd_even']:,}")
        print(f"  5. 同区号码: {stats['same_zone']:,}")
        if stats['kill_combos']:
            print(f"  6. 杀号过滤: {stats['kill_combos']:,}")
        if stats['sum_combos']:
            print(f"  7. 和值过滤: {stats['sum_combos']:,}")
        if stats['ratio_combos']:
            print(f"  8. 奇偶比过滤: {stats['ratio_combos']:,}")
        print(f"  合并后总排除数: {len(excluded):,}")
        
        print(f"\n" + "="*60)
        print(f"过滤结果:")
        print(f"  总组合数: {total_count:,}")
        print(f"  排除数量: {len(excluded):,}")
        print(f"  剩余数量: {len(filtered_combos):,}")
        print(f"  剩余比例: {len(filtered_combos)/total_count*100:.2f}%")
        print("="*60)
        
        # Export to Excel files (split into batches)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Due to huge number of combinations, export in batches
        batch_size = 1000000  # 1 million per file
        filtered_list = sorted(list(filtered_combos))
        total_batches = (len(filtered_list) + batch_size - 1) // batch_size
        
        print(f"\n正在导出到Excel文件（共{total_batches}个文件）...")
        
        export_files = []
        for batch_idx in range(total_batches):
            if cancel_check and cancel_check(): return None
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(filtered_list))
            batch_data = filtered_list[start_idx:end_idx]
            
            # Convert to DataFrame
            data = []
            for combo in batch_data:
                red = combo[:5]
                blue = combo[5:]
                data.append({
                    '前区1': red[0],
                    '前区2': red[1],
                    '前区3': red[2],
                    '前区4': red[3],
                    '前区5': red[4],
                    '后区1': blue[0],
                    '后区2': blue[1],
                    '组合': f"{red[0]:02d} {red[1]:02d} {red[2]:02d} {red[3]:02d} {red[4]:02d}-{blue[0]:02d} {blue[1]:02d}"
                })
            
            df = pd.DataFrame(data)
            
            # File name
            filename = f"daletou_filtered_{timestamp}_part{batch_idx+1}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            # Export to Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            export_files.append(filepath)
            
            print(f"  第{batch_idx+1}/{total_batches}个文件导出完成: {filename} ({len(batch_data):,}组)")
        
        # Generate summary report
        summary = {
            '导出时间': timestamp,
            '总组合数': total_count,
            '排除规则': {
                '历史开奖': stats['historical'],
                '四连号排除': stats['consecutive'],
                '等差等比数列': stats['arithmetic'],
                '全奇全偶': stats['odd_even'],
                '同区号码': stats['same_zone'],
            },
            '杀号过滤': {
                '杀红球': list(kill_red) if kill_red else [],
                '杀蓝球': list(kill_blue) if kill_blue else [],
                '过滤组合数': stats['kill_combos'],
            },
            '和值过滤': {
                '和值范围': sum_range if sum_range else None,
                '过滤组合数': stats['sum_combos'],
            },
            '奇偶比过滤': {
                '奇偶比': odd_even_ratio if odd_even_ratio else None,
                '过滤组合数': stats['ratio_combos'],
            },
            '总排除数': len(excluded),
            '剩余组合数': len(filtered_combos),
            '剩余比例': f"{len(filtered_combos)/total_count*100:.2f}%",
            '导出文件': export_files
        }
        
        # Save summary report
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("大乐透号码组合导出报告\n")
            f.write("="*60 + "\n\n")
            f.write(f"导出时间: {summary['导出时间']}\n\n")
            f.write(f"总组合数: {summary['总组合数']:,}\n\n")
            f.write("排除规则统计:\n")
            for rule, count in summary['排除规则'].items():
                f.write(f"  - {rule}: {count:,}\n")
            if kill_red or kill_blue:
                f.write(f"\n杀号设置:\n")
                if kill_red:
                    f.write(f"  - 杀红球: {', '.join([f'{n:02d}' for n in sorted(kill_red)])}\n")
                if kill_blue:
                    f.write(f"  - 杀蓝球: {', '.join([f'{n:02d}' for n in sorted(kill_blue)])}\n")
                f.write(f"  - 杀号过滤组合数: {summary['杀号过滤']['过滤组合数']:,}\n")
            f.write(f"\n总排除数: {summary['总排除数']:,}\n")
            f.write(f"剩余组合数: {summary['剩余组合数']:,}\n")
            f.write(f"剩余比例: {summary['剩余比例']}\n\n")
            f.write("导出文件列表:\n")
            for i, file in enumerate(summary['导出文件'], 1):
                f.write(f"  {i}. {os.path.basename(file)}\n")
        
        print(f"\n✓ 导出完成!")
        print(f"  导出目录: {os.path.abspath(output_dir)}")
        print(f"  导出文件数: {len(export_files)}")
        print(f"  汇总报告: {summary_file}")
        
        return summary

if __name__ == '__main__':
    exporter = DaletouExporter()
    exporter.export_filtered_combinations()
