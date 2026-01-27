# 大乐透预测系统 - 开发规范文档

## 文档版本
- **版本号**: V1.0
- **最后更新**: 2026-01-21
- **维护者**: AI Assistant

---

## 📋 目录
1. [代码规范](#代码规范)
2. [过滤条件规范](#过滤条件规范)
3. [测试规范](#测试规范)
4. [Git规范](#git规范)
5. [文档规范](#文档规范)

---

## 代码规范

### 1. Python 编码规范

#### PEP 8 基本要求

**缩进**：
```python
# ✅ 正确：使用4个空格
def predict(period, filters):
    if period:
        return result

# ❌ 错误：使用Tab或2个空格
def predict(period, filters):
  if period:
    return result
```

**行长度**：
```python
# ✅ 正确：每行不超过120个字符
def score_combination(red, blue, history, models,
                      reference_numbers=None, cancel_check=None):
    pass

# ❌ 错误：单行过长
def score_combination(red, blue, history, models, reference_numbers=None, cancel_check=None, additional_param=None):
    pass
```

**命名规范**：
```python
# ✅ 正确
class DaletouPredictor:  # 类名：大驼峰
    def predict_numbers(self, period):  # 方法名：小写+下划线
        max_score = 0  # 变量名：小写+下划线
        RED_BALL_COUNT = 5  # 常量：大写+下划线

# ❌ 错误
class daletouPredictor:  # 类名错误
    def PredictNumbers(self, period):  # 方法名错误
        MaxScore = 0  # 变量名错误
```

---

### 2. 禁止使用中文标点符号

**⚠️ 严格禁止**：

```python
# ❌ 错误：使用中文标点
if red_overlap >= 2：  # 中文冒号
    continue

result = {'red': red，'blue': blue}  # 中文逗号

# ✅ 正确：使用英文标点
if red_overlap >= 2:  # 英文冒号
    continue

result = {'red': red, 'blue': blue}  # 英文逗号
```

**常见中文标点错误**：

| 中文标点 | Unicode | 英文标点 | Unicode |
|---------|---------|---------|---------|
| ， | U+FF0C | , | U+002C |
| ： | U+FF1A | : | U+003A |
| ； | U+FF1B | ; | U+003B |
| （ | U+FF08 | ( | U+0028 |
| ） | U+FF09 | ) | U+0029 |
| " | U+201C | " | U+0022 |
| " | U+201D | " | U+0022 |

---

### 3. 注释规范

#### 函数注释

```python
def predict(self, period, n_combinations=20, kill_red=None, kill_blue=None,
            sum_range=None, odd_even_ratio=None, is_backtest=False):
    """生成预测 - V8 全量架构重构版（枚举所有符合条件的组合）
    
    Args:
        period (str): 预测期号，5位数字
        n_combinations (int): 输出组合数量，默认20
        kill_red (list): 杀红球号码列表，1-35
        kill_blue (list): 杀蓝球号码列表，1-12
        sum_range (tuple): 和值范围 (min, max)
        odd_even_ratio (str): 奇偶比，格式 "3:2"
        is_backtest (bool): 是否为回测模式
    
    Returns:
        Generator: 流式输出预测结果，每个结果为字典
            {
                'rank': 排名,
                'red': 红球列表,
                'blue': 蓝球列表,
                'score': 评分,
                'reason': 选号理由
            }
    
    Raises:
        ValueError: 当模型未训练时抛出
    
    Examples:
        >>> for result in model.predict('26009', n_combinations=10):
        ...     print(result['red'], result['blue'])
    """
    pass
```

#### 关键逻辑注释

```python
# ====== 仅在预测/导出模式下的基础过滤条件 ======
if not is_backtest:
    # 0. 历史开奖号码过滤（完全相同的红球组合）
    if last is not None:
        if set(red) == set(last['red']):
            continue
    
    # 1. 全奇全偶过滤
    odd_count = sum(1 for x in red if x % 2 == 1)
    if odd_count == 0 or odd_count == 5:
        continue
```

---

### 4. 异常处理规范

#### 明确异常类型

```python
# ✅ 正确：捕获明确的异常
try:
    model.train(history_df)
except FileNotFoundError as e:
    logger.error(f"数据文件不存在: {e}")
    raise
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
    raise

# ❌ 错误：捕获所有异常
try:
    model.train(history_df)
except Exception as e:
    pass  # 静默吞掉所有异常
```

#### 异常链传递

```python
# ✅ 正确：保留异常链
try:
    result = predict(period)
except ModelNotTrained as e:
    raise PredictionError(f"预测失败: 模型未训练") from e

# ❌ 错误：丢失原始异常信息
try:
    result = predict(period)
except ModelNotTrained:
    raise PredictionError("预测失败")
```

---

### 5. 日志规范

#### 日志级别

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: 调试信息
logger.debug(f"当前组合: {red} + {blue}, 得分: {score}")

# INFO: 关键流程信息
logger.info(f"开始预测期号 {period}")

# WARNING: 警告信息
logger.warning(f"网页 {url} 访问失败，尝试降级方案")

# ERROR: 错误信息
logger.error(f"模型训练失败: {e}", exc_info=True)

# CRITICAL: 严重错误
logger.critical(f"系统崩溃: {e}", exc_info=True)
```

#### 日志格式

```python
# ✅ 正确：结构化日志
logger.info(f"[预测] 期号={period}, 杀号={kill_red}, 耗时={elapsed:.2f}s")

# ❌ 错误：无结构日志
logger.info("预测完成")
```

---

## 过滤条件规范

### 1. 前置过滤条件（强制）

**适用场景**：预测/导出模式（`is_backtest=False`）

**不适用场景**：回测模式（`is_backtest=True`）

#### 实现模板

```python
if not is_backtest:
    # 0. 历史开奖号码过滤
    if last is not None:
        if set(red) == set(last['red']):
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
    if len(red) >= 3:
        diffs = [red[i+1] - red[i] for i in range(len(red)-1)]
        if len(set(diffs)) == 1 and diffs[0] > 0:
            continue
    
    # 4. 等比数列过滤（比值相同的连续3个号）
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
    
    # 5. 同区号码过滤（5个号全在同一区间）
    zone1 = sum(1 for x in red if 1 <= x <= 11)
    zone2 = sum(1 for x in red if 12 <= x <= 23)
    zone3 = sum(1 for x in red if 24 <= x <= 35)
    if zone1 == 5 or zone2 == 5 or zone3 == 5:
        continue
```

---

### 2. 用户自定义过滤（可选）

**适用场景**：预测/导出模式（`is_backtest=False`）

**不适用场景**：回测模式（`is_backtest=True`）

#### 实现模板

```python
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
        except:
            pass
    
    # 检查重号（前区 >= 3个重号过滤）
    if last is not None:
        red_overlap = len(set(red) & set(last['red']))
        if red_overlap >= 3:
            continue
    
    # 蓝球约束：不允许全大或全小
    blue_small_count = sum(1 for b in blue if b <= 6)
    if blue_small_count == 0 or blue_small_count == 2:
        continue
    
    # 蓝球重号（>= 2个重号过滤）
    if last is not None:
        blue_overlap = len(set(blue) & set(last['blue']))
        if blue_overlap >= 2:
            continue
```

---

### 3. 过滤条件优先级

```
1. 前置过滤条件（强制，不可绕过）
   ├─ 历史开奖号码
   ├─ 四连号
   ├─ 等差数列
   ├─ 等比数列
   ├─ 全奇全偶
   └─ 同区号码
   
2. 用户自定义过滤（可选）
   ├─ 杀号
   ├─ 和值范围
   ├─ 奇偶比
   ├─ 重号约束
   └─ 蓝球大小号
```

---

## 测试规范

### 1. 单元测试

#### 测试文件命名

```
test_<模块名>.py
```

#### 测试用例命名

```python
def test_<功能描述>_<场景描述>():
    pass

# 示例
def test_predict_with_kill_red():
    """测试带杀号的预测功能"""
    pass

def test_backtest_without_filters():
    """测试回测功能不应用过滤条件"""
    pass
```

#### 测试用例模板

```python
import unittest
from model_engine import DaletouPredictor

class TestDaletouPredictor(unittest.TestCase):
    
    def setUp(self):
        """每个测试前的初始化"""
        self.predictor = DaletouPredictor()
        self.predictor.train()
    
    def tearDown(self):
        """每个测试后的清理"""
        pass
    
    def test_predict_determinism(self):
        """测试预测确定性：相同输入应产生相同输出"""
        # Arrange
        period = '26009'
        
        # Act
        result1 = list(self.predictor.predict(period, n_combinations=5))
        result2 = list(self.predictor.predict(period, n_combinations=5))
        
        # Assert
        self.assertEqual(result1[0]['red'], result2[0]['red'])
        self.assertEqual(result1[0]['blue'], result2[0]['blue'])
    
    def test_backtest_no_filters(self):
        """测试回测模式不应用过滤条件"""
        # Arrange
        period = '25001'
        
        # Act
        result = list(self.predictor.predict(
            period, 
            is_backtest=True,
            kill_red=[1, 2, 3],  # 回测模式应忽略杀号
            sum_range=[80, 120]   # 回测模式应忽略和值范围
        ))
        
        # Assert
        # 验证杀号没有被应用（结果中可能包含1, 2, 3）
        all_reds = set()
        for r in result:
            all_reds.update(r['red'])
        self.assertTrue(1 in all_reds or 2 in all_reds or 3 in all_reds)

if __name__ == '__main__':
    unittest.main()
```

---

### 2. 集成测试

#### 测试场景

```python
def test_full_prediction_flow():
    """测试完整预测流程"""
    # 1. 加载历史数据
    # 2. 训练模型
    # 3. 发起预测
    # 4. 验证结果格式
    # 5. 验证过滤条件生效
    pass

def test_backtest_flow():
    """测试完整回测流程"""
    # 1. 加载历史数据
    # 2. 训练模型
    # 3. 执行回测
    # 4. 验证命中率计算
    # 5. 验证不应用过滤条件
    pass
```

---

### 3. 性能测试

```python
import time

def test_prediction_performance():
    """测试预测性能"""
    predictor = DaletouPredictor()
    predictor.train()
    
    start = time.time()
    result = list(predictor.predict('26009', n_combinations=20))
    elapsed = time.time() - start
    
    # 断言：预测耗时应小于60秒
    assert elapsed < 60, f"预测耗时 {elapsed:.2f}s 超过60秒"
    
    # 断言：应返回20组结果
    assert len(result) == 20, f"预期20组结果，实际 {len(result)} 组"
```

---

## Git规范

### 1. 分支管理

```
main (生产分支)
  ├─ develop (开发分支)
      ├─ feature/prediction-filter (功能分支)
      ├─ feature/backtest-upgrade (功能分支)
      ├─ bugfix/filter-bug (修复分支)
      └─ hotfix/urgent-fix (紧急修复分支)
```

### 2. Commit 规范

#### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(predict): 添加等比数列过滤` |
| `fix` | Bug修复 | `fix(filter): 修复四连号过滤逻辑错误` |
| `docs` | 文档更新 | `docs(api): 更新API文档` |
| `refactor` | 代码重构 | `refactor(score): 优化评分算法` |
| `perf` | 性能优化 | `perf(cache): 添加特征计算缓存` |
| `test` | 测试相关 | `test(predict): 添加确定性测试` |
| `chore` | 构建/工具 | `chore(deps): 升级依赖版本` |

#### 示例

```bash
git commit -m "feat(filter): 实现等比数列过滤功能

- 检查连续3个号码是否构成等比数列
- 公比相同且大于1时过滤
- 仅在预测/导出模式下生效

Closes #123"
```

---

## 文档规范

### 1. 文档分类

| 文档类型 | 文件名 | 用途 |
|---------|--------|------|
| 功能模块说明 | `SYSTEM_MODULES.md` | 功能模块详细说明 |
| 系统设计文档 | `DESIGN_DOCUMENT.md` | 架构、算法设计 |
| API接口文档 | `API_REFERENCE.md` | 接口定义、参数说明 |
| 开发规范 | `DEVELOPMENT_GUIDE.md` | 代码、测试规范 |
| 更新日志 | `CHANGELOG.md` | 版本更新记录 |

### 2. 文档格式

#### Markdown 规范

```markdown
# 一级标题（文档标题）

## 二级标题（章节）

### 三级标题（小节）

#### 四级标题（细节）

**加粗文本**

*斜体文本*

`行内代码`

> 引用块

- 无序列表
- 无序列表

1. 有序列表
2. 有序列表

| 表头1 | 表头2 |
|-------|-------|
| 内容1 | 内容2 |
```

### 3. 文档更新

每次文档更新需要：
1. ✅ 更新文档版本号
2. ✅ 更新"最后更新"日期
3. ✅ 在"更新日志"中记录变更

---

## 附录

### 开发工具推荐

| 工具 | 用途 | 推荐指数 |
|------|------|---------|
| PyCharm | Python IDE | ⭐⭐⭐⭐⭐ |
| VS Code | 轻量级编辑器 | ⭐⭐⭐⭐⭐ |
| Black | 代码格式化 | ⭐⭐⭐⭐ |
| Flake8 | 代码检查 | ⭐⭐⭐⭐ |
| pytest | 单元测试 | ⭐⭐⭐⭐⭐ |

### 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| V1.0 | 2026-01-21 | 初始版本，完整开发规范文档 |

---

**文档结束**
