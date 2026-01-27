# -*- coding: utf-8 -*-
"""
婢堆傜伴柅蹇撳娇閻浣虹矋閸氬牆鐓庡毉閸旂喕?娴犲孩澧嶉張澶婂讲閼崇晫娈戠紒鍕鎮庢稉閹烘帡娅庨悧鐟扮暰濡鈥崇础閿涘苯鐓庡毉閸撯晙缍戠紒鍕鎮
"""
import pandas as pd
from itertools import combinations
import os
from datetime import datetime

class DaletouExporter:
    """婢堆傜伴柅蹇撳娇閻浣虹矋閸氬牆鐓庡毉閸"""
    
    def __init__(self):
        # 婢堆傜伴柅蹇氬嫬鍨閿涙艾澧犻崠35闁?閿涘苯鎮楅崠?2闁?
        self.red_range = range(1, 36)  # 1-35
        self.blue_range = range(1, 13)  # 1-12
        
        # 閸栧搫鐓欓崚鎺戝瀻
        self.zone1 = range(1, 12)   # 1-11
        self.zone2 = range(12, 24)  # 12-23
        self.zone3 = range(24, 36)  # 24-35
        
    def get_all_combinations(self):
        """閻㈢喐鍨氶幍閺堝婂讲閼崇晫娈戞径褌绠伴柅蹇撳娇閻浣虹矋閸氬牞绱欑痪?143娑撳洨绮嶉敍?""
        print("濮濓絽婀閻㈢喐鍨氶幍閺堝婂讲閼崇晫娈戦崣椋庣垳缂佸嫬鎮...")
        
        all_combos = set()
        red_combos = list(combinations(self.red_range, 5))
        blue_combos = list(combinations(self.blue_range, 2))
        
        total = len(red_combos) * len(blue_combos)
        print(f"閸撳秴灏缂佸嫬鎮庨弫? {len(red_combos):,}")
        print(f"閸氬骸灏缂佸嫬鎮庨弫? {len(blue_combos):,}")
        print(f"閹鑽ょ矋閸氬牊鏆: {total:,}")
        
        for red in red_combos:
            for blue in blue_combos:
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                all_combos.add(combo)
        
        return all_combos
    
    def get_historical_combinations(self):
        """閼惧嘲褰囬幍閺堝婂坊閸欐彃绱戞總鏍у娇閻浣虹矋閸?""
        print("\n濮濓絽婀閼惧嘲褰囬崢鍡楀蕉瀵婵傛牕褰块惍?..")
        
        historical_combos = set()
        
        # 娴兼ê鍘涙禒搴㈡拱閸︾増鏋冩禒璺哄炴潪钘夌暚閺佹潙宸婚崣鍙夋殶閹?        local_file = 'daletou_history_full.txt'
        
        if os.path.exists(local_file):
            print(f"閴?閹垫儳鍩岀瑰本鏆ｉ崢鍡楀蕉閺佺増宓侀弬鍥︽㈤敍姝縧ocal_file}")
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    historical_data = f.read()
                    historical_combos = self._parse_historical_data(historical_data)
                    
                    if len(historical_combos) > 0:
                        print(f"閴?娴犲骸鐣閺佹潙宸婚崣鍙夋殶閹归弬鍥︽㈤崝鐘烘祰娴 {len(historical_combos)} 閺堢喎宸婚崣鍙夋殶閹?)
                        
                        # 妤犲矁鐦夐弫鐗堝祦鐎瑰本鏆ｉ幀?                        if len(historical_combos) >= 1500:
                            print(f"閴?閺佺増宓佺瑰本鏆ｉ幀褔鐛欑拠渚姘崇箖閿涘牆鍙{len(historical_combos)}閺堢噦绱")
                        else:
                            print(f"閳跨媴绗  閺佺増宓侀崣閼虫垝绗夌瑰本鏆ｉ敍鍫濈秼閸撳辰len(historical_combos)}閺堢噦绱濋張鐔告箿閼峰啿鐨1500+閺堢噦绱")
                        
                        return historical_combos
            except Exception as e:
                print(f"閴?鐠囪插絿鐎瑰本鏆ｉ崢鍡楀蕉閺佺増宓佹径杈瑙﹂敍姝縠}")
                print("閸ョ偤閸掗佸▏閻銊ュ敶缂冮弫鐗?..")
        else:
            print(f"閳跨媴绗  閺堥幍鎯у煂鐎瑰本鏆ｉ崢鍡楀蕉閺佺増宓侀弬鍥︽㈤敍姝縧ocal_file}")
            print("鐠囩柉绻嶇悰宀嬬窗 python download_history.py 閹存牗澧滈崝銊ょ瑓鏉?)
        
        # 婵″倹鐏夐張閸︾増鏋冩禒鏈电瑝鐎涙ê婀閹存牞璇插絿婢惰精瑙﹂敍灞煎▏閻銊ュ敶缂冮弫鐗?        print("娴ｈ法鏁ら崘鍛鐤嗛惃鍕鍎撮崚鍡樻殶閹归敍鍫滅矌娓氭稒绁寸拠鏇?..")
        
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
        
        print(f"閸樺棗褰跺婵傛牜绮嶉崥鍫熸殶: {len(historical_combos)}")
        return historical_combos
    
    def _parse_historical_data(self, historical_data):
        """鐟欙絾鐎介崢鍡楀蕉閺佺増宓佺涙冿缚瑕嗛敍宀冪箲閸ョ偛褰块惍浣虹矋閸氬牓娉﹂崥"""
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
        """閼惧嘲褰囬幍閺堝婃磽鏉╃偛褰跨紒鍕鎮庨敍鍫濆瘶閸?娑撻幋鏍︿簰娑撳﹨绻涚紒閸欓庣垳閿?""
        print("\n濮濓絽婀閻㈢喐鍨氶崶娑滅箾閸欓庣矋閸?..")
        
        consecutive_combos = set()
        
        # 闁宥呭坊閹甸張澶岀矋閸氬牞绱濆Λ閺屻儱澧犻崠?娑撻崣椋庣垳娑撻弰閸氾箑瀵橀崥4娑撻幋鏍︿簰娑撳﹨绻涚紒閸欓庣垳
        for red in combinations(self.red_range, 5):
            red_sorted = sorted(red)
            
            # 濡閺屻儲妲搁崥锕瀵橀崥?娑撻幋鏍︿簰娑撳﹨绻涚紒閸欓庣垳
            has_four_consecutive = False
            for i in range(len(red_sorted) - 3):  # 濡閺?娑撴潻鐐?                if (red_sorted[i+1] == red_sorted[i] + 1 and 
                    red_sorted[i+2] == red_sorted[i] + 2 and 
                    red_sorted[i+3] == red_sorted[i] + 3):
                    has_four_consecutive = True
                    break
            
            if has_four_consecutive:
                # 闁板秴瑙勫嶉張澶婃倵閸栬櫣绮嶉崥?                for blue in combinations(self.blue_range, 2):
                    combo = tuple(red_sorted) + tuple(sorted(blue))
                    consecutive_combos.add(combo)
        
        print(f"閸ユ稖绻涢崣椋庣矋閸氬牊鏆: {len(consecutive_combos):,}")
        return consecutive_combos
    
    def get_arithmetic_combinations(self):
        """閼惧嘲褰囬幍閺堝岀搼瀹?缁涘嬬槷閺佹澘鍨缂佸嫬鎮"""
        print("\n濮濓絽婀閻㈢喐鍨氱粵澶婃▕/缁涘嬬槷閺佹澘鍨缂佸嫬鎮...")
        
        arithmetic_combos = set()
        
        # 缁涘婃▕閺佹澘鍨閿涙艾鍙曞告禒1閸?
        for diff in range(1, 7):
            for start in range(1, 36):
                seq = [start + i * diff for i in range(5)]
                if all(1 <= x <= 35 for x in seq):
                    red = tuple(sorted(seq))
                    # 闁板秴瑙勫嶉張澶婃倵閸栬櫣绮嶉崥?                    for blue in combinations(self.blue_range, 2):
                        combo = red + tuple(sorted(blue))
                        arithmetic_combos.add(combo)
        
        # 缁涘嬬槷閺佹澘鍨閿涙艾鍙曞В鏂捐礋2閿?,2,4,8,16 閹?2,4,8,16,32缁涘涚礆
        for start in range(1, 18):
            seq = [start * (2 ** i) for i in range(5)]
            if all(1 <= x <= 35 for x in seq):
                red = tuple(sorted(seq))
                for blue in combinations(self.blue_range, 2):
                    combo = red + tuple(sorted(blue))
                    arithmetic_combos.add(combo)
        
        print(f"缁涘婃▕/缁涘嬬槷閺佹澘鍨缂佸嫬鎮庨弫? {len(arithmetic_combos)}")
        return arithmetic_combos
    
    def get_odd_even_combinations(self):
        """閼惧嘲褰囬崗銊ュ洦鏆熼幋鏍у弿閸嬭埖鏆熺紒鍕?""
        print("\n濮濓絽婀閻㈢喐鍨氶崗銊/閸忋劌浼撶紒鍕鎮...")
        
        odd_even_combos = set()
        
        # 閸撳秴灏婵傚洦鏆熼敍?,3,5,...,35
        odd_numbers = [x for x in range(1, 36) if x % 2 == 1]
        # 閸撳秴灏閸嬭埖鏆熼敍?,4,6,...,34
        even_numbers = [x for x in range(2, 36) if x % 2 == 0]
        
        # 閸忋劌鍥ㄦ殶缂佸嫬?        for red in combinations(odd_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        # 閸忋劌浼撻弫鎵绮嶉崥?        for red in combinations(even_numbers, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                odd_even_combos.add(combo)
        
        print(f"閸忋劌/閸忋劌浼撶紒鍕鎮庨弫? {len(odd_even_combos)}")
        return odd_even_combos
    
    def get_same_zone_combinations(self):
        """閼惧嘲褰囬崥灞肩撮崠鍝勭厵閻ㄥ嫬褰块惍浣虹矋閸?""
        print("\n濮濓絽婀閻㈢喐鍨氶崥灞藉隘缂佸嫬鎮...")
        
        same_zone_combos = set()
        
        # 缁?閸栫尨绱1-11閿?        for red in combinations(self.zone1, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # 缁?閸栫尨绱12-23閿?        for red in combinations(self.zone2, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        # 缁?閸栫尨绱24-35閿?        for red in combinations(self.zone3, 5):
            for blue in combinations(self.blue_range, 2):
                combo = tuple(sorted(red)) + tuple(sorted(blue))
                same_zone_combos.add(combo)
        
        print(f"閸氬苯灏缂佸嫬鎮庨弫? {len(same_zone_combos)}")
        return same_zone_combos
    
閹?   def export_filtered_combinations(self, output_dir='exports', kill_red=None, kill_blue=None):
        """鐎电厧鍤鏉╁洦鎶ら崥搴ｆ畱閸欓庣垳缂佸嫬鎮"""
        print("\n" + "="*60)
        print("瀵婵瀣鏁撻幋鎰鎷版潻鍥ㄦ姢婢堆傜伴柅蹇撳娇閻浣虹矋閸?)
        print("="*60)
        
        # 婢跺嫮鎮婇弶閸欏嘲寮閺?        kill_red = kill_red or []
        kill_blue = kill_blue or []
        kill_red_set = set(kill_red)
        kill_blue_set = set(kill_blue)
        
        if kill_red:
            print(f"
閺夌痪銏㈡倖鐠佸墽鐤: {', '.join([f'{n:02d}' for n in sorted(kill_red)])}")
        if kill_blue:
            print(f"閺夐拑婵堟倖鐠佸墽鐤: {', '.join([f'{n:02d}' for n in sorted(kill_blue)])}")
        
        # 閸掓稑缂撶电厧鍤閻╄ぐ
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 1. 閻㈢喐鍨氶幍閺堝岀矋閸?        all_combos = self.get_all_combinations()
        total_count = len(all_combos)
        
        # 2-6. 閼惧嘲褰囬棁鐟曚焦甯撻梽銈囨畱缂佸嫬鎮
        historical = self.get_historical_combinations()
        consecutive = self.get_consecutive_combinations()
        arithmetic = self.get_arithmetic_combinations()
        odd_even = self.get_odd_even_combinations()
        same_zone = self.get_same_zone_combinations()
        
        # 6. 閺夐崣鐤绻冨娿倧绱伴幒鎺楁珟閸栧懎鎯堥幐鍥х暰閸欓庣垳閻ㄥ嫮绮嶉崥?        kill_combos = set()
        if kill_red_set or kill_blue_set:
            print("
濮濓絽婀鏉╁洦鎶ら弶閸欓庣矋閸?..")
            for combo in all_combos:
                red = set(combo[:5])
                blue = set(combo[5:])
                
                # 婵″倹鐏夌痪銏㈡倖閸栧搫瀵橀崥娴犵粯鍓版稉娑撻弶閸欏嚖绱濋幋鏍鎽戦悶鍐ㄥ隘閸栧懎鎯堟禒缁樺壈娑撴稉閺夐崣鍑ょ礉鐏忚鲸甯撻梽?                if (kill_red_set and red & kill_red_set) or (kill_blue_set and blue & kill_blue_set):
                    kill_combos.add(combo)
            
            print(f"閺夐崣鐤绻冨娿倗绮嶉崥鍫熸殶: {len(kill_combos):,}")
        
        # 閸氬牆鑻熼幍閺堝庝焦甯撻梽銈囨畱缂佸嫬?        print("\n" + "="*60)
        print("濮濓絽婀閸氬牆鑻熼幒鎺楁珟閺夆叉...")
        excluded = historical | consecutive | arithmetic | odd_even | same_zone | kill_combos
        
        print(f"\n閹烘帡娅庨弶鈥叉㈢紒鐔:")
        print(f"  1. 閸樺棗褰跺婵? {len(historical):,}")
        print(f"  2. 閸ユ稖绻涢崣? {len(consecutive):,}")
        print(f"  3. 缁涘婃▕/缁涘嬬槷: {len(arithmetic):,}")
        print(f"  4. 閸忋劌/閸忋劌浼: {len(odd_even):,}")
        print(f"  5. 閸氬苯灏閸欓庣垳: {len(same_zone):,}")
        if kill_combos:
            print(f"  6. 閺夐崣鐤绻冨? {len(kill_combos):,}")
        print(f"  閸氬牆鑻熼崥搴㈢粯甯撻梽銈嗘殶: {len(excluded):,}")
        
        # 7. 鏉╁洦鎶ゅ版鍩岄張缂佸牏绮嶉崥?        print("\n濮濓絽婀鏉╁洦鎶ょ紒鍕鎮...")
        filtered_combos = all_combos - excluded
        
        print(f"\n" + "="*60)
        print(f"鏉╁洦鎶ょ紒鎾寸亯:")
        print(f"  閹鑽ょ矋閸氬牊鏆: {total_count:,}")
        print(f"  閹烘帡娅庨弫浼村櫤: {len(excluded):,}")
        print(f"  閸撯晙缍戦弫浼村櫤: {len(filtered_combos):,}")
        print(f"  閸撯晙缍戝В鏂剧伐: {len(filtered_combos)/total_count*100:.2f}%")
        print("="*60)
        
        # 鐎电厧鍤娑撶瘝xcel閺傚洣娆㈤敍鍫濆瀻婢舵矮閲渟heet閿?        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 閻㈠彉绨缂佸嫬鎮庨弫浼村櫤瀹搞劌銇囬敍灞藉瀻閹电懓鐓?        batch_size = 1000000  # 濮ｅ繋閲滈弬鍥︽100娑撳洩
        filtered_list = sorted(list(filtered_combos))
        total_batches = (len(filtered_list) + batch_size - 1) // batch_size
        
        print(f"\n濮濓絽婀鐎电厧鍤閸掔檴xcel閺傚洣娆㈤敍鍫濆彙{total_batches}娑撻弬鍥︽㈤敍...")
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(filtered_list))
            batch_data = filtered_list[start_idx:end_idx]
            
            # 鏉為幑娑撶瘚ataFrame
            data = []
            for combo in batch_data:
                red = combo[:5]
                blue = combo[5:]
                data.append({
                    '閸撳秴灏1': red[0],
                    '閸撳秴灏2': red[1],
                    '閸撳秴灏3': red[2],
                    '閸撳秴灏4': red[3],
                    '閸撳秴灏5': red[4],
                    '閸氬骸灏1': blue[0],
                    '閸氬骸灏2': blue[1],
                    '缂佸嫬鎮': f"{red[0]:02d} {red[1]:02d} {red[2]:02d} {red[3]:02d} {red[4]:02d}-{blue[0]:02d} {blue[1]:02d}"
                })
            
            df = pd.DataFrame(data)
            
            # 鐎电厧鍤閺傚洣娆
            filename = f'{output_dir}/婢堆傜伴柅蹇氱箖濠娿倗绮嶉崥鍧冪粭鐟奲atch_idx+1}閹电ラ崗鐪total_batches}閹电{timestamp}.xlsx'
            df.to_excel(filename, index=False, sheet_name=f'缁楃憡batch_idx+1}閹?)
            
            print(f"  瀹告彃鐓庡毉缁楃憡batch_idx+1}/{total_batches}閹? {len(batch_data):,}缂?-> {filename}")
        
        # 閻㈢喐鍨氱紒鐔烩剝濮ら崨
        report_data = {
            '缂佺喕锟?: [
                '閹鑽ょ矋閸氬牊鏆',
                '閸樺棗褰跺婵傛牗甯撻梽?,
                '閸ユ稖绻涢崣閿嬪笓闂?,
                '缁涘婃▕缁涘嬬槷閹烘帡娅',
                '閸忋劌鍥у弿閸嬭埖甯撻梽',
                '閸氬苯灏閹烘帡娅',
                '閹缁樺笓闂勩倖鏆',
                '閸撯晙缍戠紒鍕鎮庨弫?,
                '閸撯晙缍戝В鏂剧伐'
            ],
            '閺佷即鍣': [
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
        report_filename = f'{output_dir}/缂佺喕鈩冨Г閸涘ク{timestamp}.xlsx'
        report_df.to_excel(report_filename, index=False, sheet_name='缂佺喕鈩冨Г閸')
        
        print(f"\n缂佺喕鈩冨Г閸涘﹤鍑＄电厧? {report_filename}")
        print("\n" + "="*60)
        print("鐎电厧鍤鐎瑰本鍨氶敍?)
        print("="*60)
        
        return len(filtered_combos)


if __name__ == '__main__':
    exporter = DaletouExporter()
    exporter.export_filtered_combinations()
