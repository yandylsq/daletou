# 大乐透预测系统 - API接口文档

## 文档版本
- **版本号**: V1.0
- **最后更新**: 2026-01-21
- **维护者**: AI Assistant

---

## 📋 目录
1. [接口概述](#接口概述)
2. [通用说明](#通用说明)
3. [预测接口](#预测接口)
4. [回测接口](#回测接口)
5. [历史查询接口](#历史查询接口)
6. [错误码定义](#错误码定义)

---

## 接口概述

### 基础信息

| 项目 | 内容 |
|------|------|
| **Base URL** | `http://localhost:5000` |
| **协议** | HTTP/1.1 + SSE |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |
| **超时设置** | 60 秒 |

### 接口清单

| 序号 | 接口路径 | 方法 | 功能 | 响应类型 |
|------|---------|------|------|---------|
| 1 | `/api/predict` | POST | 开始预测 | SSE 流式 |
| 2 | `/api/backtest` | POST | 回测验证 | SSE 流式 |
| 3 | `/api/history` | GET | 历史开奖查询 | JSON |
| 4 | `/api/cancel/<task_id>` | POST | 取消任务 | JSON |

---

## 通用说明

### 请求头

```http
Content-Type: application/json
Accept: text/event-stream
```

### 响应头（SSE）

```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### SSE 数据格式

```
data: {"key": "value"}\n\n
```

### 错误响应格式

```json
{
  "error": "错误描述",
  "code": "ERROR_CODE",
  "details": "详细错误信息（可选）"
}
```

---

## 预测接口

### 1. 开始预测

#### 接口信息
- **路径**: `/api/predict`
- **方法**: `POST`
- **功能**: 为指定期号生成号码预测
- **响应**: SSE 流式输出

#### 请求参数

```json
{
  "period": "26009",
  "kill_red": [1, 2, 35],
  "kill_blue": [1, 12],
  "sum_range": [80, 120],
  "odd_even_ratio": "3:2",
  "reference_urls": [
    "https://www.toutiao.com/article/7448123456789/",
    "https://example.com/prediction"
  ]
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `period` | string | ✅ | 预测期号，5位数字 | `"26009"` |
| `kill_red` | array | ❌ | 杀红球号码，1-35 | `[1, 2, 35]` |
| `kill_blue` | array | ❌ | 杀蓝球号码，1-12 | `[1, 12]` |
| `sum_range` | array | ❌ | 和值范围 `[min, max]` | `[80, 120]` |
| `odd_even_ratio` | string | ❌ | 奇偶比，格式 `"奇:偶"` | `"3:2"` 或 `"2:3"` |
| `reference_urls` | array | ❌ | 参考网页地址列表 | `["https://..."]` |

#### 响应示例

**流式输出（每条独立）**：

```
data: {"type": "progress", "message": "正在加载历史数据..."}\n\n

data: {"type": "progress", "message": "正在训练模型..."}\n\n

data: {"type": "progress", "message": "设置随机种子: 26009 (基于期号 26009)"}\n\n

data: {"type": "progress", "message": "总组合数: 5405400 = 324632(红) × 66(蓝)"}\n\n

data: {"type": "progress", "message": "开始枚举评分..."}\n\n

data: {"type": "progress", "message": "已评分: 10000 组..."}\n\n

data: {"type": "progress", "message": "已评分: 20000 组..."}\n\n

data: {"type": "progress", "message": "共评分 2567890 组符合条件的组合"}\n\n

data: {"type": "progress", "message": "最终输出 20 组预测结果"}\n\n

data: {"type": "result", "data": {"rank": 1, "red": [3, 12, 19, 28, 34], "blue": [2, 9], "score": 1245.67, "reason": "和值理想 | 前区全新号 | 模型强力推荐(0.52) | 蓝球1小1大", "red_str": "03 12 19 28 34", "blue_str": "02 09"}}\n\n

data: {"type": "result", "data": {"rank": 2, "red": [5, 11, 18, 27, 33], "blue": [4, 10], "score": 1198.34, "reason": "和值理想 | 前区1个重号 | 模型推荐(0.48) | 蓝球1小1大", "red_str": "05 11 18 27 33", "blue_str": "04 10"}}\n\n

...

data: {"type": "complete", "message": "预测完成"}\n\n
```

#### 数据类型说明

**progress 类型**：
```json
{
  "type": "progress",
  "message": "进度信息"
}
```

**result 类型**：
```json
{
  "type": "result",
  "data": {
    "rank": 1,
    "red": [3, 12, 19, 28, 34],
    "blue": [2, 9],
    "score": 1245.67,
    "reason": "和值理想 | 前区全新号 | 模型强力推荐(0.52) | 蓝球1小1大",
    "red_str": "03 12 19 28 34",
    "blue_str": "02 09"
  }
}
```

**complete 类型**：
```json
{
  "type": "complete",
  "message": "预测完成"
}
```

**error 类型**：
```json
{
  "type": "error",
  "message": "错误描述"
}
```

#### 前端代码示例

```javascript
// JavaScript + EventSource
const eventSource = new EventSource('/api/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    period: '26009',
    kill_red: [1, 2, 35],
    sum_range: [80, 120]
  })
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'progress':
      console.log('[进度]', data.message);
      break;
    
    case 'result':
      console.log('[结果]', data.data);
      displayResult(data.data);
      break;
    
    case 'complete':
      console.log('[完成]', data.message);
      eventSource.close();
      break;
    
    case 'error':
      console.error('[错误]', data.message);
      eventSource.close();
      break;
  }
};

eventSource.onerror = function(error) {
  console.error('连接错误:', error);
  eventSource.close();
};
```

---

## 回测接口

### 2. 回测验证

#### 接口信息
- **路径**: `/api/backtest`
- **方法**: `POST`
- **功能**: 对历史期次进行模拟预测
- **响应**: SSE 流式输出

#### 请求参数

```json
{
  "start_period": "25001",
  "end_period": "25080"
}
```

**参数说明**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `start_period` | string | ✅ | 起始期号，5位数字 | `"25001"` |
| `end_period` | string | ✅ | 结束期号，5位数字 | `"25080"` |

#### 响应示例

```
data: {"type": "progress", "message": "正在加载历史数据..."}\n\n

data: {"type": "progress", "message": "开始回测 25001 至 25080，共 80 期"}\n\n

data: {"type": "result", "data": {"period": "25001", "actual_red": [5, 12, 19, 28, 34], "actual_blue": [3, 9], "predicted_red": [3, 12, 19, 27, 34], "predicted_blue": [2, 9], "red_hits": 3, "blue_hits": 1, "reason": "模型强力推荐(0.48) | 和值理想 | 前区1个重号", "current_avg_red": 3.0, "current_avg_blue": 1.0, "current_core_cov": 0.0}}\n\n

data: {"type": "result", "data": {"period": "25002", "actual_red": [7, 11, 18, 25, 32], "actual_blue": [4, 10], "predicted_red": [5, 11, 17, 26, 33], "predicted_blue": [3, 10], "red_hits": 1, "blue_hits": 1, "reason": "模型推荐(0.42) | 和值理想", "current_avg_red": 2.0, "current_avg_blue": 1.0, "current_core_cov": 0.0}}\n\n

...

data: {"type": "summary", "data": {"total_periods": 80, "avg_red_hits": 2.15, "avg_blue_hits": 0.87, "core_coverage": 12.5, "soft_coverage": 45.8, "hit_distribution": {"R0+B0": 5, "R1+B0": 12, "R1+B1": 18, "R2+B0": 8, "R2+B1": 15, "R3+B0": 4, "R3+B1": 10, "R4+B0": 2, "R4+B1": 4, "R5+B0": 1, "R5+B1": 1}}}\n\n

data: {"type": "complete", "message": "回测完成"}\n\n
```

#### 数据类型说明

**result 类型**（单期结果）：
```json
{
  "type": "result",
  "data": {
    "period": "25001",
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
}
```

**summary 类型**（汇总统计）：
```json
{
  "type": "summary",
  "data": {
    "total_periods": 80,
    "avg_red_hits": 2.15,
    "avg_blue_hits": 0.87,
    "core_coverage": 12.5,
    "soft_coverage": 45.8,
    "hit_distribution": {
      "R0+B0": 5,
      "R1+B0": 12,
      "R1+B1": 18,
      "R2+B0": 8,
      "R2+B1": 15,
      "R3+B0": 4,
      "R3+B1": 10,
      "R3+B2": 2,
      "R4+B0": 2,
      "R4+B1": 4,
      "R4+B2": 1,
      "R5+B0": 1,
      "R5+B1": 1,
      "R5+B2": 0
    }
  }
}
```

**指标说明**：

| 指标 | 说明 | 计算公式 |
|------|------|---------|
| `avg_red_hits` | 前区平均命中数 | Σ(红球命中数) / 总期数 |
| `avg_blue_hits` | 后区平均命中数 | Σ(蓝球命中数) / 总期数 |
| `core_coverage` | 核心覆盖率(%) | (R4+B2 + R5+X) / 总期数 × 100 |
| `soft_coverage` | 软覆盖率(%) | (R3+B1 + R3+B2 + R4+B0 + R4+B1) / 总期数 × 100 |
| `hit_distribution` | 命中分布 | 各命中情况的期数统计 |

---

## 历史查询接口

### 3. 历史开奖查询

#### 接口信息
- **路径**: `/api/history`
- **方法**: `GET`
- **功能**: 查询历史开奖记录
- **响应**: JSON

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `start_period` | string | ❌ | 起始期号 | `"25001"` |
| `end_period` | string | ❌ | 结束期号 | `"25080"` |
| `limit` | int | ❌ | 返回数量限制 | `50` |

#### 请求示例

```http
GET /api/history?start_period=25001&end_period=25080&limit=50
```

#### 响应示例

```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "total": 80,
    "records": [
      {
        "period": "25001",
        "date": "2025-01-01",
        "red": [5, 12, 19, 28, 34],
        "blue": [3, 9],
        "red_str": "05 12 19 28 34",
        "blue_str": "03 09"
      },
      {
        "period": "25002",
        "date": "2025-01-04",
        "red": [7, 11, 18, 25, 32],
        "blue": [4, 10],
        "red_str": "07 11 18 25 32",
        "blue_str": "04 10"
      }
    ]
  }
}
```

---

## 取消任务接口

### 4. 取消任务

#### 接口信息
- **路径**: `/api/cancel/<task_id>`
- **方法**: `POST`
- **功能**: 取消正在执行的预测或回测任务
- **响应**: JSON

#### 请求示例

```http
POST /api/cancel/task_123456789
```

#### 响应示例

**成功**：
```json
{
  "code": 0,
  "message": "任务已取消",
  "task_id": "task_123456789"
}
```

**失败**（任务不存在）：
```json
{
  "code": 404,
  "message": "任务不存在",
  "task_id": "task_123456789"
}
```

---

## 错误码定义

### 错误码表

| 错误码 | 说明 | HTTP状态码 | 解决方案 |
|--------|------|-----------|---------|
| `0` | 成功 | 200 | - |
| `1001` | 参数缺失 | 400 | 检查必填参数 |
| `1002` | 参数格式错误 | 400 | 检查参数类型和格式 |
| `1003` | 参数值超出范围 | 400 | 检查取值范围 |
| `2001` | 模型未训练 | 500 | 等待模型训练完成 |
| `2002` | 历史数据加载失败 | 500 | 检查数据文件是否存在 |
| `2003` | 网页分析失败 | 500 | 检查网页地址是否有效 |
| `3001` | 任务不存在 | 404 | 检查任务ID是否正确 |
| `3002` | 任务已完成 | 400 | 无法取消已完成的任务 |
| `9999` | 未知错误 | 500 | 查看详细错误日志 |

### 错误响应示例

**参数缺失**：
```json
{
  "code": 1001,
  "message": "参数缺失",
  "details": "缺少必填参数: period"
}
```

**参数格式错误**：
```json
{
  "code": 1002,
  "message": "参数格式错误",
  "details": "期号格式错误，应为5位数字"
}
```

**模型未训练**：
```json
{
  "code": 2001,
  "message": "模型未训练",
  "details": "请等待模型训练完成后再尝试"
}
```

---

## 附录

### 完整调用流程示例

```javascript
// 1. 发起预测请求
fetch('/api/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    period: '26009',
    kill_red: [1, 2, 35],
    sum_range: [80, 120]
  })
})
.then(response => {
  // 2. 建立 SSE 连接
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  function read() {
    reader.read().then(({done, value}) => {
      if (done) {
        console.log('流结束');
        return;
      }
      
      // 3. 解析 SSE 数据
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n\n');
      
      lines.forEach(line => {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          handleData(data);
        }
      });
      
      read();
    });
  }
  
  read();
})
.catch(error => {
  console.error('请求失败:', error);
});

// 4. 处理数据
function handleData(data) {
  switch(data.type) {
    case 'progress':
      updateProgress(data.message);
      break;
    case 'result':
      displayResult(data.data);
      break;
    case 'complete':
      showComplete(data.message);
      break;
    case 'error':
      showError(data.message);
      break;
  }
}
```

### 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| V1.0 | 2026-01-21 | 初始版本，完整API接口文档 |

---

**文档结束**
