# 📚 文档索引

**最后更新**: 2026-01-27  
**当前版本**: V11.0

---

## 📂 文档目录结构

```
docs/
├── README.md                        # 文档总览（从这里开始）
├── DOCUMENTATION_INDEX.md           # 本文件：快速索引
├── API_REFERENCE.md                 # API接口文档
├── DESIGN_DOCUMENT.md               # 系统设计文档
├── DEVELOPMENT_GUIDE.md             # 开发规范文档
├── DOCS_UPDATE_CHECKLIST.md         # 文档更新检查清单
├── SYSTEM_MODULES.md                # 系统功能模块说明书
└── VERSION_NOTES/                   # 版本说明目录
    ├── V11_OPTIMIZATION_NOTES.md    # V11激进优化版
    ├── V10_DETERMINISM_FIX.md       # V10确定性修复
    ├── V10_IMPLEMENTATION_SUMMARY.md # V10实现总结
    └── V9_UPGRADE_NOTES.md          # V9升级说明
```

---

## 🎯 快速查找

### 我是新用户，想了解系统
➡️ 从 [README.md](./README.md) 开始

### 我是产品经理/业务人员
➡️ 查看 [SYSTEM_MODULES.md](./SYSTEM_MODULES.md) 了解功能模块

### 我是前端开发者
➡️ 查看 [API_REFERENCE.md](./API_REFERENCE.md) 了解接口定义

### 我是后端开发者
➡️ 优先阅读：
1. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 编码规范
2. [DESIGN_DOCUMENT.md](./DESIGN_DOCUMENT.md) - 架构设计
3. [DOCS_UPDATE_CHECKLIST.md](./DOCS_UPDATE_CHECKLIST.md) - 文档同步规范

### 我想了解最新变更
➡️ 查看 [VERSION_NOTES/](./VERSION_NOTES/) 目录下的版本说明

### 我要修改代码
➡️ **必读**：
1. [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 编码规范
2. [DOCS_UPDATE_CHECKLIST.md](./DOCS_UPDATE_CHECKLIST.md) - 文档更新要求

---

## 📝 文档维护规范

### 强制要求
每次代码修改、功能优化、模型算法调整后，**必须同步更新相关文档**！

### 更新触发条件
- ✅ 评分系统调整
- ✅ 过滤条件变更
- ✅ 特征工程改进
- ✅ ML模型架构变化
- ✅ 权重参数调整
- ✅ 新增功能模块
- ✅ 修改现有功能
- ✅ API接口变更
- ✅ Bug修复

### 更新检查清单
详见 [DOCS_UPDATE_CHECKLIST.md](./DOCS_UPDATE_CHECKLIST.md)

---

## 📊 文档状态

| 文档名称 | 最后更新 | 状态 |
|---------|---------|------|
| README.md | 2026-01-27 | ✅ 最新 |
| SYSTEM_MODULES.md | 2026-01-21 | ⚠️ 待更新V11内容 |
| DESIGN_DOCUMENT.md | 2026-01-21 | ⚠️ 待更新V11内容 |
| API_REFERENCE.md | 2026-01-21 | ✅ 无变更 |
| DEVELOPMENT_GUIDE.md | 2026-01-21 | ✅ 无变更 |
| DOCS_UPDATE_CHECKLIST.md | 2026-01-27 | ✅ 最新 |
| V11_OPTIMIZATION_NOTES.md | 2026-01-27 | ✅ 最新 |
| V10_DETERMINISM_FIX.md | 2026-01-25 | ✅ 历史版本 |
| V10_IMPLEMENTATION_SUMMARY.md | 2026-01-25 | ✅ 历史版本 |
| V9_UPGRADE_NOTES.md | 2026-01-22 | ✅ 历史版本 |

---

## 🔄 文档更新历史

### 2026-01-27
- ✅ 整理文档结构，统一存放到docs/目录
- ✅ 创建VERSION_NOTES/子目录，集中管理版本说明
- ✅ 更新README.md，添加V11版本信息
- ✅ 创建DOCUMENTATION_INDEX.md快速索引

### 2026-01-21
- ✅ 完善文档体系，创建完整的文档导航
- ✅ 规范化所有文档格式

---

## 📞 文档反馈

如发现文档内容过时、错误或有改进建议，请：
1. 提交 GitHub Issue
2. 或直接联系维护团队

**维护者**: AI Assistant  
**联系方式**: 见项目README
