# 大乐透预测系统 - 功能模块说明书

## 文档版本
- **版本号**: V1.1
- **最后更新**: 2026-01-21
- **维护者**: AI Assistant

---

## 📋 目录
1. [系统概述](#系统概述)
2. [核心功能模块](#核心功能模块)
3. [模型算法体系](#模型算法体系)
4. [过滤条件体系](#过滤条件体系)
5. [评分系统](#评分系统)
6. [模块交互关系](#模块交互关系)

---

## 系统概述

### 系统定位
大乐透智能预测系统，基于历史数据分析、机器学习模型和多维评分体系，为用户提供科学的号码组合预测服务。

### 技术特点
- ✅ **全量枚举评分**：对所有符合条件的号码组合进行逐一评分
- ✅ **多模型融合**：集成 RandomForest、GradientBoosting、LSTM 等模型
- ✅ **实时流式输出**：Server-Sent Events 实现预测结果实时显示
- ✅ **确定性保证**：基于期号的随机种子，确保相同输入产生相同结果
- ✅ **可解释性**：每组预测提供详细选号理由

---

## 核心功能模块

### 1. 开始预测模块

#### 功能描述
为未开奖的下一期大乐透提供智能号码组合预测。

#### 核心流程
```
用户输入参数 → 前置过滤 → 用户过滤 → 全量枚举 → 深度评分 → 多样性过滤 → 输出 Top 20
```

#### 输入参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `period` | string | ✅ | 预测期号（如 "26009"） |
| `kill_red` | array | ❌ | 杀红球号码（1-35） |
| `kill_blue` | array | ❌ | 杀蓝球号码（1-12） |
| `sum_range` | array | ❌ | 和值范围 `[min, max]` |
| `odd_even_ratio` | string | ❌ | 奇偶比（如 "3:2"） |
| `reference_urls` | array | ❌ | 参考网页地址 |

#### 输出结果
```json
{
  "rank": 1,
  "red": [3, 12, 19, 28, 34],
  "blue": [2, 9],
  "score": 1245.67,
  "reason": "和值理想 | 前区全新号 | 模型强力推荐(0.52) | 蓝球1小1大",
  "red_str": "03 12 19 28 34",
  "blue_str": "02 09"
}
```

#### 前置过滤条件（强制）
1. **历史开奖号码**：与上期红球完全相同 → 过滤
2. **四连号**：4个或以上连续号码 → 过滤
3. **等差数列**：公差相同的5个号 → 过滤
4. **等比数列**：比值相同的连续3个号 → 过滤
5. **全奇/全偶**：5个号全奇或全偶 → 过滤
6. **同区号码**：5个号全在 1-11、12-23 或 24-35 → 过滤

#### 用户自定义过滤（可选）
- 杀号过滤
- 和值范围过滤
- 奇偶比过滤
- 重号过滤（前区 ≥3、后区 ≥2）
- 蓝球大小号过滤

---

### 2. 回测验证模块

#### 功能描述
对历史期次进行模拟预测，评估模型准确率和覆盖率。

#### 核心特性
- ⚠️ **不应用任何前置过滤**：模拟真实预测场景
- ⚠️ **不应用用户过滤**：保证回测真实性
- ✅ **流式输出**：每完成一期立即显示结果

#### 输入参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `start_period` | string | ✅ | 起始期号 |
| `end_period` | string | ✅ | 结束期号 |

#### 关键指标
- **平均命中率**：前区平均命中数、后区平均命中数
- **核心覆盖率**：达到 4+2 或 5+X 的期次占比
- **软覆盖率**：达到 3+1、3+2、4+0、4+1 的期次占比
- **命中分布**：R0+B0 ~ R5+B2 的分布统计

#### 输出示例
```json
{
  "period": "25080",
  "actual_red": [5, 12, 19, 28, 34],
  "actual_blue": [3, 9],
  "predicted_red": [3, 12, 19, 27, 34],
  "predicted_blue": [2, 9],
  "red_hits": 3,
  "blue_hits": 1,
  "reason": "模型强力推荐(0.48) | 和值理想 | 前区1个重号",
  "current_avg_red": 2.15,
  "current_avg_blue": 0.87,
  "current_core_cov": 12.5
}
```

---

### 3. 网页参考分析模块

#### 功能描述
从外部预测网页智能提取推荐号码，并融入评分系统。

#### 支持的网站
- 头条网（自动转换移动版）
- 普通 HTML 网页（非 JS 渲染）

#### 提取策略

**三层智能提取**：
1. **结构化数据**（权重 ×3）：表格、列表中的号码
2. **语义上下文分析**（权重 ×1 或 ×2）：
   - 正向关键词：推荐、看好、重点、胆码、精选等
   - 负向关键词：杀号、避开、排除、冷门等
3. **标题重点提取**（权重 ×2）：标题和加粗文字中的号码

#### 噪音过滤
- 自动排除 ≥4 位数字（期号、年份）
- 自动排除 >35 的大数字

#### 评分加成逻辑
```python
# 红球 Top 10 中命中 ≥2 个
ref_boost += (ref_hits * 0.1)  # 每命中1个加 10%

# 蓝球 Top 3 中命中 ≥1 个
ref_boost += 0.1  # 加 10%

# 最终评分
final_score = base_score * ref_boost
```

---

### 4. 历史数据管理模块

#### 数据来源
- **主数据源**：`daletou_history_full.txt`
- **格式要求**：`期号 日期 红球1 红球2 ... 红球5 - 蓝球1 蓝球2`

#### 数据完整性要求
- ✅ 必须包含真实历史开奖数据
- ✅ 数据格式严格遵守规范
- ❌ 禁止使用模拟数据或不完整数据

#### 热力分析
- **热号**：最近 N 期出现频率 ≥ 平均值
- **冷号**：最近 N 期出现频率 < 平均值
- **遗漏期数**：距离最近一次出现的期数
- **超冷号**：遗漏期数 ≥ 10 期

---

### 5. 模型训练模块

#### 集成模型
1. **Stacking 元学习模型**
   - 针对每个号码（1-35 红球、1-12 蓝球）训练独立的二分类模型
   - 基学习器：RandomForestClassifier + GradientBoostingClassifier
   - 元学习器：LogisticRegression

2. **LSTM 时序模型**
   - 专用于蓝球预测
   - 输入：最近 10 期的蓝球出号序列
   - 输出：12 个蓝球的出号概率

3. **号码共现网络**
   - 基于图算法挖掘号码关联
   - PageRank 算法计算号码重要性

#### 特征工程
- **统计特征**：和值、跨度、奇偶比、大小比、区域分布
- **频率特征**：出现频率、遗漏期数、连续出现次数
- **相关特征**：号码共现度、邻号关系、同尾号
- **时序特征**：趋势动量、周期性特征、波动率

---

## 模型算法体系

### 算法总览

系统采用**多层级算法架构**，按照执行顺序依次为：

```
【阶段1：数据准备】
  └─ 历史数据加载算法
  └─ 特征工程算法
  └─ 冷热号统计算法

【阶段2：模型训练】
  └─ Stacking集成学习算法
  └─ LSTM时序预测算法
  └─ 号码共现网络算法

【阶段3：预测生成】
  └─ 确定性种子设置算法
  └─ 网页号码提取算法
  └─ 全量组合枚举算法
  └─ 多级过滤算法
  └─ 多维评分算法
  └─ MMR多样性过滤算法

【阶段4：结果输出】
  └─ 选号理由生成算法
  └─ SSE流式推送算法
```

---

### 1. 数据准备阶段

#### 1.1 历史数据加载算法

**使用时机**：系统启动时、模型训练前

**算法目的**：从文本文件加载历史开奖数据，转换为结构化DataFrame

**算法流程**：
```python
def load_history_data(file_path):
    """
    输入：daletou_history_full.txt
    输出：pandas.DataFrame，包含 period, date, red(list), blue(list)
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 格式：26001 2026-01-01 03 12 19 28 34 - 02 09
            parts = line.strip().split()
            period = parts[0]
            date = parts[1]
            red = [int(x) for x in parts[2:7]]
            blue = [int(x) for x in parts[8:10]]
            data.append({
                'period': period,
                'date': date,
                'red': red,
                'blue': blue
            })
    
    return pd.DataFrame(data)
```

**关键限制**：
- 数据格式必须严格符合规范
- 缺少数据会导致训练失败
- 最少需要100期数据才能有效训练

---

#### 1.2 特征工程算法

**使用时机**：模型训练前、每次预测前

**算法目的**：从历史数据中提取175维特征向量

**特征分类**：

| 特征类别 | 特征数量 | 示例特征 |
|---------|---------|----------|
| **统计特征** | 20维 | 和值、跨度、奇偶比、大小比、区域分布、AC值 |
| **频率特征** | 47维 | 每个号码的出现频率（35红+12蓝） |
| **遗漏特征** | 47维 | 每个号码的遗漏期数 |
| **连续特征** | 47维 | 每个号码的连续出现次数 |
| **时序特征** | 14维 | 趋势动量、周期性、波动率、移动平均 |

**算法核心代码**：
```python
def extract_features(history_df, last_only=True):
    """
    输入：历史数据DataFrame
    输出：特征矩阵 [n_samples, 175]
    """
    features = []
    
    for idx in range(len(history_df)):
        if last_only and idx < len(history_df) - 1:
            continue
        
        # 获取当前期和历史期
        current = history_df.iloc[idx]
        history = history_df.iloc[:idx] if idx > 0 else pd.DataFrame()
        
        feat = {}
        
        # 1. 统计特征
        feat['red_sum'] = sum(current['red'])
        feat['red_span'] = max(current['red']) - min(current['red'])
        feat['red_odd_count'] = sum(1 for x in current['red'] if x % 2 == 1)
        feat['red_big_count'] = sum(1 for x in current['red'] if x > 18)
        
        # AC值计算
        diffs = {abs(current['red'][i] - current['red'][j]) 
                 for i in range(5) for j in range(i+1, 5)}
        feat['ac_value'] = len(diffs) - 4
        
        # 2. 频率特征（每个号码的出现频率）
        if len(history) > 0:
            for num in range(1, 36):
                freq = sum(1 for _, row in history.iterrows() if num in row['red'])
                feat[f'red_{num}_freq'] = freq / len(history)
            
            for num in range(1, 13):
                freq = sum(1 for _, row in history.iterrows() if num in row['blue'])
                feat[f'blue_{num}_freq'] = freq / len(history)
        else:
            # 无历史数据时填充0
            for num in range(1, 36):
                feat[f'red_{num}_freq'] = 0
            for num in range(1, 13):
                feat[f'blue_{num}_freq'] = 0
        
        # 3. 遗漏期数（距离最后一次出现的期数）
        if len(history) > 0:
            for num in range(1, 36):
                missing = 0
                for i in range(len(history)-1, -1, -1):
                    if num in history.iloc[i]['red']:
                        break
                    missing += 1
                feat[f'red_{num}_missing'] = missing
            
            for num in range(1, 13):
                missing = 0
                for i in range(len(history)-1, -1, -1):
                    if num in history.iloc[i]['blue']:
                        break
                    missing += 1
                feat[f'blue_{num}_missing'] = missing
        
        # 4. 时序特征（趋势动量）
        if len(history) >= 10:
            recent_10 = history.tail(10)
            feat['red_sum_trend'] = np.mean([sum(row['red']) for _, row in recent_10.iterrows()])
            feat['red_span_trend'] = np.mean([max(row['red']) - min(row['red']) for _, row in recent_10.iterrows()])
        
        features.append(feat)
    
    return pd.DataFrame(features)
```

**性能优化**：
- 使用缓存机制，避免重复计算（`_cached_feat`）
- 仅计算最后一期特征（`last_only=True`）

---

#### 1.3 冷热号统计算法

**使用时机**：每次预测前

**算法目的**：计算每个号码的冷热程度，用于评分加成

**算法定义**：
```python
def calculate_hot_cold(history_df, window=20):
    """
    输入：历史数据，统计窗口期数（默认20期）
    输出：{'red': {1: 'hot', 2: 'cold', ...}, 'blue': {...}}
    """
    recent = history_df.tail(window)
    
    # 红球冷热统计
    red_freq = {}
    for num in range(1, 36):
        freq = sum(1 for _, row in recent.iterrows() if num in row['red'])
        red_freq[num] = freq
    
    # 计算平均频率
    avg_freq = np.mean(list(red_freq.values()))
    
    # 分类冷热号
    hot_cold = {'red': {}, 'blue': {}}
    for num, freq in red_freq.items():
        if freq >= avg_freq:
            hot_cold['red'][num] = 'hot'
        else:
            hot_cold['red'][num] = 'cold'
        
        # 超冷号：遗漏≥10期
        missing = 0
        for i in range(len(recent)-1, -1, -1):
            if num in recent.iloc[i]['red']:
                break
            missing += 1
        if missing >= 10:
            hot_cold['red'][num] = 'super_cold'
    
    # 蓝球同理
    # ...
    
    return hot_cold
```

**应用场景**：
- 评分系统中的冷热号平衡加分
- 超冷号降权处理

---

### 2. 模型训练阶段

#### 2.1 Stacking集成学习算法

**使用时机**：系统启动时、历史数据更新后

**算法目的**：为每个号码（35红+12蓝）训练独立的二分类模型，预测该号码在下一期出现的概率

**算法架构**：
```
Stacking 元学习
├─ 基学习器层
│  ├─ RandomForestClassifier（n_estimators=100）
│  └─ GradientBoostingClassifier（n_estimators=100）
│
└─ 元学习器层
   └─ LogisticRegression（正则化 C=1.0）
```

**训练流程**：
```python
def train_stacking_models(features_df, history_df):
    """
    输入：特征矩阵 [n_samples, 175]，历史标签
    输出：47个独立的Stacking模型（35红+12蓝）
    """
    models = {}
    
    # 为每个号码训练独立模型
    for num in range(1, 36):  # 红球1-35
        # 构建标签：该号码在下一期是否出现
        y = []
        for idx in range(len(history_df) - 1):
            next_period = history_df.iloc[idx + 1]
            y.append(1 if num in next_period['red'] else 0)
        
        # 去掉最后一期（无下一期标签）
        X = features_df.iloc[:-1]
        
        # 基学习器
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
        
        # Stacking元学习器
        stacking = StackingClassifier(
            estimators=[('rf', rf), ('gb', gb)],
            final_estimator=LogisticRegression(),
            cv=5  # 5折交叉验证
        )
        
        # 训练
        stacking.fit(X, y)
        models[f'red_{num}'] = stacking
    
    # 蓝球同理（1-12）
    # ...
    
    return models
```

**预测使用**：
```python
def predict_with_stacking(models, current_features):
    """
    输入：当前期特征向量 [175]
    输出：{'red': {1: 0.52, 2: 0.31, ...}, 'blue': {1: 0.68, ...}}
    """
    probas = {'red': {}, 'blue': {}}
    
    for num in range(1, 36):
        model = models[f'red_{num}']
        prob = model.predict_proba([current_features])[0][1]  # 取正类概率
        probas['red'][num] = prob
    
    # 蓝球同理
    # ...
    
    return probas
```

**关键限制**：
- 需要至少100期历史数据
- 训练时间：约30-60秒（47个模型）
- 内存占用：约200MB

**何时使用此算法**：
- 评分阶段：获取每个号码的模型推荐置信度
- 高置信度号码（>0.45）获得最高加成（×3.25）

---

#### 2.2 LSTM时序预测算法

**使用时机**：系统启动时（专用于蓝球预测）

**算法目的**：基于历史蓝球出号序列，预测下一期蓝球的出号概率

**算法架构**：
```python
import torch
import torch.nn as nn

class BlueBallLSTM(nn.Module):
    def __init__(self, input_size=12, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 12)  # 输出12个蓝球概率
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # x: [batch_size, seq_len=10, input_size=12]
        lstm_out, _ = self.lstm(x)
        # 取最后一个时间步
        last_out = lstm_out[:, -1, :]
        # 全连接层
        out = self.fc(last_out)
        # Sigmoid激活（概率值）
        return self.sigmoid(out)
```

**训练数据构建**：
```python
def build_lstm_dataset(history_df, seq_len=10):
    """
    输入：历史数据
    输出：X [n_samples, seq_len=10, 12], y [n_samples, 12]
    """
    X, y = [], []
    
    for i in range(seq_len, len(history_df)):
        # 输入：最近10期的蓝球one-hot编码
        seq = []
        for j in range(i - seq_len, i):
            blue_vec = [0] * 12
            for b in history_df.iloc[j]['blue']:
                blue_vec[b - 1] = 1  # one-hot
            seq.append(blue_vec)
        X.append(seq)
        
        # 标签：下一期蓝球的one-hot
        y_vec = [0] * 12
        for b in history_df.iloc[i]['blue']:
            y_vec[b - 1] = 1
        y.append(y_vec)
    
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)
```

**训练过程**：
```python
def train_lstm_model(history_df, epochs=50):
    model = BlueBallLSTM()
    criterion = nn.BCELoss()  # 二元交叉熵
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    X, y = build_lstm_dataset(history_df)
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
    
    return model
```

**预测使用**：
```python
def predict_blue_with_lstm(model, history_df):
    """
    输入：最近10期历史
    输出：{1: 0.68, 2: 0.32, ..., 12: 0.45}
    """
    seq = []
    for i in range(-10, 0):
        blue_vec = [0] * 12
        for b in history_df.iloc[i]['blue']:
            blue_vec[b - 1] = 1
        seq.append(blue_vec)
    
    X = torch.tensor([seq], dtype=torch.float32)
    with torch.no_grad():
        probs = model(X)[0].numpy()
    
    return {i+1: float(probs[i]) for i in range(12)}
```

**何时使用此算法**：
- 评分阶段：蓝球评分时与Stacking模型加权融合（60%Stacking + 40%LSTM）

**关键限制**：
- 需要至少20期历史数据（seq_len=10）
- 训练时间：约5-10秒
- 准确率：蓝球平均命中率约0.8-1.0个

---

#### 2.3 号码共现网络算法

**使用时机**：系统启动时（可选）

**算法目的**：挖掘号码之间的关联关系，辅助评分

**算法流程**：
```python
import networkx as nx

def build_cooccurrence_network(history_df):
    """
    输入：历史数据
    输出：networkx.Graph，节点为号码，边权重为共现次数
    """
    G = nx.Graph()
    
    # 添加节点
    for num in range(1, 36):
        G.add_node(num)
    
    # 添加边（共现关系）
    for _, row in history_df.iterrows():
        red = row['red']
        for i in range(len(red)):
            for j in range(i+1, len(red)):
                if G.has_edge(red[i], red[j]):
                    G[red[i]][red[j]]['weight'] += 1
                else:
                    G.add_edge(red[i], red[j], weight=1)
    
    return G
```

**PageRank算法计算号码重要性**：
```python
def calculate_number_importance(G):
    """
    输入：共现网络图
    输出：{1: 0.025, 2: 0.031, ..., 35: 0.028}
    """
    pagerank = nx.pagerank(G, weight='weight')
    return pagerank
```

**何时使用此算法**：
- 评分阶段：高重要性号码获得加分
- 应用较少，主要用于实验性评分

---

### 3. 预测生成阶段

#### 3.1 确定性种子设置算法

**使用时机**：每次预测开始前（第一步）

**算法目的**：确保相同期号产生相同预测结果

**算法实现**：
```python
def set_deterministic_seed(period):
    """
    输入：期号字符串（如 "26009"）
    输出：无（设置全局随机种子）
    """
    seed = int(period)
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    
    print(f"[*] 设置随机种子: {seed} (基于期号 {period})")
```

**为什么需要这个算法**：
- 模型内部可能使用随机采样（如多样性过滤）
- 评分时可能引入微小随机扰动
- 确保用户多次预测同一期号，结果完全一致

**关键限制**：
- 必须在所有随机操作之前调用
- 必须使用期号作为种子（不能用时间戳）

---

#### 3.2 网页号码提取算法

**使用时机**：用户提供参考网页时

**算法目的**：从预测网页中智能提取推荐号码

**三层提取策略**：

```python
def fetch_reference_numbers(urls):
    """
    输入：网页URL列表
    输出：{'red': {1: 3.5, 2: 1.2, ...}, 'blue': {1: 2.0, ...}}  # 号码→权重
    """
    all_numbers = {'red': {}, 'blue': {}}
    
    for url in urls:
        try:
            # 尝试直接请求
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200 or len(resp.text) < 500:
                # 降级：尝试移动版
                if 'toutiao.com' in url:
                    mobile_url = convert_to_mobile_url(url)
                    resp = requests.get(mobile_url, headers=headers, timeout=15)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # ====== 第一层：结构化数据提取（权重×3）======
            tables = soup.find_all('table')
            for table in tables:
                nums = extract_numbers_from_table(table)
                for num in nums:
                    if 1 <= num <= 35:
                        all_numbers['red'][num] = all_numbers['red'].get(num, 0) + 3.0
                    elif 1 <= num <= 12:
                        all_numbers['blue'][num] = all_numbers['blue'].get(num, 0) + 3.0
            
            # ====== 第二层：语义上下文分析 ======
            positive_keywords = ['推荐', '看好', '重点', '胆码', '精选', '必选']
            negative_keywords = ['杀号', '避开', '排除', '冷门', '不看好']
            
            paragraphs = soup.find_all(['p', 'div', 'span', 'li'])
            for para in paragraphs:
                text = para.get_text()
                
                # 检查上下文
                has_positive = any(kw in text for kw in positive_keywords)
                has_negative = any(kw in text for kw in negative_keywords)
                
                if has_negative:
                    continue  # 跳过负面上下文
                
                weight = 2.0 if has_positive else 1.0
                
                # 提取号码
                nums = extract_numbers_from_text(text)
                for num in nums:
                    if 1 <= num <= 35:
                        all_numbers['red'][num] = all_numbers['red'].get(num, 0) + weight
                    elif 1 <= num <= 12:
                        all_numbers['blue'][num] = all_numbers['blue'].get(num, 0) + weight
            
            # ====== 第三层：标题和加粗文字（权重×2）======
            titles = soup.find_all(['h1', 'h2', 'h3', 'strong', 'b'])
            for title in titles:
                text = title.get_text()
                nums = extract_numbers_from_text(text)
                for num in nums:
                    if 1 <= num <= 35:
                        all_numbers['red'][num] = all_numbers['red'].get(num, 0) + 2.0
                    elif 1 <= num <= 12:
                        all_numbers['blue'][num] = all_numbers['blue'].get(num, 0) + 2.0
        
        except Exception as e:
            print(f"[WARNING] 网页 {url} 提取失败: {e}")
            continue
    
    return all_numbers
```

**噪音过滤规则**：
```python
def extract_numbers_from_text(text):
    """
    输入：文本
    输出：号码列表（已过滤噪音）
    """
    # 正则提取数字
    pattern = r'\b\d+\b'
    matches = re.findall(pattern, text)
    
    filtered = []
    for m in matches:
        num = int(m)
        # 过滤规则：
        # 1. 排除≥4位数（期号、年份）
        if len(m) >= 4:
            continue
        # 2. 排除>35的大数字
        if num > 35:
            continue
        # 3. 排除0
        if num == 0:
            continue
        
        filtered.append(num)
    
    return filtered
```

**何时使用此算法**：
- 评分阶段：红球Top10命中≥2个，每命中1个加10%评分
- 蓝球Top3命中≥1个，加10%评分

**关键限制**：
- 网页动态渲染可能提取失败（尝试移动版降级）
- 提取准确率约70-80%
- 超时设置15秒

---

#### 3.3 全量组合枚举算法

**使用时机**：过滤后、评分前

**算法目的**：生成所有可能的号码组合，边枚举边过滤

**算法实现**：
```python
from itertools import combinations

def enumerate_combinations(avail_red, avail_blue, filters, is_backtest=False):
    """
    输入：
      - avail_red: 可用红球列表（已去除杀号）
      - avail_blue: 可用蓝球列表
      - filters: 过滤条件字典
      - is_backtest: 是否回测模式
    
    输出：生成器，逐一yield符合条件的组合 (red, blue)
    """
    # 生成所有红球组合 C(n, 5)
    all_red_combos = combinations(avail_red, 5)
    all_blue_combos = list(combinations(avail_blue, 2))  # 蓝球组合较少，可以全部生成
    
    total = len(list(combinations(avail_red, 5))) * len(all_blue_combos)
    print(f"[*] 总组合数: {total}")
    
    for red in combinations(avail_red, 5):  # 重新生成（生成器已耗尽）
        red = sorted(red)
        
        # ====== 前置过滤（仅预测模式）======
        if not is_backtest:
            if violates_basic_rules(red, filters):
                continue
        
        # ====== 用户过滤（仅预测模式）======
        if not is_backtest:
            if violates_user_filters(red, filters):
                continue
        
        # 遍历蓝球
        for blue in all_blue_combos:
            blue = sorted(blue)
            
            # 蓝球过滤（仅预测模式）
            if not is_backtest:
                if violates_blue_filters(blue, filters):
                    continue
            
            yield (red, blue)
```

**复杂度分析**：
```
总组合数 = C(n_red, 5) × C(n_blue, 2)

无杀号：C(35, 5) × C(12, 2) = 324,632 × 66 = 21,425,712
杀3红：C(32, 5) × C(12, 2) = 201,376 × 66 = 13,290,816
杀5红2蓝：C(30, 5) × C(10, 2) = 142,506 × 45 = 6,412,770

经前置过滤后：约剩余 40-50%
经用户过滤后：约剩余 25-35%
```

**为什么不一次性生成所有组合**：
- 内存爆炸：2100万组合需要约10GB内存
- 边枚举边过滤：内存占用仅500MB

---

#### 3.4 多级过滤算法

**使用时机**：组合枚举过程中

**算法目的**：快速剔除不符合条件的组合，减少评分计算量

**过滤优先级**：
```
【回测模式】不应用任何过滤

【预测模式】
  ↓
【前置过滤】（强制）
  ├─ 快速检查1：历史开奖号码（set比较，O(1)）
  ├─ 快速检查2：全奇全偶（计数，O(5)）
  ├─ 中速检查3：四连号（循环，O(4)）
  ├─ 中速检查4：等差数列（差值计算，O(4)）
  ├─ 中速检查5：等比数列（比值计算，O(3)）
  └─ 快速检查6：同区号码（分区计数，O(5)）
  ↓
【用户过滤】（可选）
  ├─ 快速检查1：和值范围（求和，O(5)）
  ├─ 快速检查2：奇偶比（计数，O(5)）
  ├─ 中速检查3：重号约束（集合交集，O(5)）
  ├─ 快速检查4：蓝球大小号（计数，O(2)）
  └─ 中速检查5：蓝球重号（集合交集，O(2)）
```

**过滤顺序优化原则**：
1. **快速检查优先**：计算复杂度低的检查放在前面
2. **高淘汰率优先**：淘汰率高的检查放在前面
3. **独立检查优先**：不依赖其他计算结果的检查放在前面

**示例代码**：
```python
def violates_basic_rules(red, filters):
    """
    前置过滤检查
    返回True表示违反规则，应过滤
    """
    # 检查1：历史开奖号码（最快）
    if filters.get('last_red'):
        if set(red) == set(filters['last_red']):
            return True
    
    # 检查2：全奇全偶（最快）
    odd_count = sum(1 for x in red if x % 2 == 1)
    if odd_count == 0 or odd_count == 5:
        return True
    
    # 检查3：四连号
    consecutive_count = 1
    max_consecutive = 1
    for i in range(len(red) - 1):
        if red[i+1] - red[i] == 1:
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 1
    if max_consecutive >= 4:
        return True
    
    # 检查4：等差数列
    diffs = [red[i+1] - red[i] for i in range(len(red)-1)]
    if len(set(diffs)) == 1 and diffs[0] > 0:
        return True
    
    # 检查5：等比数列
    for i in range(len(red) - 2):
        if red[i] > 0 and red[i+1] > 0:
            ratio1 = red[i+1] / red[i]
            ratio2 = red[i+2] / red[i+1]
            if abs(ratio1 - ratio2) < 0.01 and ratio1 > 1:
                return True
    
    # 检查6：同区号码
    zone1 = sum(1 for x in red if 1 <= x <= 11)
    zone2 = sum(1 for x in red if 12 <= x <= 23)
    zone3 = sum(1 for x in red if 24 <= x <= 35)
    if zone1 == 5 or zone2 == 5 or zone3 == 5:
        return True
    
    return False  # 未违反任何规则
```

---

#### 3.5 多维评分算法

**使用时机**：组合通过所有过滤后

**算法目的**：为每个号码组合计算综合得分

**评分公式**：
```
final_score = base_score × red_boost × blue_boost × ref_boost

其中：
- base_score: 基础得分（100-500分）
- red_boost: 红球模型加成（×1.0 - ×4.25）
- blue_boost: 蓝球模型加成（×1.0 - ×3.0）
- ref_boost: 网页参考加成（×1.0 - ×1.5）
```

**详细算法实现**：
```python
def score_combination(red, blue, hot_cold, last, models, ref_numbers):
    """
    输入：
      - red: 红球列表 [5个号码]
      - blue: 蓝球列表 [2个号码]
      - hot_cold: 冷热号统计
      - last: 上期开奖号码
      - models: 机器学习模型
      - ref_numbers: 网页参考号码
    
    输出：综合评分（浮点数）
    """
    score = 0.0
    
    # ========== 第一层：基础统计特征（100-500分）==========
    
    # 1. 和值理想区间
    red_sum = sum(red)
    if 85 <= red_sum <= 115:
        score += 120
    elif 70 <= red_sum <= 130:
        score += 60
    else:
        score -= 50
    
    # 2. 奇偶比
    odd_count = sum(1 for x in red if x % 2 == 1)
    if odd_count in [2, 3]:  # 2:3 或 3:2 最理想
        score += 80
    elif odd_count in [1, 4]:
        score += 30
    
    # 3. 跨度
    span = max(red) - min(red)
    if 22 <= span <= 32:
        score += 100
    elif 18 <= span <= 35:
        score += 50
    
    # 4. 连号惩罚
    consecutive_pairs = sum(1 for i in range(len(red)-1) if red[i+1] - red[i] == 1)
    if consecutive_pairs >= 2:
        score -= 350
    elif consecutive_pairs == 1:
        score += 30  # 适度连号可加分
    
    # 5. AC值（离散度）
    diffs = {abs(red[i] - red[j]) for i in range(5) for j in range(i+1, 5)}
    ac_val = len(diffs) - 4
    if ac_val < 4:
        score -= 500  # 严重惩罚
    elif ac_val >= 7:
        score += 150
    elif ac_val >= 5:
        score += 80
    
    # 6. 012路平衡
    m0 = sum(1 for x in red if x % 3 == 0)
    m1 = sum(1 for x in red if x % 3 == 1)
    m2 = sum(1 for x in red if x % 3 == 2)
    if 1 <= m0 <= 2 and 1 <= m1 <= 2 and 1 <= m2 <= 2:
        score += 150
    
    # 7. 质数分布
    primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
    p_count = sum(1 for x in red if x in primes)
    if 1 <= p_count <= 3:
        score += 100
    elif p_count == 0 or p_count >= 4:
        score -= 50
    
    # ========== 第二层：历史特征匹配（50-100分）==========
    
    # 8. 重号策略
    if last:
        red_overlap = len(set(red) & set(last['red']))
        if red_overlap == 0:
            score += 100  # 全新号
        elif red_overlap == 1:
            score += 50  # 适度重号
        elif red_overlap == 2:
            score += 10  # 允许但不推荐
    
    # 9. 冷热号平衡
    hot_count = sum(1 for x in red if hot_cold['red'].get(x) == 'hot')
    if 2 <= hot_count <= 3:
        score += 80
    
    # 超冷号降权
    super_cold_count = sum(1 for x in red if hot_cold['red'].get(x) == 'super_cold')
    if super_cold_count >= 2:
        score -= 100
    
    # 10. 蓝球大小平衡
    blue_small = sum(1 for b in blue if b <= 6)
    if blue_small == 1:  # 1小1大
        score += 80
    elif blue_small == 0 or blue_small == 2:
        score += 20  # 全大或全小可接受
    
    # ========== 第三层：机器学习模型加成（×1.0 - ×4.25）==========
    
    # 11. Stacking模型红球置信度
    red_probas = [models['stacking']['red'].get(n, 0) for n in red]
    top3_conf = sum(sorted(red_probas, reverse=True)[:3])
    
    if top3_conf > 0.45:
        red_boost = 1.0 + (top3_conf * 5.0)  # 最高3.25x
    elif top3_conf > 0.3:
        red_boost = 1.0 + (top3_conf * 3.0)
    elif top3_conf > 0.2:
        red_boost = 1.0 + (top3_conf * 1.5)
    else:
        red_boost = 1.0
    
    # 12. 蓝球模型融合（Stacking 60% + LSTM 40%）
    blue_probas_stacking = [models['stacking']['blue'].get(b, 0) for b in blue]
    blue_probas_lstm = [models['lstm']['blue'].get(b, 0) for b in blue]
    
    blue_conf = sum([
        p_s * 0.6 + p_l * 0.4
        for p_s, p_l in zip(blue_probas_stacking, blue_probas_lstm)
    ]) / 2
    
    if blue_conf > 0.2:
        blue_boost = 1.0 + (blue_conf * 3.0)
    else:
        blue_boost = 1.0
    
    # ========== 第四层：网页参考加成（×1.0 - ×1.5）==========
    
    ref_boost = 1.0
    if ref_numbers:
        # 红球Top10命中数
        top_red_ref = sorted(ref_numbers['red'].items(), key=lambda x: x[1], reverse=True)[:10]
        top_red_nums = [num for num, _ in top_red_ref]
        ref_hits = len(set(red) & set(top_red_nums))
        
        if ref_hits >= 2:
            ref_boost += (ref_hits * 0.1)
        
        # 蓝球Top3命中数
        top_blue_ref = sorted(ref_numbers['blue'].items(), key=lambda x: x[1], reverse=True)[:3]
        top_blue_nums = [num for num, _ in top_blue_ref]
        if len(set(blue) & set(top_blue_nums)) >= 1:
            ref_boost += 0.1
    
    # ========== 最终得分计算 ==========
    final_score = max(score, 100) * red_boost * blue_boost * ref_boost
    
    return final_score
```

**评分范围**：
```
最低分：100 × 1.0 × 1.0 × 1.0 = 100
典型分：350 × 2.5 × 1.8 × 1.2 = 1890
最高分：500 × 4.25 × 3.0 × 1.5 = 9562
```

---

#### 3.6 MMR多样性过滤算法

**使用时机**：评分完成后、输出前

**算法目的**：避免输出的Top20组合过于相似（如前区相同4个号）

**算法原理**：Maximum Marginal Relevance（最大边际相关性）

```python
def apply_mmr_diversity_filter(scored_combos, n=20, similarity_threshold=4):
    """
    输入：
      - scored_combos: 已排序的组合列表 [{red, blue, score}, ...]
      - n: 最终输出数量
      - similarity_threshold: 相似度阈值（红球重叠数）
    
    输出：多样化的Top N组合
    """
    final_results = []
    
    for combo in scored_combos:
        if len(final_results) >= n:
            break
        
        # 检查与已选组合的相似度
        is_too_similar = False
        for selected in final_results:
            overlap = len(set(combo['red']) & set(selected['red']))
            if overlap >= similarity_threshold:
                is_too_similar = True
                break
        
        # 不相似则加入结果集
        if not is_too_similar:
            final_results.append(combo)
    
    # 如果不够n个，补充高分组合（放宽相似度要求）
    if len(final_results) < n:
        for combo in scored_combos:
            if len(final_results) >= n:
                break
            if combo not in final_results:
                final_results.append(combo)
    
    return final_results
```

**示例**：
```
评分Top5（按分数排序）：
1. [03, 12, 19, 28, 34] + [02, 09] - 1890分
2. [03, 12, 19, 27, 34] + [02, 09] - 1850分  ← 与#1重叠4个，过滤
3. [05, 11, 18, 26, 33] + [04, 10] - 1820分  ← 与#1重叠0个，保留
4. [03, 12, 20, 28, 34] + [02, 09] - 1800分  ← 与#1重叠4个，过滤
5. [07, 14, 22, 29, 35] + [03, 11] - 1780分  ← 与#1重叠0个，保留

最终输出：#1, #3, #5
```

**何时放宽相似度阈值**：
- 如果相似度阈值=4 无法凑够20组，降低到3
- 仍不够，则直接补充高分组合（不再检查相似度）

---

### 4. 结果输出阶段

#### 4.1 选号理由生成算法

**使用时机**：最终输出前

**算法目的**：为每组预测生成可解释的选号理由

**算法实现**：
```python
def generate_reason(red, blue, score, models, ref_numbers, last):
    """
    输入：号码组合、评分、模型、参考号码、上期
    输出：理由字符串
    """
    reasons = []
    
    # 1. 和值理由
    red_sum = sum(red)
    if 85 <= red_sum <= 115:
        reasons.append("和值理想")
    elif 70 <= red_sum <= 130:
        reasons.append(f"和值{red_sum}")
    
    # 2. 重号理由
    if last:
        overlap = len(set(red) & set(last['red']))
        if overlap == 0:
            reasons.append("前区全新号")
        elif overlap == 1:
            reasons.append("前区1个重号")
        elif overlap == 2:
            reasons.append("前区2个重号")
    
    # 3. 模型置信度
    red_probas = [models['stacking']['red'].get(n, 0) for n in red]
    top3_conf = sum(sorted(red_probas, reverse=True)[:3])
    if top3_conf > 0.45:
        reasons.append(f"模型强力推荐({top3_conf:.2f})")
    elif top3_conf > 0.3:
        reasons.append(f"模型推荐({top3_conf:.2f})")
    
    # 4. 蓝球策略
    blue_small = sum(1 for b in blue if b <= 6)
    if blue_small == 1:
        reasons.append("蓝球1小1大")
    elif blue_small == 0:
        reasons.append("蓝球全大")
    else:
        reasons.append("蓝球全小")
    
    # 5. 网页参考
    if ref_numbers:
        top_red_ref = sorted(ref_numbers['red'].items(), key=lambda x: x[1], reverse=True)[:10]
        ref_hits = len(set(red) & set([n for n, _ in top_red_ref]))
        if ref_hits >= 2:
            reasons.append(f"参考网页命中{ref_hits}号")
    
    return " | ".join(reasons)
```

**输出示例**：
```
"和值理想 | 前区全新号 | 模型强力推荐(0.52) | 蓝球1小1大 | 参考网页命中3号"
```

---

#### 4.2 SSE流式推送算法

**使用时机**：输出阶段

**算法目的**：将预测结果实时推送到前端，提升用户体验

**算法实现**：
```python
def predict_with_streaming(period, filters):
    """
    Generator函数，逐一yield预测结果
    """
    # 进度消息
    yield {"type": "progress", "message": "正在加载历史数据..."}
    
    # 加载数据
    history_df = load_history_data()
    
    yield {"type": "progress", "message": "正在训练模型..."}
    
    # 训练模型
    models = train_models(history_df)
    
    yield {"type": "progress", "message": f"设置随机种子: {period}"}
    
    set_deterministic_seed(period)
    
    # 枚举评分
    scored_combos = []
    count = 0
    for red, blue in enumerate_combinations(...):
        score = score_combination(red, blue, ...)
        scored_combos.append({'red': red, 'blue': blue, 'score': score})
        
        count += 1
        if count % 10000 == 0:
            yield {"type": "progress", "message": f"已评分: {count} 组..."}
    
    # 排序
    scored_combos.sort(key=lambda x: x['score'], reverse=True)
    
    # 多样性过滤
    final = apply_mmr_diversity_filter(scored_combos, n=20)
    
    # 输出结果
    for i, combo in enumerate(final):
        reason = generate_reason(combo['red'], combo['blue'], ...)
        
        yield {
            "type": "result",
            "data": {
                "rank": i + 1,
                "red": combo['red'],
                "blue": combo['blue'],
                "score": round(combo['score'], 2),
                "reason": reason,
                "red_str": ' '.join([f'{x:02d}' for x in combo['red']]),
                "blue_str": ' '.join([f'{x:02d}' for x in combo['blue']])
            }
        }
        
        time.sleep(0.5)  # 控制推送频率
    
    yield {"type": "complete", "message": "预测完成"}
```

**Flask路由集成**：
```python
@app.route('/api/predict', methods=['POST'])
def predict_api():
    data = request.json
    
    def generate():
        for item in model.predict_with_streaming(data['period'], data):
            yield f"data: {json.dumps(item)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
```

---

### 算法使用决策树

```
用户发起预测请求
  │
  ├─ 是否回测模式？
  │   ├─ 是 → 跳过所有过滤算法，直接全量评分
  │   └─ 否 → 继续
  │
  ├─ 1. 设置确定性种子（基于期号）
  │
  ├─ 2. 是否提供参考网页？
  │   ├─ 是 → 执行网页号码提取算法
  │   └─ 否 → 跳过
  │
  ├─ 3. 执行全量组合枚举算法
  │   │
  │   ├─ 3.1 应用前置过滤算法（强制）
  │   │     ├─ 历史开奖号码检查
  │   │     ├─ 四连号检查
  │   │     ├─ 等差数列检查
  │   │     ├─ 等比数列检查
  │   │     ├─ 全奇全偶检查
  │   │     └─ 同区号码检查
  │   │
  │   ├─ 3.2 应用用户过滤算法（可选）
  │   │     ├─ 和值范围检查
  │   │     ├─ 奇偶比检查
  │   │     ├─ 重号约束检查
  │   │     └─ 蓝球约束检查
  │   │
  │   └─ 3.3 执行多维评分算法
  │         ├─ 基础统计特征评分
  │         ├─ 历史特征匹配评分
  │         ├─ Stacking模型加成
  │         ├─ LSTM模型加成
  │         └─ 网页参考加成
  │
  ├─ 4. 排序（按分数降序）
  │
  ├─ 5. 执行MMR多样性过滤算法
  │   ├─ 相似度阈值=4
  │   ├─ 不够20组？降低到3
  │   └─ 仍不够？直接补充
  │
  ├─ 6. 执行选号理由生成算法
  │
  └─ 7. 执行SSE流式推送算法
```

---

### 算法性能对比

| 算法 | 时间复杂度 | 空间复杂度 | 执行耗时 | 瓶颈 |
|------|-----------|-----------|---------|------|
| 历史数据加载 | O(n) | O(n) | <1秒 | 文件I/O |
| 特征工程 | O(n×m) | O(n×175) | 5-10秒 | 循环计算 |
| Stacking训练 | O(n×m×k) | O(47×模型) | 30-60秒 | 模型训练 |
| LSTM训练 | O(n×seq×h) | O(模型参数) | 5-10秒 | 反向传播 |
| 全量枚举 | O(C(n,5)×C(m,2)) | O(1) | 10-30秒 | 组合数量 |
| 多维评分 | O(p) | O(p) | 10-30秒 | 评分计算 |
| MMR过滤 | O(p×n) | O(n) | <1秒 | 相似度计算 |

**总预测耗时**：约60-120秒（含训练）

**优化后预测耗时**：约10-30秒（模型缓存）

---

## 过滤条件体系

### 过滤条件分类

| 类别 | 应用场景 | 是否可选 |
|------|---------|---------|
| **前置过滤** | 预测/导出 | ❌ 强制 |
| **用户过滤** | 预测/导出 | ✅ 可选 |
| **回测过滤** | 回测验证 | ❌ 不应用 |

### 前置过滤详解

#### 1. 历史开奖号码过滤
```python
if set(red) == set(last['red']):
    continue  # 完全相同的红球组合直接过滤
```

#### 2. 四连号过滤
```python
# 示例：01 02 03 04 05 → 5连号 → 过滤
# 示例：05 06 07 08 12 → 4连号 → 过滤
# 示例：01 03 05 07 09 → 无连号 → 通过
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
```

#### 3. 等差数列过滤
```python
# 示例：02 07 12 17 22 → 公差5 → 过滤
# 示例：01 04 07 10 13 → 公差3 → 过滤
# 示例：05 12 19 28 34 → 不等差 → 通过
diffs = [red[i+1] - red[i] for i in range(len(red)-1)]
if len(set(diffs)) == 1 and diffs[0] > 0:
    continue  # 所有间隔相同
```

#### 4. 等比数列过滤
```python
# 示例：01 02 04 08 16 → 公比2 → 过滤
# 示例：03 06 12 24 35 → 公比2 → 过滤
# 示例：05 12 19 28 34 → 不等比 → 通过
for i in range(len(red) - 2):
    if red[i] > 0 and red[i+1] > 0:
        ratio1 = red[i+1] / red[i]
        ratio2 = red[i+2] / red[i+1]
        if abs(ratio1 - ratio2) < 0.01 and ratio1 > 1:
            is_geometric = True
            break
```

#### 5. 全奇/全偶过滤
```python
odd_count = sum(1 for x in red if x % 2 == 1)
if odd_count == 0 or odd_count == 5:
    continue  # 全奇或全偶直接过滤
```

#### 6. 同区号码过滤
```python
# 区域定义：
# 一区：01-11
# 二区：12-23
# 三区：24-35
zone1 = sum(1 for x in red if 1 <= x <= 11)
zone2 = sum(1 for x in red if 12 <= x <= 23)
zone3 = sum(1 for x in red if 24 <= x <= 35)
if zone1 == 5 or zone2 == 5 or zone3 == 5:
    continue  # 5个号全在同一区
```

---

## 评分系统

### 评分维度

#### 1. 基础统计特征（100-500分）

**连号惩罚**：
```python
consecutive_pairs = sum(1 for i in range(len(red)-1) if red[i+1] - red[i] == 1)
if consecutive_pairs >= 2:
    score -= 350
```

**AC值校验**：
```python
diffs = {abs(red[i] - red[j]) for i in range(5) for j in range(i+1, 5)}
ac_val = len(diffs) - 4
if ac_val < 4:
    score -= 500
```

**012路平衡**：
```python
m0 = sum(1 for x in red if x % 3 == 0)
m1 = sum(1 for x in red if x % 3 == 1)
m2 = sum(1 for x in red if x % 3 == 2)
if m0 >= 4 or m1 >= 4 or m2 >= 4:
    score += 150
```

**质数分布**：
```python
primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
p_count = sum(1 for x in red if x in primes)
if 1 <= p_count <= 3:
    score += 100
```

#### 2. 历史特征匹配（50-100分）

**和值理想区间**：
```python
if 85 <= red_sum <= 115:
    score += 120
```

**重号策略**：
```python
red_overlap = len(set(red) & set(last['red']))
if red_overlap == 1:
    score += 50  # 适度重号
elif red_overlap == 0:
    score += 100  # 全新号
```

**蓝球大小平衡**：
```python
blue_small = sum(1 for b in blue if b <= 6)
if blue_small == 1:  # 1小1大
    score += 80
```

#### 3. 机器学习置信度（倍乘 1.0-4.25）

**红球 Stacking 加成**：
```python
p_vals = sorted([red_probas.get(n, 0) for n in red], reverse=True)
top3_sum = sum(p_vals[:3])

if top3_sum > 0.45:
    red_stacking_boost = 1.0 + (top3_sum * 5.0)  # 最高 3.25x
elif top3_sum > 0.3:
    red_stacking_boost = 1.0 + (top3_sum * 3.0)
elif top3_sum > 0.2:
    red_stacking_boost = 1.0 + (top3_sum * 1.5)
```

**蓝球热力加成**：
```python
b_avg_conf = sum([
    blue_probas.get(b, 0) * 0.6 + lstm_probas.get(b, 0) * 0.4
    for b in blue
])
if b_avg_conf > 0.2:
    blue_boost = 1.0 + (b_avg_conf * 3.0)
```

#### 4. 网页参考加成（倍乘 1.0-1.5）

```python
ref_hits = len(set(red) & set(top_red_ref))
if ref_hits >= 2:
    ref_boost += (ref_hits * 0.1)
```

### 最终评分公式

```python
final_score = base_score * red_stacking_boost * blue_boost * ref_boost
```

---

## 模块交互关系

### 数据流图

```
┌─────────────────┐
│  历史数据加载   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  模型训练初始化 │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌─────────────────┐
│  用户发起预测   │─────→│  网页参考分析   │
└────────┬────────┘      └────────┬────────┘
         │                        │
         ↓                        │
┌─────────────────┐              │
│  前置条件过滤   │              │
└────────┬────────┘              │
         │                        │
         ↓                        │
┌─────────────────┐              │
│  用户条件过滤   │              │
└────────┬────────┘              │
         │                        │
         ↓                        ↓
┌─────────────────────────────────┐
│     全量枚举 + 深度评分         │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────┐
│  多样性过滤MMR  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  流式输出结果   │
└─────────────────┘
```

### 模块调用关系

| 调用方 | 被调用方 | 调用目的 |
|--------|---------|---------|
| `app.py` | `DaletouPredictor.train()` | 训练模型 |
| `app.py` | `DaletouPredictor.predict()` | 生成预测 |
| `app.py` | `DaletouPredictor.validate_model()` | 回测验证 |
| `predict()` | `_fetch_reference_numbers()` | 网页分析 |
| `predict()` | `generate_candidates()` | 候选生成 |
| `predict()` | `score_combination()` | 组合评分 |
| `score_combination()` | `_predict_with_stacking()` | 模型推荐 |
| `score_combination()` | `_predict_blue_with_lstm()` | LSTM预测 |

---

## 附录

### 术语表

| 术语 | 解释 |
|------|------|
| **前区** | 大乐透的5个红球（1-35） |
| **后区** | 大乐透的2个蓝球（1-12） |
| **AC值** | 号码组合的离散度指标，AC = (差值集合大小) - 4 |
| **012路** | 号码除以3的余数分类：0路、1路、2路 |
| **MMR** | Maximum Marginal Relevance，最大边际相关性算法 |
| **SSE** | Server-Sent Events，服务器推送事件 |
| **Stacking** | 集成学习的一种方法，通过元学习器组合多个基学习器 |

### 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| V1.1 | 2026-01-21 | 新增《模型算法体系》章节，详细说明12个核心算法的使用时机、目的、流程、限制 |
| V1.0 | 2026-01-21 | 初始版本，完整功能模块说明 |

---

**文档结束**
