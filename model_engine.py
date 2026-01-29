import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime
import re
import os
import joblib
import requests
from bs4 import BeautifulSoup
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# 原生 Numpy LSTM 实现（替代 TensorFlow/PyTorch 解决兼容性问题）
class NumpyLSTM:
    def __init__(self, input_size=12, hidden_size=64, output_size=12):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # 门控权重初始化 (Xavier 初始化)
        limit = np.sqrt(6 / (input_size + hidden_size))
        # 组合权重 [Wf, Wi, Wc, Wo]
        self.W = np.random.uniform(-limit, limit, (4, hidden_size, input_size + hidden_size))
        self.b = np.zeros((4, hidden_size))
        
        # 输出层权重
        self.Wy = np.random.uniform(-limit, limit, (output_size, hidden_size))
        self.by = np.zeros(output_size)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def train(self, X, y, epochs=100, lr=0.01):
        """简单的 BPTT 训练逻辑"""
        for _ in range(epochs):
            for i in range(len(X)):
                self._step(X[i], y[i], lr)

    def _step(self, x_seq, y_true, lr):
        # 简化的参数更新逻辑（用于蓝球预测已足够）
        # 实际预测时我们会使用更稳定的预设权重或基础训练
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)
        
        # 前向传播
        for x in x_seq:
            concat = np.concatenate((x, h))
            f = self.sigmoid(np.dot(self.W[0], concat) + self.b[0])
            i = self.sigmoid(np.dot(self.W[1], concat) + self.b[1])
            c_hat = np.tanh(np.dot(self.W[2], concat) + self.b[2])
            o = self.sigmoid(np.dot(self.W[3], concat) + self.b[3])
            c = f * c + i * c_hat
            h = o * np.tanh(c)
            
        y_pred = self.sigmoid(np.dot(self.Wy, h) + self.by)
        
        # 简化的梯度下降
        dy = y_pred - y_true
        dWy = np.outer(dy, h)
        self.Wy -= lr * dWy
        self.by -= lr * dy

    def predict(self, x_seq):
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)
        for x in x_seq:
            concat = np.concatenate((x, h))
            f = self.sigmoid(np.dot(self.W[0], concat) + self.b[0])
            i = self.sigmoid(np.dot(self.W[1], concat) + self.b[1])
            c_hat = np.tanh(np.dot(self.W[2], concat) + self.b[2])
            o = self.sigmoid(np.dot(self.W[3], concat) + self.b[3])
            c = f * c + i * c_hat
            h = o * np.tanh(c)
        return self.sigmoid(np.dot(self.Wy, h) + self.by)

# 集成学习模型
try:
    import xgboost as xgb
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    print("⚠️ 集成学习库未安装，将使用基础算法")

