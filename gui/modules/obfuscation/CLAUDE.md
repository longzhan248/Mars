# CLAUDE.md - iOS代码混淆模块

## 模块概述
iOS代码混淆模块，用于对iOS原生项目（Objective-C/Swift）进行代码混淆，帮助应对App Store审核问题。

## 核心功能
- **类名/方法名/属性名混淆** - 核心混淆功能
- **垃圾代码生成** - 增加代码复杂度 (v2.2.0)
- **字符串加密** - 保护敏感信息 (v2.2.0)
- **资源文件处理** - XIB/Storyboard/图片处理
- **增量混淆** - 支持版本迭代
- **并行处理** - 性能优化 (v2.3.0)

## 架构设计

### 核心模块
```
gui/modules/obfuscation/
├── config_manager.py          # 配置管理器
├── whitelist_manager.py       # 白名单管理器
├── name_generator.py          # 名称生成器
├── project_analyzer.py        # 项目分析器
├── code_parser.py             # 代码解析器
├── code_transformer.py        # 代码转换器
├── resource_handler.py        # 资源处理器
├── obfuscation_engine.py      # 混淆引擎核心
├── obfuscation_tab.py         # GUI界面
├── obfuscation_cli.py         # CLI工具
└── garbage_generator.py       # 垃圾代码生成器
```

### 数据流
```
配置管理 → 项目分析 → 代码解析 → 名称生成 → 白名单过滤 → 代码转换 → 资源处理 → 输出
```

## 使用方法

### GUI使用
```bash
# 启动主程序
./scripts/run_analyzer.sh

# 切换到"iOS代码混淆"标签页
# 1. 选择项目和输出目录
# 2. 配置混淆选项
# 3. 点击"开始混淆"
```

### CLI使用
```bash
# 基础混淆
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/obfuscated \
    --template standard

# 自定义配置
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --class-names --method-names \
    --prefix "WHC" --seed "my_seed"

# 增量混淆
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --incremental \
    --mapping /path/to/old_mapping.json
```

## 配置选项

### 基础混淆
- `class_names`: 混淆类名
- `method_names`: 混淆方法名
- `property_names`: 混淆属性名
- `protocol_names`: 混淆协议名

### 高级功能
- `insert_garbage_code`: 插入垃圾代码 (v2.2.0)
- `string_encryption`: 字符串加密 (v2.2.0)
- `enable_incremental`: 增量混淆
- `use_fixed_seed`: 确定性混淆

### 性能优化 (v2.3.0)
- `parallel_processing`: 并行处理 (默认启用)
- `enable_parse_cache`: 解析缓存 (默认启用)
- `max_workers`: 最大线程数

## 内置模板

### minimal (最小化)
- 仅混淆核心符号
- 适合快速测试

### standard (标准)
- 平衡的混淆策略
- 推荐日常使用

### aggressive (激进)
- 最强混淆力度
- 适合正式发布

## 白名单系统

### 系统API
内置500+系统类、1000+系统方法白名单，包括：
- UIKit (100+ 类)
- Foundation (80+ 类)
- Core Graphics (30+ 类)

### 第三方库
自动检测和保护：
- CocoaPods依赖
- Swift Package Manager
- Carthage依赖

## 垃圾代码生成 (v2.2.0)

### 配置选项
- `garbage_count`: 垃圾类数量 (5-100)
- `garbage_complexity`: 复杂度 (simple/moderate/complex)
- `garbage_prefix`: 类名前缀

### 功能特点
- 支持ObjC和Swift
- 三种复杂度级别
- 调用关系生成 (v2.2.3)
- 确定性生成

## 字符串加密 (v2.2.0)

### 加密算法
- `xor`: 异或加密 (推荐)
- `base64`: Base64编码
- `shift`: 移位加密
- `rot13`: ROT13编码

### 配置选项
- `encryption_algorithm`: 加密算法
- `encryption_key`: 加密密钥
- `string_min_length`: 最小加密长度

## 性能优化 (v2.3.0)

### 并行处理
- **多线程解析**: 3-5x加速 (10+文件)
- **多进程转换**: 2-6x加速 (5000+行/文件)
- **智能阈值**: 自动选择最佳策略

### 缓存系统
- **两级缓存**: 内存+磁盘
- **MD5检测**: 自动检测文件变化
- **性能提升**: 100-300x (重复构建)

### 使用效果
```
⚡ 启用并行解析 (127个文件, 8线程)...
📦 启用解析缓存: .obfuscation_cache
📊 缓存命中: 95/127 (74.8%)
⚡ 启用多进程转换 (总代码行数: 65432, 4进程)...
```

## 常见问题

### 混淆失败
1. 检查项目路径和权限
2. 确认配置参数正确
3. 查看详细错误日志

### 编译错误
1. 检查映射文件是否正确导入
2. 验证垃圾代码文件已添加到项目
3. 确认解密代码已集成

### 性能问题
1. 启用并行处理和缓存
2. 减少垃圾代码数量
3. 使用增量混淆

## 安全注意事项

1. **备份原始代码** - 混淆前务必备份
2. **测试验证** - 混淆后完整测试功能
3. **映射保存** - 妥善保存名称映射文件
4. **版本管理** - 为每个版本保留独立映射

## 开发状态

### ✅ 已完成 (v2.3.0)
- 核心混淆功能 (100%)
- GUI界面集成
- CLI工具
- 垃圾代码生成
- 字符串加密
- 增量混淆
- 并行处理优化

### 🔄 开发中
- 资源处理增强
- 更多加密算法
- 自动化项目集成

---

*详细技术文档请参考源码注释和测试用例。*