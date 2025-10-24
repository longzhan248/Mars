# CLAUDE.md

此文件为 Claude Code 在此代码库中工作时提供指导。

## 项目用途

**心娱开发助手 (Xinyu DevTools)** - 一站式iOS开发工具集，集成日志分析、崩溃解析、推送测试、沙盒浏览和代码混淆等功能。核心包含用于解码和分析 Mars xlog 文件的完整工具套件。

## 快速开始

```bash
# 一键启动（自动处理所有环境配置）
./scripts/run_analyzer.sh
```

首次运行会自动创建虚拟环境并安装依赖。

## 核心功能

### 📊 Mars日志分析 + AI智能诊断
- xlog文件解码和分析
- AI驱动的崩溃分析、性能诊断
- 智能搜索和跳转功能

### 🔧 iOS开发工具集
- IPS崩溃解析、APNS推送测试
- iOS沙盒浏览、dSYM分析
- LinkMap分析、代码混淆

### ⚡ 性能优化
- 倒排索引搜索 (性能提升93%)
- 流式文件加载 (支持GB级文件)
- 内存优化 (占用减少70%)

## 近期重要更新

**2025-10-23**: 🏆 代码质量优化完成
- ✅ 5个超大文件重构为16个模块
- ✅ 所有文件符合500行限制
- ✅ 应用工厂、策略、委托等设计模式
- 📄 详见: [代码质量重构报告](docs/CODE_QUALITY_REFACTORING_2025.md)

*详细更新历史请参考 [CHANGELOG.md](CHANGELOG.md)*

## 项目结构

```
.
├── gui/
│   ├── mars_log_analyzer_modular.py    # 主程序入口
│   ├── modules/                        # 模块化组件
│   │   ├── ai_interaction_manager.py   # AI交互管理 🆕
│   │   ├── data_models.py              # 数据模型
│   │   ├── file_operations.py          # 文件操作
│   │   └── obfuscation/                # iOS混淆模块
│   │       ├── code_transformer.py     # 代码转换
│   │       ├── symbol_replacer.py 🆕   # 符号替换
│   │       ├── encryption_algorithms.py 🆕  # 加密算法
│   │       ├── third_party_detector.py 🆕   # 第三方检测
│   │       └── ui/                     # UI组件
│   │           ├── symbol_whitelist_manager.py 🆕
│   │           └── string_whitelist_manager.py 🆕
│   └── components/                     # UI组件
├── decoders/                           # 解码器
├── push_tools/                         # iOS推送工具
├── tools/                              # 辅助工具
├── scripts/                            # 启动脚本
└── docs/                               # 文档

🆕 = 2025-10-23 代码质量优化新增
```

## 开发规范 🚨

### 1. 模块化开发原则 📦

**所有新增代码必须遵循模块化设计：**
- **单一职责原则**: 每个模块只负责一个特定功能
- **高内聚低耦合**: 模块内部紧密相关，模块间依赖最小化
- **清晰的接口定义**: 每个模块提供明确的公共API
- **独立可测试**: 每个模块应该能够独立进行单元测试

### 2. 代码行数限制 📏

**每个文件不得超过 500 行代码（不含注释和空行）**

```bash
# 检查文件代码行数
grep -v '^\s*#' file.py | grep -v '^\s*$' | wc -l
```

**当文件超过限制时：**
1. 识别可独立的功能模块
2. 创建新的子模块文件
3. 提取相关代码到新模块
4. 更新导入和调用关系

**参考案例：**
- `gui/modules/obfuscation/` - 从1500行拆分为11个模块
- `gui/modules/ai_diagnosis/` - 从1200行拆分为8个模块

### 3. 代码质量要求 ✨

- **类型注解**: 所有公共函数必须有类型注解
- **文档字符串**: 所有模块、类和公共函数必须有docstring
- **错误处理**: 必须有适当的异常处理
- **单元测试**: 核心功能模块需要配套测试

### 4. 命名规范 📝

- 文件名: `module_name.py`
- 类名: `ClassName`
- 函数名: `function_name()`
- 常量: `CONSTANT_NAME`
- 私有成员: `_private_method()`

### 5. 违规处理 ⚠️

**Claude Code 将拒绝执行以下操作：**
- 创建超过 500 行的新文件
- 向已超过 500 行的文件添加非修复性代码
- 创建缺乏明确职责的"大杂烩"模块

**正确做法**: 先进行模块化重构，再实现新功能。

---

## 常用命令

### 启动程序
```bash
./scripts/run_analyzer.sh              # GUI程序（推荐）
./scripts/run_push_tool.sh             # iOS推送工具
```

### 命令行解码
```bash
python3 decoders/decode_mars_nocrypt_log_file_py3.py file.xlog
```

### iOS代码混淆
```bash
# GUI使用
./scripts/run_analyzer.sh  # 选择"iOS代码混淆"标签页

# CLI使用
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --template standard
```

## 常见问题

**Q: 缺少依赖模块？**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Q: GUI打不开？**
使用 `./scripts/run_analyzer.sh` 启动，它会自动处理依赖。

**Q: 详细功能说明？**
参考 [FEATURES.md](FEATURES.md)

**Q: 如何参与开发？**
参考 [DEVELOPMENT.md](DEVELOPMENT.md)

## 技术文档

- **代码质量重构**: `docs/CODE_QUALITY_REFACTORING_2025.md`
- **性能优化**: `docs/technical/`
- **AI集成**: `docs/technical/`
- **更新历史**: `CHANGELOG.md`

## 快速参考

**主要入口**:
- 主程序: `gui/mars_log_analyzer_modular.py`
- 启动脚本: `./scripts/run_analyzer.sh`

**关键模块**:
- 数据模型: `gui/modules/data_models.py`
- 文件操作: `gui/modules/file_operations.py`
- AI诊断: `gui/modules/ai_diagnosis/`
- iOS混淆: `gui/modules/obfuscation/`

---

*详细说明请参考对应的专门文档*