class DaletouPredictor:
    """大乐透预测引擎 - 增强版，包含更多算法"""
    
    def __init__(self, history_path='daletou_history_full.txt'):
        self.history_path = history_path
        self.history_df = self._load_history()
        self.is_trained = False
        self.feature_weights = {}
        self.recent_errors = []
        self.markov_transitions = {}
        self.pattern_memory = []
        self.dynamic_weights = {}
        self.ensemble_models = {'red': {}, 'blue': {}}
        self.stacking_meta_model = {}
        self.blue_stacking_meta_model = {}
        self.blue_lstm_model = None
        self.actual_numbers_pool = []
        self.co_occurrence_graph = {}
        
        # 资产存储路径
        self.assets_dir = 'model_assets'
        if not os.path.exists(self.assets_dir): os.makedirs(self.assets_dir)
        
        # 评分系统动态权重 (V4 进化版)
        self.scoring_weights = {
            'sum_weight': 1.0, 'span_weight': 1.0, 'odd_even_weight': 1.0,
            'hot_cold_weight': 1.0, 'similar_weight': 1.0, 'm012_weight': 1.2
        }
        self.adaptive_weights = {'frequency': 1.0, 'missing': 1.0, 'pattern': 1.0, 'actual_weight': 1.0}
        
        # 尝试恢复持久化资产
        self.load_state()

    def _load_history(self):
        if not os.path.exists(self.history_path): return pd.DataFrame()
        with open(self.history_path, 'r', encoding='utf-8') as f:
            return self.parse_historical_data(f.read())

    def save_state(self, tag='latest'):
        """保存当前模型状态与权重"""
        import joblib
        state = {
            'stacking_red': self.stacking_meta_model,
            'stacking_blue': self.blue_stacking_meta_model,
            'blue_lstm': self.blue_lstm_model,
            'scoring_weights': self.scoring_weights,
            'adaptive_weights': self.adaptive_weights,
            'markov': self.markov_transitions,
            'last_trained_period': int(self.history_df.iloc[-1]['period']) if len(self.history_df)>0 else 0
        }
        path = os.path.join(self.assets_dir, f'model_state_{tag}.pkl')
        joblib.dump(state, path)
        # print(f"[*] 模型资产已持久化至: {path}")

    def load_state(self, tag='latest'):
        """从磁盘恢复模型状态"""
        import joblib
        path = os.path.join(self.assets_dir, f'model_state_{tag}.pkl')
        if os.path.exists(path):
            try:
                state = joblib.load(path)
                self.stacking_meta_model = state.get('stacking_red', {})
                self.blue_stacking_meta_model = state.get('stacking_blue', {})
                self.blue_lstm_model = state.get('blue_lstm')
                self.scoring_weights = state.get('scoring_weights', self.scoring_weights)
                self.adaptive_weights = state.get('adaptive_weights', self.adaptive_weights)
                self.markov_transitions = state.get('markov', {})
                self.is_trained = True
                # print(f"[*] 成功从磁盘恢复模型资产 ({tag})")
                return True
            except: pass
        return False
        
    def _fetch_reference_numbers(self, urls):
        """从参考网页中智能提取推荐号码 - V3 增强版（支持动态渲染）"""
        if not urls: return {'red': Counter(), 'blue': Counter()}
        
        red_counts = Counter()
        blue_counter = Counter()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.toutiao.com/'
        }
        
        # 关键词定义
        positive_keywords = ['推荐', '看好', '重点', '关注', '必选', '首选', '胆码', '精选', '主推', '稳胆', '热门', '杀号']
        negative_keywords = ['避开', '不看好', '排除', '冷门', '弃选', '舍弃']
        
        for url in urls:
            try:
                print(f"[*] 正在智能分析参考网页: {url}", flush=True)
                
                # 尝试多种方式获取内容
                resp = None
                try:
                    # 方法1：直接请求
                    resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                    if resp.status_code == 200 and len(resp.text) > 500:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                    else:
                        raise Exception(f"网页返回空白或异常: {resp.status_code}")
                except Exception as e1:
                    print(f"[WARN] 直接请求失败: {e1}", flush=True)
                    # 方案2：尝试移动版链接
                    if 'toutiao.com' in url and '/w/' in url:
                        # 提取文章ID
                        import re
                        match = re.search(r'/w/(\d+)', url)
                        if match:
                            article_id = match.group(1)
                            mobile_url = f"https://m.toutiao.com/i{article_id}/"
                            print(f"[*] 尝试移动版: {mobile_url}", flush=True)
                            resp = requests.get(mobile_url, headers=headers, timeout=15)
                            soup = BeautifulSoup(resp.text, 'html.parser')
                        else:
                            raise Exception("无法解析文章ID")
                    else:
                        raise Exception("不支持的网站类型")
                
                if not resp or resp.status_code != 200:
                    print(f"[ERROR] 网页访问失败: {resp.status_code if resp else 'No response'}", flush=True)
                    continue
                
                # 提取文本内容
                text_content = soup.get_text()
                print(f"[DEBUG] 获取文本长度: {len(text_content)} 字符", flush=True)
                
                if len(text_content) < 100:
                    print(f"[ERROR] 网页内容过少，可能是JS动态渲染页面，请直接提供号码或使用普通网页", flush=True)
                    continue
                
                # 1. 提取结构化数据
                structured_numbers = self._extract_structured_numbers(soup)
                for n in structured_numbers['red']:
                    red_counts[n] += 3
                for n in structured_numbers['blue']:
                    blue_counter[n] += 3
                
                # 2. 段落级语义分析
                paragraphs = soup.find_all(['p', 'div', 'span', 'li', 'article'])
                for para in paragraphs:
                    text = para.get_text()
                    if not text.strip() or len(text) < 5: continue
                    
                    # 跳过明确的负向内容
                    if any(neg in text for neg in negative_keywords):
                        continue
                    
                    # 检查是否包含正向关键词
                    has_positive = any(pos in text for pos in positive_keywords)
                    
                    # 提取数字
                    numbers = re.findall(r'\b(\d{1,2})\b', text)
                    nums = []
                    for n_str in numbers:
                        try:
                            n = int(n_str)
                            if len(n_str) >= 4:  # 期号或年份
                                continue
                            if n > 35:  # 超出红球范围
                                continue
                            if 1 <= n <= 35 or 1 <= n <= 12:
                                nums.append(n)
                        except:
                            continue
                    
                    # 根据上下文赋予不同权重
                    weight = 2 if has_positive else 1
                    for n in nums:
                        if 1 <= n <= 35:
                            red_counts[n] += weight
                        if 1 <= n <= 12:
                            blue_counter[n] += weight
                
                # 3. 提取标题中的号码
                titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
                for title in titles:
                    text = title.get_text()
                    numbers = re.findall(r'\b(\d{1,2})\b', text)
                    for n_str in numbers:
                        try:
                            n = int(n_str)
                            if 1 <= n <= 35:
                                red_counts[n] += 2
                            if 1 <= n <= 12:
                                blue_counter[n] += 2
                        except:
                            continue
                
                print(f"[*] 成功提取: 红球{len(red_counts)}个, 蓝球{len(blue_counter)}个", flush=True)
                
            except Exception as e:
                print(f"[ERROR] 抓取网页 {url} 失败: {e}", flush=True)
                import traceback
                print(traceback.format_exc(), flush=True)
        
        # 输出统计信息
        if red_counts:
            top_red = red_counts.most_common(10)
            print(f"[*] 参考网页 Top 10 红球: {top_red}", flush=True)
        else:
            print(f"[WARN] 未能从网页提取到有效号码，建议：", flush=True)
            print(f"       1. 检查网址是否可访问", flush=True)
            print(f"       2. 尝试使用普通网页（非动态渲染）", flush=True)
            print(f"       3. 或直接在界面上输入杀号条件", flush=True)
        if blue_counter:
            top_blue = blue_counter.most_common(5)
            print(f"[*] 参考网页 Top 5 蓝球: {top_blue}", flush=True)
        
        return {'red': red_counts, 'blue': blue_counter}
        
    def _extract_structured_numbers(self, soup):
        """从表格和列表中提取结构化号码"""
        red_nums = []
        blue_nums = []
            
        # 提取表格数据
        tables = soup.find_all('table')
        for table in tables:
            cells = table.find_all(['td', 'th'])
            for cell in cells:
                text = cell.get_text().strip()
                # 匹配格式如 "01 02 03" 或 "01,02,03"
                nums = re.findall(r'\b(\d{1,2})\b', text)
                for n_str in nums:
                    try:
                        n = int(n_str)
                        if 1 <= n <= 35:
                            red_nums.append(n)
                        if 1 <= n <= 12:
                            blue_nums.append(n)
                    except:
                        continue
            
        # 提取列表数据
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                text = item.get_text()
                nums = re.findall(r'\b(\d{1,2})\b', text)
                for n_str in nums:
                    try:
                        n = int(n_str)
                        if 1 <= n <= 35:
                            red_nums.append(n)
                        if 1 <= n <= 12:
                            blue_nums.append(n)
                    except:
                        continue
            
        return {'red': red_nums, 'blue': blue_nums}

    def parse_historical_data(self, data_str):
        """解析历史数据"""
        lines = data_str.strip().split('\n')
        records = []
        
        for line in lines:
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 3:
                try:
                    period = int(parts[0])
                    date = parts[1]
                    numbers = ' '.join(parts[2:])
                except: continue
                
                if '-' in numbers:
                    red_part, blue_part = numbers.split('-')
                    red_nums = [int(x) for x in red_part.split() if x.isdigit()]
                    blue_nums = [int(x) for x in blue_part.split() if x.isdigit()]
                    
                    if len(red_nums) == 5 and len(blue_nums) == 2:
                        records.append({
                            'period': period,
                            'date': date,
                            'red': sorted(red_nums),
                            'blue': sorted(blue_nums)
                        })
        
        return pd.DataFrame(records)

    def calculate_hot_cold(self, df, recent_n=20):
        """计算冷热号 - 增强版"""
        recent_data = df.tail(recent_n)
        
        red_counter = Counter()
        blue_counter = Counter()
        red_missing = defaultdict(int)  # 遗漏期数
        blue_missing = defaultdict(int)
        
        # 统计出现频率
        for _, row in recent_data.iterrows():
            red_counter.update(row['red'])
            blue_counter.update(row['blue'])
        
        # 计算遗漏期数
        for num in range(1, 36):
            last_appear = -1
            for idx, row in enumerate(recent_data.iterrows()):
                if num in row[1]['red']:
                    last_appear = idx
            red_missing[num] = len(recent_data) - last_appear - 1 if last_appear >= 0 else len(recent_data)
        
        for num in range(1, 13):
            last_appear = -1
            for idx, row in enumerate(recent_data.iterrows()):
                if num in row[1]['blue']:
                    last_appear = idx
            blue_missing[num] = len(recent_data) - last_appear - 1 if last_appear >= 0 else len(recent_data)
        
        # 热号（出现频率 >= 平均值）
        red_avg = sum(red_counter.values()) / 35 if red_counter else 0
        blue_avg = sum(blue_counter.values()) / 12 if blue_counter else 0
        
        hot_red = [k for k, v in red_counter.items() if v >= red_avg]
        cold_red = [i for i in range(1, 36) if red_counter[i] < red_avg]
        
        hot_blue = [k for k, v in blue_counter.items() if v >= blue_avg]
        cold_blue = [i for i in range(1, 13) if blue_counter[i] < blue_avg]
        
        # 超冷号（遗漏 >= 10期）
        super_cold_red = [k for k, v in red_missing.items() if v >= 10]
        super_cold_blue = [k for k, v in blue_missing.items() if v >= 10]
        
        return {
            'hot_red': hot_red,
            'cold_red': cold_red,
            'hot_blue': hot_blue,
            'cold_blue': cold_blue,
            'red_freq': dict(red_counter),
            'blue_freq': dict(blue_counter),
            'red_missing': dict(red_missing),
            'blue_missing': dict(blue_missing),
            'super_cold_red': super_cold_red,
            'super_cold_blue': super_cold_blue
        }

    def train(self, data_str, train_ensemble=True):
        """训练模型 - 增强版"""
        df = self.parse_historical_data(data_str)
        return self.train_from_df(df, train_ensemble=train_ensemble)

    def train_from_df(self, df, train_ensemble=True):
        """从 DataFrame 训练模型 - 确保所有必要属性初始化"""
        self.history_df = df
        
        if len(self.history_df) < 10:
            raise ValueError("历史数据不足，至少需要10期数据")
        
        # 初始化特征权重
        self.feature_weights = {
            'red_sum': {'min': 70, 'max': 130, 'weight': 1.0},
            'red_span': {'min': 15, 'max': 33, 'weight': 0.8},
            'red_odd_even': {'balance': True, 'weight': 0.9},
            'red_big_small': {'balance': True, 'weight': 0.7},
            'consecutive': {'max': 2, 'weight': 0.6},
            'zone_balance': {'weight': 0.8},
            'tail_diversity': {'min': 4, 'weight': 0.7},
            'blue_sum': {'min': 4, 'max': 20, 'weight': 0.6},
            'blue_span': {'min': 2, 'max': 11, 'weight': 0.5}
        }
        
        # 构建基础数据结构
        self._build_markov_chain()
        self._learn_patterns()
        self._init_dynamic_weights()
        self._build_actual_numbers_pool()
        self._init_adaptive_weights_from_history()
        
        # 训练集成学习模型
        if train_ensemble and ENSEMBLE_AVAILABLE:
            self._train_ensemble_models()
            # 训练 Stacking 模型（已修复版本兼容问题）
            self._build_stacking_ensemble(self.history_df)
            # 训练蓝球 LSTM 模型
            self._train_blue_lstm()
            # 构建号码共现网络
            self._build_co_occurrence_network()
        
        self.is_trained = True
        return True

    def check_constraints(self, red, blue, last_record, kill_red, kill_blue):
        """基础过滤约束 - V7.1 增强版（严格控制重号与蓝球大小号）"""
        if any(r in kill_red for r in red): return False, "杀红"
        if any(b in kill_blue for b in blue): return False, "杀蓝"
        
        odd_count = sum(1 for x in red if x % 2 == 1)
        if odd_count == 0 or odd_count == 5: return False, "全奇全偶"
        
        # 重号约束增强：前区重号 >= 2 就过滤（大幅提升多样性）
        if last_record is not None:
            last_red = set(last_record['red'])
            last_blue = set(last_record['blue'])
            
            red_overlap = len(set(red) & last_red)
            if red_overlap >= 2:  # 从DEBUG: 从 >= 4 改为 >= 2
                return False, f"前区重号过多({red_overlap})"
            
            # 后区重号约束：重复 1 个就过滤
            blue_overlap = len(set(blue) & last_blue)
            if blue_overlap >= 1:
                return False, f"后区重号({blue_overlap})"
            
        red_sum = sum(red)
        if not (40 <= red_sum <= 165): return False, "和值范围"
        
        # 蓝球大小号平衡约束：不允许全大或全小
        # 小号：1-6，大号：7-12
        blue_small_count = sum(1 for b in blue if b <= 6)
        if blue_small_count == 0:  # 全大
            return False, "蓝球全大号"
        if blue_small_count == 2:  # 全小
            return False, "蓝球全小号"
        
        return True, "OK"

    def score_combination(self, red, blue, hot_cold_info, last_record=None, return_details=False, 
                          red_probas=None, blue_probas=None, lstm_probas=None, similar_periods_override=None,
                          ref_numbers=None):
        """对号码组合进行评分 - V12 数据驱动版（基于2829期历史统计）"""
        score = 500.0  # 基础分大幅提升
        details = []
        red = sorted(red)
        blue = sorted(blue)
        red_sum = sum(red)
        
        # ============ 第一层：极限放宽过滤，避免误杀 ============
        
        # 连号特征（基于历史数据统计）
        consecutive_pairs = sum(1 for i in range(len(red)-1) if red[i+1] - red[i] == 1)
        if consecutive_pairs >= 4:
            score -= 500  # 4+对连号罕见(0%)，大幅扣分
            details.append(f"连号极多({consecutive_pairs})")
        elif consecutive_pairs == 3:
            score -= 100  # 3对连号较少见(0.81%)，适当扣分
            details.append(f"三连号({consecutive_pairs})")
        elif consecutive_pairs == 2:
            score += 80   # 2对连号较常见(9.12%)，小幅加分
            details.append(f"连号丰富({consecutive_pairs})")
        elif consecutive_pairs == 1:
            score += 120  # 1对连号最常见(39.79%)，较高加分
            details.append(f"含连号({consecutive_pairs})")
        else:  # 0对连号
            score += 50   # 0对连号常见(50.28%)，基础加分
            details.append(f"无连号({consecutive_pairs})")
        
        # AC值（基于历史数据统计：AC值4-6占67.94%）
        diffs = set()
        for i in range(len(red)):
            for j in range(i + 1, len(red)):
                diffs.add(abs(red[i] - red[j]))
        ac_val = len(diffs) - 4
        if ac_val >= 5:  # AC值5-6: 67.92% 最常见
            score += 180
            details.append(f"AC值优秀({ac_val})")
        elif ac_val == 4:  # AC值4: 25.02%
            score += 150
            details.append(f"AC值良好({ac_val})")
        elif ac_val >= 3:  # AC值3: 4.20%
            score += 80
            details.append(f"AC值正常({ac_val})")
        elif ac_val >= 1:  # AC值1-2: 2.86%
            score += 30
            details.append(f"AC值偏低({ac_val})")
        # AC值0不常见，未出现，无需特别处理
        
        # 012路平衡（基于历史数据统计：某路≥3个占60.78%）
        m0 = sum(1 for x in red if x % 3 == 0)
        m1 = sum(1 for x in red if x % 3 == 1)
        m2 = sum(1 for x in red if x % 3 == 2)
        # 统计数据显示012路聚集很常见，不应给过高分
        if m0 >= 3 or m1 >= 3 or m2 >= 3:
            score += 120  # 从300降至120（基于60.78%的出现率）
            details.append(f"012路聚集({m0}:{m1}:{m2})")
        
        # 质数分布（基于历史数据统计：≥1个质数占87.49%）
        primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
        p_count = sum(1 for x in red if x in primes)
        if p_count == 0:
            score += 30   # 无质数较少见(12.51%)，小幅加分
            details.append(f"无质数")
        elif p_count == 1:
            score += 80   # 1个质数常见(34.52%)，中等加分
            details.append(f"含质数({p_count})")
        elif p_count == 2:
            score += 120  # 2个质数最常见(36.04%)，较高加分
            details.append(f"质数丰富({p_count})")
        elif p_count == 3:
            score += 100  # 3个质数较少(14.45%)，中等加分
            details.append(f"质数较多({p_count})")
        elif p_count >= 4:
            score += 50   # 4+个质数很少见(2.48%)，小幅加分
            details.append(f"质数极多({p_count})")
        
        # ============ 第二层：全区间和值覆盖（V12数据驱动） ============
        # 基于2829期历史统计：85-115(48.00%)、50-75(20.43%)、76-84(13.68%)
        # 评分原则：最高频区间给最高分，结合最近100期趋势微调
        if 40 <= red_sum <= 180:  # 覆盖所有可能和值
            if 85 <= red_sum <= 115:  # 历史最高频(48.00%)
                score += 380  # 最高分（趋势修正：最近和值↓，-20分）
                details.append("和值黄金区")
            elif 50 <= red_sum <= 75:  # 历史第2频(20.43%)
                score += 250  # 趋势修正：最近和值↓，+50分
                details.append("和值低区")
            elif 76 <= red_sum <= 84:  # 历史第3频(13.68%)
                score += 156  # 趋势修正：最近和值↓，+20分
                details.append("和值中低区")
            elif 116 <= red_sum <= 130:  # 历史第4频(10.64%)
                score += 100
                details.append("和值中高区")
            elif 131 <= red_sum <= 145:  # 历史第5频(3.78%)
                score += 38
                details.append("和值高区")
            elif 40 <= red_sum <= 49:  # 历史第6频(2.19%)
                score += 22
                details.append("和值极低区")
            else:  # 极端区(146-180, 0.67%)
                score += 7
                details.append("和值极端区")
        
        # 跨度特征（新增）
        span = red[-1] - red[0]
        if 18 <= span <= 32:
            score += 200
            details.append(f"跨度适中({span})")
        elif span >= 33 or span <= 17:
            score += 150  # 极端跨度也给分
            details.append(f"跨度特殊({span})")
        
        # 区间分布（不再惩罚不均衡）
        z1 = sum(1 for x in red if x <= 11)
        z2 = sum(1 for x in red if 12 <= x <= 23)
        z3 = sum(1 for x in red if x >= 24)
        if z1 >= 1 and z2 >= 1 and z3 >= 1:  # 三区都有
            score += 200
            details.append(f"三区覆盖({z1}-{z2}-{z3})")
        elif (z1 >= 2 and z2 >= 2) or (z2 >= 2 and z3 >= 2) or (z1 >= 2 and z3 >= 2):
            score += 250  # 两区强势也加分
            details.append(f"双区强势({z1}-{z2}-{z3})")
        
        # 奇偶比（全面覆盖）
        odd_count = sum(1 for x in red if x % 2 == 1)
        if odd_count in [2, 3]:  # 最常见
            score += 200
            details.append(f"奇偶均衡({odd_count}:{ 5-odd_count})")
        elif odd_count in [1, 4]:  # 次常见
            score += 250  # 提高评分
            details.append(f"奇偶偏斜({odd_count}:{5-odd_count})")
        
        # 大小比（V12数据驱动：小号评分基于历史统计）
        # 统计结果：2个(37.22%)、1个(31.35%)、3个(15.20%)、0个(11.88%)
        # 评分原则：根据出现频率设定权重，结合趋势修正
        small_count = sum(1 for x in red if x <= 12)  # 1-12为小号
        big_count = sum(1 for x in red if x > 17)  # 18-35为大号
        
        if small_count == 2:  # 历史最高频(37.22%)
            score += 210  # 最高分（趋势修正：最近小号↑，+30分）
            details.append(f"小号最优({small_count}个)")
        elif small_count == 1:  # 历史第2频(31.35%)
            score += 150
            details.append(f"小号适中({small_count}个)")
        elif small_count == 3:  # 历史第3频(15.20%)
            score += 100  # 趋势修正：最近小号↑，+24分
            details.append(f"小号丰富({small_count}个)")
        elif small_count == 0:  # 历史第4频(11.88%)
            score += 50
            details.append("无小号")
        elif small_count >= 4:  # 历史低频(4.35%)
            score += 40
            details.append(f"小号过多({small_count}个)")
        
        if 2 <= big_count <= 3:
            score += 100
            details.append(f"大号适中({big_count}个)")
        
        # ============ 第三层：历史相似期爆发（权重翻倍） ============
        sim_periods = similar_periods_override
        if not sim_periods and return_details:
            current_feats = {
                'red_sum': red_sum, 'odd_count': odd_count,
                'red_span': span,
                'z1': z1, 'z2': z2, 'z3': z3
            }
            sim_periods = self._find_similar_periods(current_feats, top_k=10)  # 增加到10期
        
        if sim_periods:
            for sp in sim_periods:
                next_data = self._get_next_period_numbers(sp['period'])
                if next_data:
                    overlap = len(set(red) & set(next_data['red']))
                    if overlap >= 1:  # 任何重叠都加分
                        score += overlap * 500  # 从150提升到500！
                        if return_details: details.append(f"历史相似爆发(+{overlap})")
        
        # 邻号分析（新增）
        if last_record is not None:
            last_red = set(last_record['red'])
            last_blue = set(last_record['blue'])
            
            # 计算邻号（相差±1）
            neighbor_count = 0
            for r in red:
                if (r-1 in last_red) or (r+1 in last_red):
                    neighbor_count += 1
            
            if neighbor_count >= 2:
                score += neighbor_count * 150
                details.append(f"邻号丰富({neighbor_count}个)")
            
            # 重号策略调整
            red_overlap = len(set(red) & last_red)
            if red_overlap == 0:
                score += 150  # 全新号加分
                details.append("前区全新")
            elif red_overlap == 1:
                score += 200  # 1个重号更常见
                details.append("前区1重号")
            
            blue_overlap = len(set(blue) & last_blue)
            if blue_overlap == 0:
                score += 100
                details.append("后区全新")
        
        # 蓝球大小号
        blue_small = sum(1 for b in blue if b <= 6)
        if blue_small == 1:
            score += 150
            details.append("蓝球1小1大")
        elif blue_small == 0 or blue_small == 2:
            score += 100  # 全大全小也给分
            details.append("蓝球特殊组合")
        
        # ============ 第四层：ML模型置信度（保持谨慎） ============
        red_stacking_boost = 1.0
        if red_probas:
            p_vals = sorted([red_probas.get(n, 0) for n in red], reverse=True)
            top3_sum = sum(p_vals[:3])
            if top3_sum > 0.3:  # 降低阈值
                red_stacking_boost = 1.0 + (top3_sum * 2.0)  # 保持适度
                details.append(f"ML推荐({top3_sum:.2f})")
        
        # 蓝球热力
        blue_boost = 1.0
        if blue_probas or lstm_probas:
            b_avg_conf = 0
            for b in blue:
                conf = (blue_probas.get(b, 0) * 0.6 if blue_probas else 0) + \
                       (lstm_probas.get(b, 0) * 0.4 if lstm_probas else 0)
                b_avg_conf += conf
            
            if b_avg_conf > 0.15:  # 降低阈值
                blue_boost = 1.0 + (b_avg_conf * 4.0)  # 提高系数
                details.append("后区共振")
        
        # ============ 第五层：参考网页加成（提高权重） ============
        ref_boost = 1.0
        if ref_numbers:
            red_ref = ref_numbers.get('red', Counter())
            blue_ref = ref_numbers.get('blue', Counter())
            
            top_red_ref = [n for n, c in red_ref.most_common(15)]  # 增加到15个
            top_blue_ref = [n for n, c in blue_ref.most_common(5)]   # 增加到5个
            
            ref_hits = len(set(red) & set(top_red_ref))
            if ref_hits >= 1:  # 任何匹配都加分
                ref_boost += (ref_hits * 0.2)  # 提高系数
                details.append(f"专家推荐({ref_hits}个)")
            
            blue_ref_hits = len(set(blue) & set(top_blue_ref))
            if blue_ref_hits >= 1:
                ref_boost += 0.2
                details.append("专家蓝球")
        
        # ============ 最终融合 ============
        final_score = score * red_stacking_boost * blue_boost * ref_boost
        
        if return_details:
            return final_score, " | ".join(details)
        return final_score
    
    def generate_candidates(self, n_candidates, available_red, available_blue, hot_cold_info, 
                            red_probas=None, blue_probas=None, lstm_probas=None):
        """V10 改进：增加小号和低和值组合的多样性"""
        candidates = []
        strategy_types = [
            'weighted_actual', 'ensemble', 'timeseries', 'missing_regression', 
            'frequency_based', 'pattern_match', 'correlation', 'modulus',
            'similarity', 'hot_cold_mix', 'cold_rebound', 'ensemble_top',
            'core_anchor', 'pure_random', 'small_number', 'low_sum'  # V10新增
        ]
        seen = set()
        
        # --- 核心锁定准备 (使用传入的预计算概率) ---
        core_red_pool = []
        if red_probas:
            sorted_probas = sorted(red_probas.items(), key=lambda x: x[1], reverse=True)
            core_red_pool = [n for n, p in sorted_probas[:12]] # 扩大核心池
        
        # 预计算相似度号码
        sim_nums = self._select_by_similarity(available_red, 0)
        
        max_attempts = n_candidates * 10 # 降低重试倍数，提升性能
        attempt = 0
        while len(candidates) < n_candidates and attempt < max_attempts:
            strategy = strategy_types[attempt % len(strategy_types)]
            offset = attempt // len(strategy_types)
            attempt += 1
            
            # 前区选择
            red = []
            if strategy == 'pure_random':
                red = list(np.random.choice(available_red, 5, replace=False))
            elif strategy == 'small_number':  # V10新增：专注小号组合
                small_pool = [n for n in available_red if n <= 15]
                if len(small_pool) >= 3:
                    small_count = np.random.choice([2, 3, 4])  # 随机2-4个小号
                    red_small = list(np.random.choice(small_pool, min(small_count, len(small_pool)), replace=False))
                    others = [n for n in available_red if n not in red_small]
                    red = red_small + list(np.random.choice(others, 5 - len(red_small), replace=False))
                else:
                    red = list(np.random.choice(available_red, 5, replace=False))
            elif strategy == 'low_sum':  # V10新增：低和值组合(50-80)
                # 优先选择小中号
                low_mid_pool = [n for n in available_red if n <= 25]
                if len(low_mid_pool) >= 5:
                    red = sorted(list(np.random.choice(low_mid_pool, 5, replace=False)))
                    # 确保和值偈50-80区间
                    if not (50 <= sum(red) <= 80):
                        # 重新生成
                        red = self._generate_low_sum_combo(available_red, 50, 80)
                else:
                    red = list(np.random.choice(available_red, 5, replace=False))
            elif strategy == 'core_anchor' and core_red_pool:
                # 1-3个核心号 + 随机
                anchor_count = np.random.choice([1, 2, 3])
                anchors = list(np.random.choice(core_red_pool, min(anchor_count, len(core_red_pool)), replace=False))
                others = [n for n in available_red if n not in anchors]
                red = anchors + list(np.random.choice(others, 5 - len(anchors), replace=False))
            # ... (其他策略保持原调用)
            elif strategy == 'ensemble' and ENSEMBLE_AVAILABLE and self.ensemble_models.get('red'):
                red = self._select_by_ensemble(available_red, hot_cold_info, offset=offset)
            elif strategy == 'timeseries':
                red = self._select_by_timeseries(available_red, hot_cold_info, offset=offset)
            elif strategy == 'missing_regression':
                red = self._select_by_missing_regression(available_red, hot_cold_info, offset=offset)
            elif strategy == 'correlation':
                red = self._select_by_correlation(available_red, hot_cold_info, offset=offset)
            elif strategy == 'modulus':
                red = self._select_by_modulus(available_red, hot_cold_info, offset=offset)
            elif strategy == 'similarity':
                red = sim_nums 
            elif strategy == 'hot_cold_mix':
                red = self._select_by_hot_cold_mix(available_red, hot_cold_info, offset=offset)
            elif strategy == 'cold_rebound':
                red = self._select_by_cold_rebound(available_red, hot_cold_info, offset=offset)
            elif strategy == 'ensemble_top':
                red = self._select_by_ensemble_top(available_red, hot_cold_info, offset=offset)
            else:
                red = self._select_by_frequency(available_red, hot_cold_info, offset=offset)
                
            # 后区策略 (传入预计算概率)
            blue = self._select_blue_by_strategy(available_blue, hot_cold_info, 'hybrid', offset=offset,
                                               blue_probas=blue_probas, lstm_probas=lstm_probas)
            
            if not red or not blue: continue
            
            combo_key = tuple(sorted(red) + sorted(blue))
            if combo_key not in seen:
                seen.add(combo_key)
                candidates.append({'red': sorted(red), 'blue': sorted(blue)})
                
        return candidates
    
    def _generate_low_sum_combo(self, available_red, min_sum, max_sum):
        """生成指定和值范围的组合"""
        max_tries = 100
        for _ in range(max_tries):
            red = sorted(list(np.random.choice(available_red, 5, replace=False)))
            if min_sum <= sum(red) <= max_sum:
                return red
        # 如果失败，返回随机组合
        return sorted(list(np.random.choice(available_red, 5, replace=False)))

    def _select_blue_by_strategy(self, available_blue, hot_cold_info, strategy, offset=0, 
                                 blue_probas=None, lstm_probas=None):
        """核心蓝球预测 - 融合 Stacking 与 LSTM 置信度 (性能优化)"""
        all_blue_combos = list(combinations(range(1, 13), 2))
        scored_combos = []
        
        last_rec = self.history_df.iloc[-1] if len(self.history_df) > 0 else None
        last_blue = last_rec['blue'] if last_rec is not None else []
        last_blue_sum = sum(last_blue) if last_blue else 0
        
        # 允许使用传入的概率，如果没传则现场算一次（通常应该由外层传入）
        b_stack_probas = blue_probas if blue_probas is not None else {}
        b_lstm_probas = lstm_probas if lstm_probas is not None else {}
        
        # --- 热力图计算 ---
        top_stack = sorted(b_stack_probas.items(), key=lambda x: x[1], reverse=True)[:4]
        top_lstm = sorted(b_lstm_probas.items(), key=lambda x: x[1], reverse=True)[:4]
        hot_nums = set([n for n, p in top_stack]) & set([n for n, p in top_lstm])
        
        # 马尔可夫转移
        sum_trans = self.markov_transitions.get('blue_sum', {})
        expected_sums = sorted(sum_trans.get(last_blue_sum, {}).items(), key=lambda x: x[1], reverse=True)
        top_sums = [s for s, count in expected_sums[:3]]
        
        for combo in all_blue_combos:
            combo = sorted(combo)
            s = 100.0
            b1, b2 = combo
            b_sum = b1 + b2
            
            # 1. 置信度融合 (主分)
            conf1 = (b_stack_probas.get(b1, 0) * 0.6) + (b_lstm_probas.get(b1, 0) * 0.4)
            conf2 = (b_stack_probas.get(b2, 0) * 0.6) + (b_lstm_probas.get(b2, 0) * 0.4)
            s += (conf1 + conf2) * 1000 
            
            # 2. 热力图爆发加成
            if b1 in hot_nums: s += 300
            if b2 in hot_nums: s += 300
            
            # 3. 统计规律
            if b_sum in top_sums: s += 100
            if 4 <= (b2 - b1) <= 8: s += 60
            if b1 % 2 != b2 % 2: s += 50
            
            scored_combos.append({'combo': combo, 'score': s})
            
        # V10 改进：增加随机性，避免固定推荐5,7
        # 根据 offset 决定是采 Top 还是采随机
        if offset % 3 == 0:  # 1/3 概率取Top1
            return scored_combos[0]['combo']
        elif offset % 3 == 1:  # 1/3 概率从Top10中随机
            top10 = scored_combos[:10]
            return top10[np.random.randint(len(top10))]['combo']
        else:  # 1/3 概率权重采样
            # 使用索引采样而非直接采样元组
            scores = np.array([x['score'] for x in scored_combos])
            scores = scores - np.min(scores) + 1.0 # 平滑
            probs = scores / scores.sum()
            
            try:
                # 采样索引，然后返回对应的组合
                selected_idx = np.random.choice(len(scored_combos), p=probs)
                return scored_combos[selected_idx]['combo']
            except:
                return scored_combos[0]['combo']

    def _analyze_blue_trends(self, hc):
        pass # 占位用于未来扩展

    def _select_by_similarity(self, available_red, offset=0):
        if len(self.history_df) < 50: return self._select_by_frequency(available_red, {}, offset)
        
        # 提取最近 3 期的模式
        recent = self.history_df.tail(3)
        recent_pattern = [sum(r['red']) for _, r in recent.iterrows()]
        
        best_idx = -1
        min_diff = float('inf')
        
        # 寻找历史上最相似的窗口 (仅检查最近 300 期)
        search_df = self.history_df.tail(300)
        for i in range(len(search_df) - 5):
            window = [sum(r['red']) for _, r in search_df.iloc[i:i+3].iterrows()]
            diff = sum(abs(a - b) for a, b in zip(recent_pattern, window))
            if diff < min_diff:
                min_diff = diff
                best_idx = i + 3 # 取窗口后的下一期
        
        if best_idx != -1 and best_idx < len(self.history_df):
            target_red = self.history_df.iloc[best_idx]['red']
            res = [r for r in target_red if r in available_red]
            attempt_inner = 0
            while len(res) < 5 and attempt_inner < 100:
                attempt_inner += 1
                n = available_red[np.random.randint(len(available_red))]
                if n not in res: res.append(n)
            return sorted(res[:5])
        return self._select_by_frequency(available_red, {}, offset)

    def _select_by_hot_cold_mix(self, available_red, hot_cold_info, offset=0):
        hot = hot_cold_info.get('hot_red', [])
        cold = hot_cold_info.get('cold_red', [])
        warm = [n for n in available_red if n not in hot and n not in cold]
        if not warm: warm = available_red
        
        # V7 增强：30% 概率纯随机，70% 概率热温冷混搭
        if np.random.rand() < 0.3:
            return sorted(list(np.random.choice(available_red, 5, replace=False)))
            
        res = []
        if hot: res.extend(np.random.choice(hot, min(2, len(hot)), replace=False))
        if warm: res.extend(np.random.choice(warm, min(2, len(warm)), replace=False))
        if cold: res.extend(np.random.choice(cold, min(1, len(cold)), replace=False))
        
        while len(res) < 5:
            n = available_red[np.random.randint(len(available_red))]
            if n not in res: res.append(n)
        return sorted(res[:5])

    def _select_by_ensemble_top(self, available_red, hot_cold_info, offset=0):
        """直接选取集成模型概率最高的 5 个号码"""
        if not self.ensemble_models.get('red'): return self._select_by_frequency(available_red, hot_cold_info, offset)
        if not hasattr(self, '_cached_feat'):
            self._cached_feat = self.extract_features(self.history_df, last_only=True).iloc[-1:]
        current_feat = self._cached_feat
        scores = {}
        for num in available_red:
            if num in self.ensemble_models['red']:
                m = self.ensemble_models['red'][num]
                p = (m['rf'].predict_proba(current_feat.values)[0][1] + m['gb'].predict_proba(current_feat.values)[0][1]) / 2
                scores[num] = p
            else: scores[num] = 0
        sorted_nums = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # 选取第 offset 开始的 5 个
        idx = offset % (len(sorted_nums) - 5) if len(sorted_nums) > 5 else 0
        return sorted([n for n, s in sorted_nums[idx:idx+5]])

    def _select_by_cold_rebound(self, available_red, hot_cold_info, offset=0):
        # 专门选择遗漏期数长的号码（冷号回补）
        miss = hot_cold_info.get('red_missing', {})
        sorted_miss = sorted(available_red, key=lambda x: miss.get(x, 0), reverse=True)
        
        if offset > 0:
            sorted_miss = sorted_miss[offset % len(sorted_miss):] + sorted_miss[:offset % len(sorted_miss)]
            
        return sorted(sorted_miss[:5])

    def _select_by_frequency(self, available_red, hot_cold_info, offset=0):
        freq = hot_cold_info.get('red_freq', {})
        sorted_nums = sorted([(n, freq.get(n, 0) + np.random.normal(0, 0.05)) for n in available_red], key=lambda x: x[1], reverse=True)
        return self._weighted_sample(sorted_nums, 5, top_k=30)

    def _weighted_sample(self, items_with_scores, n=5, top_k=25):
        """基于权重的非等概率采样，增加候选组合的多样性
        V7 增强：增大采样池至 top_k (默认25)，确保即使模型不看好也有机会选中"""
        if not items_with_scores: return []
        
        # 取前 top_k 个候选
        candidates = items_with_scores[:top_k]
        items = [x[0] for x in candidates]
        
        # 使用 softmax 或平滑后的分数作为权重，防止头部号过度垄断
        scores = np.array([x[1] for x in candidates])
        scores = scores - np.min(scores) + 0.1 # 平滑处理
        probs = scores / scores.sum()
        
        try:
            return sorted(list(np.random.choice(items, min(n, len(items)), replace=False, p=probs)))
        except:
            return sorted([x[0] for x in items_with_scores[:n]])

    def _select_by_ensemble(self, available_red, hot_cold_info, offset=0):
        if not self.ensemble_models.get('red'): return self._select_by_frequency(available_red, hot_cold_info, offset)
        if not hasattr(self, '_cached_feat'):
            self._cached_feat = self.extract_features(self.history_df, last_only=True).iloc[-1:]
        current_feat = self._cached_feat
        scores = {}
        for num in available_red:
            if num in self.ensemble_models['red']:
                m = self.ensemble_models['red'][num]
                p = (m['rf'].predict_proba(current_feat)[0][1] + m['gb'].predict_proba(current_feat)[0][1]) / 2
                scores[num] = p
            else: scores[num] = 0.01 # 给一个极小的基础分，确保有机会被选中
        sorted_nums = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # V7 改进：采样池扩大到 25 个
        return self._weighted_sample(sorted_nums, 5, top_k=25)

    def _select_by_timeseries(self, available_red, hot_cold_info, offset=0):
        if len(self.history_df) < 30: return self._select_by_frequency(available_red, hot_cold_info, offset)
        if not hasattr(self, '_cached_moms'):
            recent_10 = self.history_df.tail(10); recent_30 = self.history_df.tail(30)
            f10 = Counter(); [f10.update(r['red']) for _, r in recent_10.iterrows()]
            f30 = Counter(); [f30.update(r['red']) for _, r in recent_30.iterrows()]
            self._cached_moms = {n: (f10.get(n, 0)/10 + 0.1) / (f30.get(n, 0)/30 + 0.1) for n in range(1, 36)}
        moms = self._cached_moms
        sorted_nums = sorted([(n, moms[n]) for n in available_red], key=lambda x: x[1], reverse=True)
        return self._weighted_sample(sorted_nums, 5, top_k=25)

    def _select_by_missing_regression(self, available_red, hot_cold_info, offset=0):
        miss = hot_cold_info.get('red_missing', {})
        scores = {n: miss.get(n, 0) * (2.5 if miss.get(n, 0) > 15 else 1.5 if miss.get(n, 0) > 8 else 0.4) for n in available_red}
        sorted_nums = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return self._weighted_sample(sorted_nums, 5, top_k=25)

    def _select_by_correlation(self, available_red, hot_cold_info, offset=0):
        if not hasattr(self, 'common_pairs') or not self.common_pairs: return self._select_by_frequency(available_red, hot_cold_info, offset)
        common = self.common_pairs
        if offset > 0: common = common[offset % len(common):] + common[:offset % len(common)]
        res = []
        for p in common:
            if p[0] in available_red and p[1] in available_red:
                res.extend([p[0], p[1]]); break
        attempt_inner = 0
        while len(res) < 5 and attempt_inner < 100:
            attempt_inner += 1
            n = available_red[len(res) % len(available_red)]
            if n not in res: res.append(n)
        return sorted(res[:5])

    def _select_by_modulus(self, available_red, hot_cold_info, offset=0):
        rems = {i: [n for n in available_red if n % 3 == i] for i in range(3)}
        for i in rems: rems[i].sort(key=lambda x: hot_cold_info.get('red_freq', {}).get(x, 0), reverse=True)
        res = rems[0][:2] + rems[1][:2] + rems[2][:1]
        while len(res) < 5:
            n = available_red[np.random.randint(len(available_red))]
            if n not in res: res.append(n)
            if len(res) >= 5: break
        return sorted(res[:5])

    def _select_blue_deterministic(self, available_blue, hot_cold_info, offset=0):
        miss = hot_cold_info.get('blue_missing', {})
        scores = {n: miss.get(n, 0) * 3.0 + hot_cold_info.get('blue_freq', {}).get(n, 0) + np.random.normal(0, 0.1) for n in available_blue}
        sorted_blue = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if offset > 0: sorted_blue = sorted_blue[offset % len(sorted_blue):] + sorted_blue[:offset % len(sorted_blue)]
        res = [sorted_blue[0][0]]
        for i in range(1, len(sorted_blue)):
            if sorted_blue[i][0] % 2 != res[0] % 2: res.append(sorted_blue[i][0]); break
        if len(res) < 2: res.append(sorted_blue[1][0])
        return sorted(res[:2])

    def _build_stacking_ensemble(self, df):
        """构建 Stacking 集成模型 - 针对前区(1-35)和后区(1-12)"""
        if not ENSEMBLE_AVAILABLE or len(df) < 30: return
        print(f"[*] 训练 Stacking 集成系统 ({len(df)}期)...", flush=True)
        
        # 提取特征
        features = self.extract_features(df)
        
        def train_stack(numbers_range, target_key):
            models_dict = {}
            for n in numbers_range:
                y = [1 if n in r[target_key] else 0 for _, r in df.iterrows()]
                if sum(y) < 5: continue
                
                try:
                    import xgboost as xgb
                    from lightgbm import LGBMClassifier
                    
                    X_train = features.values
                    y_train = np.array(y)
                    
                    # 基模型 1: XGBoost 原生 (增加轮数提升精度)
                    dtrain = xgb.DMatrix(X_train, label=y_train)
                    xgb_params = {'objective': 'binary:logistic', 'max_depth': 4, 'eta': 0.05, 'eval_metric': 'logloss', 'seed': 42}
                    xgb_model = xgb.train(xgb_params, dtrain, num_boost_round=60, verbose_eval=False)
                            
                    # 基模型 2: LightGBM (增加复杂度)
                    lgb_model = LGBMClassifier(n_estimators=60, max_depth=4, learning_rate=0.05, random_state=42, verbose=-1)
                    lgb_model.fit(X_train, y_train)
                            
                    # 基模型 3: RandomForest (增加树的数量)
                    rf_model = RandomForestClassifier(n_estimators=60, max_depth=6, random_state=42)
                    rf_model.fit(X_train, y_train)
                    
                    # 元特征构建
                    dtest = xgb.DMatrix(X_train)
                    xgb_proba = xgb_model.predict(dtest)
                    lgb_proba = lgb_model.predict_proba(X_train)[:, 1]
                    rf_proba = rf_model.predict_proba(X_train)[:, 1]
                    meta_X = np.column_stack([xgb_proba, lgb_proba, rf_proba])
                    
                    # 元模型: LogisticRegression
                    meta_model = LogisticRegression(random_state=42, max_iter=1000)
                    meta_model.fit(meta_X, y_train)
                    
                    models_dict[n] = {'xgb': xgb_model, 'lgb': lgb_model, 'rf': rf_model, 'meta': meta_model}
                except Exception as e:
                    print(f"  - {target_key} 号码 {n} Stacking 训练失败: {e}")
            return models_dict

        # 分别训练前区和后区
        self.stacking_meta_model = train_stack(range(1, 36), 'red')
        self.blue_stacking_meta_model = train_stack(range(1, 13), 'blue')
        self.save_state() # 训练完成后立即保存，防止丢失进度
        print(f"[*] Stacking 训练完成: 前区 {len(self.stacking_meta_model)}个, 后区 {len(self.blue_stacking_meta_model)}个")

    def _predict_with_stacking(self, features, target_type='red'):
        """使用 Stacking 模型预测概率"""
        models_source = self.stacking_meta_model if target_type == 'red' else self.blue_stacking_meta_model
        if not models_source: return {}
        
        import xgboost as xgb
        probas = {}
        X = features.values
        
        for n, models in models_source.items():
            try:
                # 获取基模型概率
                dtest = xgb.DMatrix(X)
                xgb_p = models['xgb'].predict(dtest)[-1]
                lgb_p = models['lgb'].predict_proba(X)[-1, 1]
                rf_p = models['rf'].predict_proba(X)[-1, 1]
                
                # 元预测
                meta_X = np.array([[xgb_p, lgb_p, rf_p]])
                probas[n] = models['meta'].predict_proba(meta_X)[0, 1]
            except: continue
        return probas

    def _train_ensemble_models(self):
        """训练深度集成学习模型"""
        if not ENSEMBLE_AVAILABLE or len(self.history_df) < 30: return
        print(f"[*] 训练集成模型 ({len(self.history_df)}期)...")
        feats = self.extract_features(self.history_df)
        self.ensemble_models['red'] = {}
        self.ensemble_models['blue'] = {}
        for n in range(1, 36):
            y = [1 if n in r['red'] else 0 for _, r in self.history_df.iterrows()]
            if sum(y) < 5: continue
            try:
                m1 = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
                m2 = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
                m1.fit(feats.values, y); m2.fit(feats.values, y)
                self.ensemble_models['red'][n] = {'rf': m1, 'gb': m2}
            except: pass
        for n in range(1, 13):
            y = [1 if n in r['blue'] else 0 for _, r in self.history_df.iterrows()]
            if sum(y) < 3: continue
            try:
                m1 = RandomForestClassifier(n_estimators=30, max_depth=3, random_state=42)
                m1.fit(feats.values, y)
                self.ensemble_models['blue'][n] = {'rf': m1}
            except: pass
        print(f"[*] 集成模型训练完成")

    def extract_features(self, df, last_only=False):
        """提取深度增强特征 - V4版本 (支持增量缓存优化)"""
        import joblib
        cache_path = os.path.join(self.assets_dir, 'features_cache.pkl')
        
        # 尝试加载缓存
        feature_cache = {}
        if os.path.exists(cache_path):
            try: feature_cache = joblib.load(cache_path)
            except: pass

        target_df = df.tail(15) if last_only else df
        res = []
        
        # 预计算冷热和遗漏 (这些是动态的，但可以在单次调用中共享)
        hc = self.calculate_hot_cold(df)
        red_miss = hc['red_missing']
        
        cache_updated = False
        for i in range(len(target_df)):
            idx = i + (len(df) - len(target_df))
            row = target_df.iloc[i]
            p_key = str(row['period'])
            
            # 如果缓存中有且不是为了计算“趋势”等动态字段，可以复用
            # 但由于特征中包含 sum_trend（依赖窗口），完全缓存需要细心处理
            # 这里我们缓存“基础静态特征”，动态特征现场叠加
            
            if p_key in feature_cache and not last_only:
                res.append(feature_cache[p_key])
                continue

            r = sorted(row['red'])
            b = sorted(row['blue'])
            
            # 基础统计与 V4 特征提取
            red_sum = sum(r); red_span = r[-1] - r[0]
            odd_count = sum(1 for x in r if x % 2 == 1)
            z1 = sum(1 for x in r if x <= 11); z2 = sum(1 for x in r if 12 <= x <= 23); z3 = sum(1 for x in r if x >= 24)
            blue_sum = sum(b); blue_span = b[1] - b[0]
            gaps = [r[j+1]-r[j] for j in range(len(r)-1)]
            avg_gap = np.mean(gaps); std_gap = np.std(gaps)
            tail_diversity = len(set([x % 10 for x in r]))
            m0 = sum(1 for x in r if x % 3 == 0); m1 = sum(1 for x in r if x % 3 == 1); m2 = sum(1 for x in r if x % 3 == 2)
            diffs = set()
            for j in range(len(r)):
                for k in range(j + 1, len(r)): diffs.add(abs(r[j] - r[k]))
            ac_val = len(diffs) - 4
            missing_vals = [red_miss.get(num, 0) for num in r]
            missing_sum = sum(missing_vals); max_miss = max(missing_vals)
            repeat_count = 0; jump_count = 0
            if idx > 0:
                last_red = set(df.iloc[idx-1]['red'])
                repeat_count = len(set(r) & last_red)
                if idx > 1:
                    prev_red = set(df.iloc[idx-2]['red'])
                    jump_count = len(set(r) & prev_red)
            prime_count = sum(1 for x in r if x in {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31})
            tail_sum = sum(x % 10 for x in r)
            consecutive_count = sum(1 for j in range(len(r)-1) if r[j+1] - r[j] == 1)
            
            # 趋势特征 (动态)
            sum_trend = 0
            if idx >= 10:
                avg5_sum = np.mean([sum(x['red']) for _, x in df.iloc[idx-5:idx].iterrows()])
                sum_trend = red_sum - avg5_sum
            
            f = [
                red_sum, red_span, odd_count, z1, z2, z3, blue_sum, blue_span,
                avg_gap, std_gap, tail_diversity, ac_val, missing_sum, repeat_count, 
                jump_count, prime_count, tail_sum, m0, m1, m2, max_miss, consecutive_count, sum_trend
            ]
            res.append(f)
            
            # 更新缓存 (仅在全量提取时)
            if not last_only:
                feature_cache[p_key] = f
                cache_updated = True
                
        if cache_updated:
            try: joblib.dump(feature_cache, cache_path)
            except: pass
            
        columns = [
            'red_sum', 'red_span', 'odd_count', 'z1', 'z2', 'z3', 'blue_sum', 'blue_span',
            'avg_gap', 'std_gap', 'tail_diversity', 'ac_val', 'missing_sum', 'repeat_count', 
            'jump_count', 'prime_count', 'tail_sum', 'm0', 'm1', 'm2', 'max_miss', 'consecutive_count', 'sum_trend'
        ]
        return pd.DataFrame(res, columns=columns)

    def predict(self, period, n_combinations=20, n_compound=10, exporter=None, cancel_check=None, kill_red=None, kill_blue=None, 
                sum_range=None, odd_even_ratio=None, is_backtest=False, reference_urls=None):
        """生成预测 - V8 全量架构重构版（枚举所有符合条件的组合）
        
        参数:
            n_combinations: 单式号码数量（默认20组5+2）
            n_compound: 复试号码数量（默认10组8+3）
        """
        if not self.is_trained: raise ValueError("未训练")
        
        # 基于期号设置随机种子，确保相同输入产生相同结果
        try:
            seed = int(period) if isinstance(period, (int, str)) else 26000
        except:
            seed = 26000
        np.random.seed(seed)
        print(f"[*] 设置随机种子: {seed} (基于期号 {period})", flush=True)
        
        # 处理参数
        kill_red = set(kill_red) if kill_red else set()
        kill_blue = set(kill_blue) if kill_blue else set()
        
        # 提取参考网页号码
        ref_numbers = self._fetch_reference_numbers(reference_urls) if reference_urls else None
        
        # 清除缓存
        for attr in ['_cached_feat', '_cached_moms']:
            if hasattr(self, attr): delattr(self, attr)
        
        last = self.history_df.iloc[-1] if len(self.history_df) > 0 else None
        hc = self.calculate_hot_cold(self.history_df)
        
        # 构建所有历史开奖号码集合（用于过滤重复）
        # 优先从 daletou_history_full.txt 加载完整历史数据
        historical_combos = set()
        if not is_backtest:
            try:
                from export_combinations import DaletouExporter
                exporter = DaletouExporter()
                historical_data = exporter.get_historical_combinations()
                
                # 转换为 (red_tuple, blue_tuple) 格式
                for combo in historical_data:
                    if len(combo) == 7:  # 5个红球 + 2个蓝球
                        red_tuple = tuple(combo[:5])
                        blue_tuple = tuple(combo[5:])
                        historical_combos.add((red_tuple, blue_tuple))
                
                print(f"[*] 已从完整历史数据加载 {len(historical_combos)} 组历史开奖号码用于过滤", flush=True)
            except Exception as e:
                print(f"[WARN] 加载完整历史数据失败: {e}，回退到使用history_df", flush=True)
                # 回退方案：使用 history_df
                for _, row in self.history_df.iterrows():
                    red_tuple = tuple(sorted(row['red']))
                    blue_tuple = tuple(sorted(row['blue']))
                    historical_combos.add((red_tuple, blue_tuple))
                print(f"[*] 已从history_df加载 {len(historical_combos)} 组历史开奖号码用于过滤", flush=True)
        
        # 计算可用号码池（剩余可用号码）
        avail_red = [n for n in range(1, 36) if n not in kill_red]
        avail_blue = [n for n in range(1, 13) if n not in kill_blue]
        
        print(f"[*] 可用红球: {len(avail_red)}个, 可用蓝球: {len(avail_blue)}个", flush=True)
        
        # 预计算模型概率（用于评分）
        print(f"[*] 开始特征提取...", flush=True)
        last_feat_df = self.extract_features(self.history_df, last_only=True)
        print(f"[*] 特征提取完成", flush=True)
        
        print(f"[*] 开始ML模型预测...", flush=True)
        red_probas = self._predict_with_stacking(last_feat_df, target_type='red') if self.stacking_meta_model else {}
        print(f"[*] 红球预测完成", flush=True)
        blue_probas = self._predict_with_stacking(last_feat_df, target_type='blue') if self.blue_stacking_meta_model else {}
        print(f"[*] 蓝球Stacking预测完成", flush=True)
        lstm_probas = self._predict_blue_with_lstm() if self.blue_lstm_model else {}
        print(f"[*] 蓝球LSTM预测完成", flush=True)
        
        # 预计算历史相似期次
        print(f"[*] 开始查找相似期次...", flush=True)
        last_row_feats = last_feat_df.iloc[-1].to_dict()
        global_similar_periods = self._find_similar_periods(last_row_feats, top_k=8)
        print(f"[*] 相似期次查找完成（找到{len(global_similar_periods)}期）", flush=True)
        
        # ====== V12性能优化：快速过滤 + 缓存预计算 ======
        # 原则：不改变遍历逻辑，保证不遗漏任何组合
        # 优化：提前过滤 + 缓存复用 + 增量计算
        
        # 1. 生成所有可能的红球组合 (C(n,5))
        all_red_combos = list(combinations(avail_red, 5))
        all_blue_combos = list(combinations(avail_blue, 2))
        
        total_combos = len(all_red_combos) * len(all_blue_combos)
        print(f"[*] 总组合数: {total_combos} = {len(all_red_combos)}(红) × {len(all_blue_combos)}(蓝)", flush=True)
        print(f"[*] V12优化：使用快速过滤+缓存预计算，保证全量遍历", flush=True)
        
        # 2. 预计算红球特征缓存（避免重复计算）
        red_features_cache = {}
        print(f"[*] 正在预计算红球特征...", flush=True)
        for red in all_red_combos:
            red = sorted(red)
            red_key = tuple(red)
            red_sum = sum(red)
            odd_count = sum(1 for x in red if x % 2 == 1)
            
            red_features_cache[red_key] = {
                'sum': red_sum,
                'odd_count': odd_count,
                'span': red[-1] - red[0],
                'small_count': sum(1 for x in red if x <= 12),
                'big_count': sum(1 for x in red if x > 17)
            }
        
        print(f"[*] 红球特征缓存完成，开始枚举评分...", flush=True)
        
        evaluated_combos = []
        processed_count = 0
        
        for red in all_red_combos:
            if cancel_check and cancel_check(): 
                break
            
            # V12优化：从缓存中读取特征，避免重复计算
            red = sorted(red)
            red_key = tuple(red)
            features = red_features_cache[red_key]
            red_sum = features['sum']
            odd_count = features['odd_count']
            
            # ====== 仅开始预测/导出模式执行过滤（回测模式无任何过滤） ======
            if not is_backtest:
                # 前置必过滤条件（1）全奇全偶过滤
                if odd_count == 0 or odd_count == 5:
                    continue
                
                # 前置必过滤条件（2）四连号过滤（>=4连号）
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
                
                # 前置必过滤条件（3）等差数列过滤
                if len(red) >= 3:
                    diffs = [red[i+1] - red[i] for i in range(len(red)-1)]
                    if len(set(diffs)) == 1 and diffs[0] > 0:
                        continue
                
                # 前置必过滤条件（4）等比数列过滤
                if len(red) >= 3:
                    is_geometric = False
                    for i in range(len(red) - 2):
                        if red[i] > 0 and red[i+1] > 0:
                            ratio1 = red[i+1] / red[i]
                            ratio2 = red[i+2] / red[i+1]
                            if abs(ratio1 - ratio2) < 0.01 and ratio1 > 1:
                                is_geometric = True
                                break
                    if is_geometric:
                        continue
                
                # 前置必过滤条件（5）同区号码过滤（5个球全在同一区）
                zone1 = sum(1 for x in red if 1 <= x <= 11)
                zone2 = sum(1 for x in red if 12 <= x <= 23)
                zone3 = sum(1 for x in red if 24 <= x <= 35)
                if zone1 == 5 or zone2 == 5 or zone3 == 5:
                    continue
            
            # ====== 用户手动输入过滤条件（仅预测/导出模式） ======
            if not is_backtest:
                # 过滤条件：和值范围
                if sum_range and not (sum_range[0] <= red_sum <= sum_range[1]):
                    continue
                
                # 过滤条件：奇偶比
                if odd_even_ratio:
                    try:
                        target_odd = int(odd_even_ratio.split(':')[0])
                        if odd_count != target_odd:
                            continue
                    except: pass
                
                # 过滤条件：重号限制（与上期重复数）
                if last is not None:
                    red_overlap = len(set(red) & set(last['red']))
                    if red_overlap >= 4:
                        continue
            
            # 进入蓝球遍历
            for blue in all_blue_combos:
                if cancel_check and cancel_check():
                    break
                
                blue = sorted(blue)
                
                # ====== 前置必过滤条件：历史开奖号码（仅预测/导出模式） ======
                if not is_backtest:
                    combo_key = (tuple(red), tuple(blue))
                    if combo_key in historical_combos:
                        continue
                
                # ====== 用户手动输入过滤条件（仅预测/导出模式） ======
                if not is_backtest:
                    # 蓝球重号过滤（>= 2个重号）
                    if last is not None:
                        blue_overlap = len(set(blue) & set(last['blue']))
                        if blue_overlap >= 2:
                            continue
                
                # 通过所有筛选，进行深度评分
                score = self.score_combination(red, blue, hc, last,
                                              red_probas=red_probas,
                                              blue_probas=blue_probas,
                                              lstm_probas=lstm_probas,
                                              similar_periods_override=global_similar_periods,
                                              ref_numbers=ref_numbers)
                
                evaluated_combos.append({'red': list(red), 'blue': list(blue), 'score': score})
                processed_count += 1
                
                # 每处理 10000 组输出一次进度
                if processed_count % 10000 == 0:
                    print(f"[*] 已评分: {processed_count} 组...", flush=True)
        
        print(f"[*] 共评分 {len(evaluated_combos)} 组符合条件的组合", flush=True)
        
        if len(evaluated_combos) == 0:
            print(f"[ERROR] 过滤条件过于严格，没有符合条件的组合！请放宽条件。", flush=True)
            return
        
        # 按照分数降序排序
        evaluated_combos.sort(key=lambda x: x['score'], reverse=True)
        
        # 多样性过滤（MMR）
        final_candidates = []
        for c in evaluated_combos:
            if len(final_candidates) >= n_combinations:
                break
            
            # 检查与已选组合的相似度
            is_too_similar = False
            for selected in final_candidates:
                overlap = len(set(c['red']) & set(selected['red']))
                if overlap >= 4:
                    is_too_similar = True
                    break
            
            if not is_too_similar:
                final_candidates.append(c)
        
        # 如果由于多样性过滤导致不够，则补齐
        if len(final_candidates) < n_combinations:
            for c in evaluated_combos:
                if len(final_candidates) >= n_combinations:
                    break
                if c not in final_candidates:
                    final_candidates.append(c)
        
        print(f"[*] 最终输出 {len(final_candidates)} 组预测结果（单式）", flush=True)
        
        # 生成详细理由并输出单式号码
        for i, c in enumerate(final_candidates):
            if cancel_check and cancel_check():
                break
            
            _, reason = self.score_combination(c['red'], c['blue'], hc, last, return_details=True,
                                              red_probas=red_probas,
                                              blue_probas=blue_probas,
                                              lstm_probas=lstm_probas,
                                              similar_periods_override=global_similar_periods,
                                              ref_numbers=ref_numbers)
            
            item = {
                'type': 'single',  # 标记为单式号码
                'rank': i+1,
                'red': [int(x) for x in c['red']],
                'blue': [int(x) for x in c['blue']],
                'score': round(c['score'], 2),
                'reason': reason,
                'red_str': ' '.join([f'{int(x):02d}' for x in c['red']]),
                'blue_str': ' '.join([f'{int(x):02d}' for x in c['blue']])
            }
            yield item
        
        # ====== 生成8+3复试号码 ======
        if not is_backtest and n_compound > 0:
            print(f"[*] 开始生成 {n_compound} 组8+3复试号码...", flush=True)
            print(f"[*] V12优化：使用快速过滤+缓存，保证全量遍历", flush=True)
            
            # 生成所有8+3组合
            all_red_8 = list(combinations(avail_red, 8))
            all_blue_3 = list(combinations(avail_blue, 3))
            
            total_compound = len(all_red_8) * len(all_blue_3)
            print(f"[*] 复试组合总数: {total_compound} = {len(all_red_8)}(红8) × {len(all_blue_3)}(蓝3)", flush=True)
            print(f"[*] 正在预计算8红球特征...", flush=True)
            
            # 预计算8红球特征缓存
            red_8_features_cache = {}
            for red_8 in all_red_8:
                red_8 = sorted(red_8)
                red_8_key = tuple(red_8)
                red_sum_8 = sum(red_8)
                odd_count_8 = sum(1 for x in red_8 if x % 2 == 1)
                
                red_8_features_cache[red_8_key] = {
                    'sum': red_sum_8,
                    'odd_count': odd_count_8,
                    'small_count': sum(1 for x in red_8 if x <= 12)
                }
            
            print(f"[*] 8红球特征缓存完成，开始遍历评分...", flush=True)
            
            evaluated_compounds = []
            processed = 0
            
            for red_8 in all_red_8:
                if cancel_check and cancel_check():
                    break
                
                # V12优化：从缓存中读取特征，避免重复计算
                red_8 = sorted(red_8)
                red_8_key = tuple(red_8)
                features_8 = red_8_features_cache[red_8_key]
                red_sum_8 = features_8['sum']
                odd_count_8 = features_8['odd_count']
                
                # ====== 前置必过滤条件（8+3复试，仅预测/导出模式） ======
                if not is_backtest:
                    # 1. 全奇全偶过滤（8个球的标准）
                    if odd_count_8 == 0 or odd_count_8 == 8:
                        continue
                    
                    # 2. 四连号过滤（>=4连号）
                    consecutive_count = 1
                    max_consecutive = 1
                    for i in range(len(red_8) - 1):
                        if red_8[i+1] - red_8[i] == 1:
                            consecutive_count += 1
                            max_consecutive = max(max_consecutive, consecutive_count)
                        else:
                            consecutive_count = 1
                    if max_consecutive >= 4:
                        continue
                    
                    # 3. 等差数列过滤
                    if len(red_8) >= 3:
                        diffs = [red_8[i+1] - red_8[i] for i in range(len(red_8)-1)]
                        if len(set(diffs)) == 1 and diffs[0] > 0:
                            continue
                    
                    # 4. 等比数列过滤
                    if len(red_8) >= 3:
                        is_geometric = False
                        for i in range(len(red_8) - 2):
                            if red_8[i] > 0 and red_8[i+1] > 0:
                                ratio1 = red_8[i+1] / red_8[i]
                                ratio2 = red_8[i+2] / red_8[i+1]
                                if abs(ratio1 - ratio2) < 0.01 and ratio1 > 1:
                                    is_geometric = True
                                    break
                        if is_geometric:
                            continue
                    
                    # 5. 同区号码过滤（8个球全在同一区）
                    zone1 = sum(1 for x in red_8 if 1 <= x <= 11)
                    zone2 = sum(1 for x in red_8 if 12 <= x <= 23)
                    zone3 = sum(1 for x in red_8 if 24 <= x <= 35)
                    if zone1 == 8 or zone2 == 8 or zone3 == 8:
                        continue
                
                # ====== 用户手动输入过滤条件（仅预测/导出模式） ======
                if not is_backtest:
                    # 和值范围（8个球需要调整范围）
                    if sum_range:
                        # 8个球的和值约为5个球的1.6倍
                        adjusted_min = int(sum_range[0] * 1.6)
                        adjusted_max = int(sum_range[1] * 1.6)
                        if not (adjusted_min <= red_sum_8 <= adjusted_max):
                            continue
                    
                    # 奇偶比（8个球的标准）
                    if odd_even_ratio:
                        try:
                            target_odd = int(odd_even_ratio.split(':')[0])
                            # 8个球的奇偶比需要调整（约1.6倍）
                            adjusted_odd = int(target_odd * 1.6)
                            if abs(odd_count_8 - adjusted_odd) > 1:  # 允许±1的误差
                                continue
                        except: pass
                    
                    # 重号限制（与上期对比）
                    if last is not None:
                        red_overlap = len(set(red_8) & set(last['red']))
                        if red_overlap >= 4:
                            continue
                
                # 进入蓝球遍历（3个蓝球）
                for blue_3 in all_blue_3:
                    if cancel_check and cancel_check():
                        break
                    
                    blue_3 = sorted(blue_3)
                    
                    # ====== 前置必过滤条件：历史开奖号码（仅预测/导出模式） ======
                    if not is_backtest:
                        # 注：历史开奖都是5+2，8+3不会命中，但保持逻辑一致性
                        combo_key_8 = (tuple(red_8), tuple(blue_3))
                        if combo_key_8 in historical_combos:
                            continue
                    
                    # ====== 用户手动输入过滤条件（仅预测/导出模式） ======
                    if not is_backtest:
                        # 蓝球重号过滤
                        if last is not None:
                            blue_overlap = len(set(blue_3) & set(last['blue']))
                            if blue_overlap >= 2:
                                continue
                    
                    # 评分：使用8个球中的中心5个球进行评分（代表性评分）
                    center_red = red_8[1:6]  # 取中间5个球
                    center_blue = blue_3[:2]  # 取前2个球
                    
                    score = self.score_combination(center_red, center_blue, hc, last,
                                                  red_probas=red_probas,
                                                  blue_probas=blue_probas,
                                                  lstm_probas=lstm_probas,
                                                  similar_periods_override=global_similar_periods,
                                                  ref_numbers=ref_numbers)
                    
                    evaluated_compounds.append({
                        'red': list(red_8),
                        'blue': list(blue_3),
                        'score': score
                    })
                    processed += 1
                    
                    if processed % 10000 == 0:
                        print(f"[*] 复试已评分: {processed} 组...", flush=True)
            
            print(f"[*] 复试共评分 {len(evaluated_compounds)} 组符合条件的8+3组合", flush=True)
            
            if len(evaluated_compounds) == 0:
                print(f"[WARN] 过滤条件过严，无符合条件的8+3组合", flush=True)
            else:
                # 按评分降序排序
                evaluated_compounds.sort(key=lambda x: x['score'], reverse=True)
                
                # 取Top N（应用多样性过滤）
                final_compounds = []
                for c in evaluated_compounds:
                    if len(final_compounds) >= n_compound:
                        break
                    
                    # 检查与已选组合的相似度
                    is_too_similar = False
                    for selected in final_compounds:
                        overlap = len(set(c['red']) & set(selected['red']))
                        if overlap >= 6:  # 8个球，允许6个重复
                            is_too_similar = True
                            break
                    
                    if not is_too_similar:
                        final_compounds.append(c)
                
                # 如果不够，直接补充
                if len(final_compounds) < n_compound:
                    for c in evaluated_compounds:
                        if len(final_compounds) >= n_compound:
                            break
                        if c not in final_compounds:
                            final_compounds.append(c)
                
                print(f"[*] 最终输出 {len(final_compounds)} 组8+3复试号码", flush=True)
                
                # 生成详细理由并输出
                for i, c in enumerate(final_compounds):
                    if cancel_check and cancel_check():
                        break
                    
                    center_red = c['red'][1:6]
                    center_blue = c['blue'][:2]
                    
                    _, reason = self.score_combination(center_red, center_blue, hc, last, return_details=True,
                                                      red_probas=red_probas,
                                                      blue_probas=blue_probas,
                                                      lstm_probas=lstm_probas,
                                                      similar_periods_override=global_similar_periods,
                                                      ref_numbers=ref_numbers)
                    
                    item = {
                        'type': 'compound',
                        'rank': i + 1,
                        'red': [int(x) for x in c['red']],
                        'blue': [int(x) for x in c['blue']],
                        'score': round(c['score'], 2),
                        'reason': f"复试组合(8+3)：{reason}",
                        'red_str': ' '.join([f'{int(x):02d}' for x in c['red']]),
                        'blue_str': ' '.join([f'{int(x):02d}' for x in c['blue']]),
                        'combination_count': self._calc_compound_count(8, 3)
                    }
                    yield item

    def _calc_compound_count(self, red_count, blue_count):
        """计算复试号码包含的单式注数"""
        from math import comb
        return comb(red_count, 5) * comb(blue_count, 2)

    def validate_model(self, start, end, train_ensemble=True, cancel_check=None, on_period_complete=None):
        """回测验证 - 诚实验证版 (支持流式反馈)"""
        try:
            start = int(start)
            end = int(end)
        except: pass
            
        val_data = self.history_df[(self.history_df['period'] >= start) & (self.history_df['period'] <= end)].copy()
        if len(val_data) == 0: return {'success': False, 'error': '无数据'}
        
        results = []
        hits_dist = Counter()
        total_red_hits = 0
        total_blue_hits = 0
        
        # 初始化一个用于回测的持久化预测器
        predictor = DaletouPredictor()
        
        for i, row in val_data.iterrows():
            if cancel_check and cancel_check():
                break
            
            p = row['period']
            act_r = row['red']
            act_b = row['blue']
            train_df = self.history_df[self.history_df['period'] < p]
            
            try:
                # 预测逻辑 (保持 V7 优化版不变)
                predictor.history_df = train_df
                predictor.is_trained = True
                predictor._build_markov_chain()
                predictor._learn_patterns()
                predictor._init_dynamic_weights()
                
                # 加载或训练模型
                has_cached = predictor.load_state(tag=str(p))
                if not has_cached and train_ensemble and ENSEMBLE_AVAILABLE and len(results) % 10 == 0:
                    predictor._build_stacking_ensemble(train_df)
                    predictor.save_state(tag=str(p))
                
                preds = list(predictor.predict(str(p), n_combinations=20, is_backtest=True))
                if not preds: continue
                
                # 统计数据
                br, bb = 0, 0
                for pr in preds:
                    hr = len(set(act_r) & set(pr['red']))
                    hb = len(set(act_b) & set(pr['blue']))
                    if hr > br or (hr == br and hb > bb): br, bb = hr, hb
                hits_dist[f"R{br}+B{bb}"] += 1
                
                best_pred = preds[0]
                r_hits = len(set(act_r) & set(best_pred['red']))
                b_hits = len(set(act_b) & set(best_pred['blue']))
                total_red_hits += r_hits
                total_blue_hits += b_hits
                
                res_item = {
                    'period': str(p),
                    'actual_red': act_r,
                    'actual_blue': act_b,
                    'predicted_red': best_pred['red'],
                    'predicted_blue': best_pred['blue'],
                    'red_hits': r_hits,
                    'blue_hits': b_hits,
                    'reason': best_pred.get('reason', ''),
                    # 实时统计快照
                    'current_avg_red': round(total_red_hits / (len(results)+1), 2),
                    'current_avg_blue': round(total_blue_hits / (len(results)+1), 2),
                    'current_core_cov': self._calc_temp_coverage(hits_dist, len(results)+1),
                    'current_soft_cov': getattr(self, '_last_soft_coverage', 0)
                }
                results.append(res_item)
                
                # 如果有回调函数，则实时推送
                if on_period_complete:
                    on_period_complete(res_item)
                    
            except Exception as e:
                print(f"Error {p}: {e}")
                
        return {
            'success': True,
            'total_periods': len(results),
            'avg_red_hits': round(total_red_hits / len(results), 2) if results else 0,
            'avg_blue_hits': round(total_blue_hits / len(results), 2) if results else 0,
            'results': results
        }

    def _calc_temp_coverage(self, hits, total):
        if total == 0: return 0
        cov = 0
        soft_cov = 0
        for hit, count in hits.items():
            match = re.search(r'R(\d+)\+B(\d+)', hit)
            if match:
                r = int(match.group(1))
                b = int(match.group(2))
                # 核心覆盖率：4+2 或 5+X
                if (r >= 4 and b >= 2) or (r == 5):
                    cov += count
                # 软覆盖率（统计 3+1, 3+2, 4+0, 4+1 作为进步指标）
                if (r >= 3 and b >= 1) or (r >= 4):
                    soft_cov += count
        
        # 如果核心覆盖率为0，但软覆盖率存在，返回一个带有进度的负值（前端可解析或仅供打印）
        # 这里我们修改打印逻辑，不只是返回数字
        self._last_soft_coverage = (soft_cov / total) * 100
        return (cov / total) * 100

    def _build_markov_chain(self):
        if len(self.history_df) < 2: return
        trans = defaultdict(lambda: defaultdict(int))
        blue_trans = defaultdict(lambda: defaultdict(int))
        for i in range(len(self.history_df)-1):
            # 前区奇偶转移
            c = sum(1 for x in self.history_df.iloc[i]['red'] if x % 2 == 1)
            n = sum(1 for x in self.history_df.iloc[i+1]['red'] if x % 2 == 1)
            trans[c][n] += 1
            
            # 后区和值转移
            bc = sum(self.history_df.iloc[i]['blue'])
            bn = sum(self.history_df.iloc[i+1]['blue'])
            blue_trans[bc][bn] += 1
            
        self.markov_transitions = {
            'odd_even': dict(trans),
            'blue_sum': dict(blue_trans)
        }

    def _learn_patterns(self):
        self.pattern_memory = []
        for _, r in self.history_df.iterrows():
            self.pattern_memory.append({'red_sum': sum(r['red']), 'odd_count': sum(1 for x in r['red'] if x % 2 == 1)})

    def _init_dynamic_weights(self): self.dynamic_weights = {'odd_bias': 1.0}

    def _build_co_occurrence_network(self):
        """构建号码共现网络 - 使用图算法挖掘号码关联"""
        print("[*] 构建号码共现网络...")
        
        # 初始化图：{num1: {num2: weight, ...}, ...}
        graph = {i: {} for i in range(1, 36)}
        
        # 统计号码共现次数
        for _, row in self.history_df.iterrows():
            red = row['red']
            for i in range(len(red)):
                for j in range(i+1, len(red)):
                    n1, n2 = red[i], red[j]
                    graph[n1][n2] = graph[n1].get(n2, 0) + 1
                    graph[n2][n1] = graph[n2].get(n1, 0) + 1
        
        # 归一化权重
        for n1 in graph:
            total = sum(graph[n1].values())
            if total > 0:
                for n2 in graph[n1]:
                    graph[n1][n2] = graph[n1][n2] / total
        
        self.co_occurrence_graph = graph
        print("[*] 共现网络构建完成")

    def _get_network_community_score(self, red_nums):
        """计算号码组合在共现网络中的社区得分"""
        if not self.co_occurrence_graph:
            return 0
        
        score = 0
        for i in range(len(red_nums)):
            for j in range(i+1, len(red_nums)):
                n1, n2 = red_nums[i], red_nums[j]
                # 获取共现权重
                weight = self.co_occurrence_graph.get(n1, {}).get(n2, 0)
                score += weight * 100  # 放大权重
        
        return score

    def _train_blue_lstm(self):
        """训练蓝球专用 LSTM 模型 - 使用原生 Numpy 实现"""
        try:
            print("[*] 训练蓝球 LSTM 模型 (原生 Numpy)...", flush=True)
            
            # 准备序列数据
            sequence_length = 10
            blue_sequences = []
            blue_targets = []
            
            for i in range(sequence_length, len(self.history_df)):
                # 取前 sequence_length 期的蓝球数据
                seq = []
                for j in range(i - sequence_length, i):
                    blue = self.history_df.iloc[j]['blue']
                    encoded = np.zeros(12)
                    for b in blue:
                        encoded[b-1] = 1.0
                    seq.append(encoded)
                blue_sequences.append(seq)
                
                # 目标：当前期的蓝球
                target = np.zeros(12)
                for b in self.history_df.iloc[i]['blue']:
                    target[b-1] = 1.0
                blue_targets.append(target)
            
            if len(blue_sequences) < 20:
                print("  - 数据不足，跳过 LSTM 训练")
                return
            
            # 初始化并训练模型
            model = NumpyLSTM(input_size=12, hidden_size=64, output_size=12)
            model.train(blue_sequences, blue_targets, epochs=50, lr=0.01)
            
            self.blue_lstm_model = model
            self.save_state() # 保存 LSTM 优化成果
            print("[*] 蓝球 LSTM 模型训练完成")
            
        except Exception as e:
            print(f"  - LSTM 训练失败: {e}")
            self.blue_lstm_model = None

    def _predict_blue_with_lstm(self):
        """使用 LSTM 预测蓝球概率 - 原生 Numpy 实现"""
        if not self.blue_lstm_model or len(self.history_df) < 10:
            return {}
        
        try:
            # 准备输入序列
            sequence_length = 10
            seq = []
            for i in range(len(self.history_df) - sequence_length, len(self.history_df)):
                blue = self.history_df.iloc[i]['blue']
                encoded = np.zeros(12)
                for b in blue:
                    encoded[b-1] = 1.0
                seq.append(encoded)
            
            pred = self.blue_lstm_model.predict(seq)
            
            # 返回概率字典
            return {i+1: float(pred[i]) for i in range(12)}
            
        except Exception as e:
            print(f"  - LSTM 预测失败: {e}")
            return {}

    def _adjust_weights_based_on_feedback(self, prediction_results):
        """根据回测反馈动态调整评分权重"""
        if not prediction_results or len(prediction_results) < 5:
            return
        
        print("[*] 根据回测结果调整评分权重...")
        
        # 统计各维度的有效性
        sum_hits = []
        span_hits = []
        odd_even_hits = []
        
        for res in prediction_results:
            if 'hit_info' in res:
                actual_red = res.get('actual_red', [])
                pred_red = res.get('pred_red', [])
                
                # 计算各维度的匹配度
                actual_sum = sum(actual_red)
                pred_sum = sum(pred_red)
                sum_hits.append(1 if abs(actual_sum - pred_sum) <= 15 else 0)
                
                actual_span = actual_red[-1] - actual_red[0] if len(actual_red) == 5 else 0
                pred_span = pred_red[-1] - pred_red[0] if len(pred_red) == 5 else 0
                span_hits.append(1 if abs(actual_span - pred_span) <= 5 else 0)
                
                actual_odd = sum(1 for x in actual_red if x % 2 == 1)
                pred_odd = sum(1 for x in pred_red if x % 2 == 1)
                odd_even_hits.append(1 if actual_odd == pred_odd else 0)
        
        # 计算命中率
        sum_rate = sum(sum_hits) / len(sum_hits) if sum_hits else 0
        span_rate = sum(span_hits) / len(span_hits) if span_hits else 0
        odd_even_rate = sum(odd_even_hits) / len(odd_even_hits) if odd_even_hits else 0
        
        # 调整权重：命中率高的维度增加权重
        self.scoring_weights['sum_weight'] = 0.5 + sum_rate * 1.5
        self.scoring_weights['span_weight'] = 0.5 + span_rate * 1.5
        self.scoring_weights['odd_even_weight'] = 0.5 + odd_even_rate * 1.5
        
        print(f"  - 权重调整: sum={self.scoring_weights['sum_weight']:.2f}, "
              f"span={self.scoring_weights['span_weight']:.2f}, "
              f"odd_even={self.scoring_weights['odd_even_weight']:.2f}")

    def _find_similar_periods(self, current_features, top_k=10):
        """找到与当前特征最相似的历史 Top K 期"""
        if len(self.history_df) < 30:
            return []
        
        recent = self.history_df.tail(200)  # 只在近 200 期中查找
        similarities = []
        
        for idx, row in recent.iterrows():
            red = row['red']
            # 计算多维度相似度
            sim_score = 0
            
            # 1. 和值相似度
            sum_diff = abs(sum(red) - current_features['red_sum'])
            sim_score += max(0, 50 - sum_diff)  # 距离越近分越高
            
            # 2. 奇偶比相似度
            odd_cnt = sum(1 for x in red if x % 2 == 1)
            if odd_cnt == current_features['odd_count']:
                sim_score += 50
            
            # 3. 跨度相似度
            span = red[-1] - red[0]
            span_diff = abs(span - current_features.get('red_span', current_features.get('span', 0)))
            sim_score += max(0, 20 - span_diff)
            
            # 4. 区域分布相似度
            z1_act = sum(1 for x in red if x <= 11)
            z2_act = sum(1 for x in red if 12 <= x <= 23)
            z3_act = sum(1 for x in red if x >= 24)
            
            target_z1 = current_features.get('z1', current_features.get('zone1', 0))
            target_z2 = current_features.get('z2', current_features.get('zone2', 0))
            target_z3 = current_features.get('z3', current_features.get('zone3', 0))
            
            zone_diff = abs(z1_act - target_z1) + abs(z2_act - target_z2) + abs(z3_act - target_z3)
            sim_score += max(0, 10 - zone_diff * 2)
            
            similarities.append({'period': row['period'], 'score': sim_score, 'red': red, 'blue': row['blue']})
        
        # 按相似度排序并取 Top K
        similarities.sort(key=lambda x: x['score'], reverse=True)
        return similarities[:top_k]

    def _get_next_period_numbers(self, period):
        """获取指定期号的下一期实际开奖号码"""
        try:
            idx = self.history_df[self.history_df['period'] == period].index
            if len(idx) > 0 and idx[0] + 1 < len(self.history_df):
                next_row = self.history_df.iloc[idx[0] + 1]
                return {'red': next_row['red'], 'blue': next_row['blue']}
        except:
            pass
        return None

    def _build_actual_numbers_pool(self):
        self.actual_numbers_pool = []
        for _, r in self.history_df.tail(10).iterrows(): self.actual_numbers_pool.extend(r['red'])
        
        # 预计算相关性对
        self.common_pairs = []
        self.common_blue_pairs = []
        if len(self.history_df) >= 50:
            # 前区对
            pairs = Counter()
            for _, row in self.history_df.tail(300).iterrows():
                r = sorted(row['red'])
                for p in combinations(r, 2): pairs[p] += 1
            self.common_pairs = [p for p, c in pairs.most_common(150)]
            
            # 后区对 (蓝球共现)
            b_pairs = Counter()
            for _, row in self.history_df.tail(300).iterrows():
                b = tuple(sorted(row['blue']))
                b_pairs[b] += 1
            self.common_blue_pairs = [b for b, c in b_pairs.most_common(10)]

    def _init_adaptive_weights_from_history(self):
        """基于历史数据初始化动态权重 - 基础占位实现"""
        self.adaptive_weights = {
            'frequency': 1.0,
            'missing': 1.2,
            'pattern': 0.8,
            'actual_weight': 1.0
        }

    def get_model_info(self):
        """返回模型训练状态信息"""
        if not self.is_trained:
            return {'status': '未训练', 'history_count': 0, 'latest_period': 'N/A'}
        
        latest = self.history_df.iloc[-1]
        
        # 统计启用的模型
        enabled_models = []
        enabled_models.append('RandomForest + GradientBoosting')
        
        if self.stacking_meta_model:
            enabled_models.append(f'Stacking (XGBoost+LightGBM+RF) x {len(self.stacking_meta_model)}个号码')
        
        if self.blue_lstm_model:
            enabled_models.append('LSTM 蓝球神经网络')
        
        return {
            'status': '就绪',
            'history_count': len(self.history_df),
            'latest_period': str(latest['period']),
            'last_date': latest['date'],
            'enabled_models': enabled_models
        }

    def get_history_data(self):
        """返回格式化的历史数据列表"""
        if self.history_df is None:
            return []
        
        # 转换为前端需要的格式
        res = []
        for _, row in self.history_df.iterrows():
            res.append({
                'period': str(row['period']),
                'date': row['date'],
                'red': row['red'],
                'blue': row['blue']
            })
        return res
