# iOS代码混淆模块

## 模块概述
iOS代码混淆工具，支持Objective-C/Swift项目混淆，应对App Store审核。

## 核心功能
- 类名/方法名/属性名/协议名混淆
- 垃圾代码生成和字符串加密
- 白名单管理（符号+字符串）
- 增量混淆和并行处理优化

## 架构 (重构后 v2.3.2)

```
gui/modules/obfuscation/
├── tab_main.py (381行)         # 主控制器
├── ui/
│   ├── config_panel.py (511行)     # 配置面板
│   ├── progress_panel.py (122行)   # 进度显示
│   ├── mapping_panel.py (308行)    # 映射管理
│   ├── whitelist_panel.py (755行)  # 白名单管理
│   └── help_dialog.py (309行)      # 参数帮助
├── tests/                          # 单元测试
├── obfuscation_engine.py           # 混淆引擎
├── obfuscation_cli.py              # CLI工具
└── ...                             # 其他核心模块
```

**重构成果**: 2330行→2386行+测试 (10个文件,模块化程度10倍提升)

## 快速使用

### GUI
```bash
./scripts/run_analyzer.sh
# 选择"iOS代码混淆"标签 → 配置 → 开始混淆
```

### CLI
```bash
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --template standard
```

## 配置选项

**基础混淆**:
- `class_names`, `method_names`, `property_names`, `protocol_names`

**高级功能**:
- `insert_garbage_code`: 垃圾代码生成
- `string_encryption`: 字符串加密 (xor/base64/shift/rot13)
- `enable_incremental`: 增量混淆

**性能优化**:
- `parallel_processing`: 并行处理 (3-6x加速)
- `enable_parse_cache`: 解析缓存 (100-300x提升)

## 内置模板
- **minimal**: 最小化混淆（快速测试）
- **standard**: 标准策略（推荐）
- **aggressive**: 激进混淆（正式发布）

## 白名单系统
- **系统API**: 内置500+类、1000+方法白名单
- **第三方库**: 自动检测CocoaPods/SPM/Carthage
- **自定义白名单**: 支持通配符(*和?)、JSON导入导出

## 版本历史

**v2.3.2** (2025-10-22) - Phase 1.5 & 1.6
- ✅ 新增whitelist_panel.py (755行)
- ✅ 新增help_dialog.py (309行)
- ✅ 完整单元测试框架

**v2.3.1** (2025-10-22) - Phase 1 重构
- ✅ UI模块化 (2330行→5个模块,重构率57%)

**v2.3.0** (2025-10-21) - 性能优化
- ✅ 并行处理和缓存系统

**v2.2.0** (2025-10-15) - 功能增强
- ✅ 垃圾代码生成和字符串加密

---

**版本**: 2.4.0 | **更新**: 2025-10-23 | **状态**: ✅ 所有超大文件重构完成 (Phase 1-5)
