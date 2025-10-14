# Mars日志分析系统 - 专业版

一个功能强大的iOS开发工具套件，集成Mars/微信 xlog日志解析、IPS崩溃分析、iOS推送测试、沙盒浏览、dSYM符号化、LinkMap分析和**iOS代码混淆**等专业功能。

## 🌟 主要功能

### 核心功能
- ✅ **专属格式**：专门解析Mars/微信的.xlog格式日志文件
- ✅ **批量解析**：支持文件夹和单文件选择，智能分组相似文件
- ✅ **并行处理**：多线程并行解析，显著提升处理速度
- ✅ **模块分组**：自动识别和分组不同模块（mars::stn、HY-Default等）
- ✅ **高级过滤**：支持关键词、正则表达式、时间范围、日志级别组合过滤
- ✅ **数据可视化**：饼图、柱状图、时间分布图等多种图表
- ✅ **懒加载显示**：大文件优化，流畅显示百万级日志
- ✅ **导出功能**：支持导出当前视图、模块报告、过滤结果

### iOS开发工具
- ✅ **IPS崩溃分析**：解析iOS崩溃报告，支持符号化
- ✅ **iOS推送测试**：APNS推送测试工具，支持沙盒和生产环境
- ✅ **iOS沙盒浏览**：浏览iOS应用沙盒文件系统，支持预览和导出
- ✅ **dSYM符号化**：自动加载dSYM文件，崩溃地址符号化
- ✅ **LinkMap分析**：iOS应用二进制大小分析，代码瘦身
- ✅ **iOS代码混淆** 🆕：专业级代码混淆工具，应对App Store机器审核

### 日志级别支持
- FATAL（致命）
- ERROR（错误）
- WARNING（警告）
- INFO（信息）
- DEBUG（调试）
- VERBOSE（详细）

### 时间过滤格式
- 完整格式：`YYYY-MM-DD HH:MM:SS`
- 仅时间：`HH:MM:SS`（只比较时间部分）
- 仅日期：`YYYY-MM-DD`（自动扩展为全天）

## 📁 项目结构

```
mars-log-analyzer/
│
├── mars_log_analyzer_pro.py      # 主程序（专业版）
├── decode_mars_nocrypt_log_file_py3.py  # 核心解码器
├── fast_decoder.py               # 快速并行解码器
├── optimized_decoder.py          # 优化解码器（实验性）
├── scrolled_text_with_lazy_load.py  # 懒加载文本组件
├── run_analyzer.sh               # Mac/Linux启动脚本
├── run_analyzer.bat              # Windows启动脚本
├── requirements.txt              # Python依赖
├── README.md                     # 英文文档
├── README_CN.md                  # 中文文档
└── CLAUDE.md                     # 技术文档

生成文件（运行后）：
├── venv/                         # Python虚拟环境
└── *.log                         # 解析后的日志文件
```

## 🚀 快速开始

### 系统要求

#### Mac系统
- macOS 10.12 或更高版本
- Python 3.6+
- 约100MB可用磁盘空间

#### Windows系统
- Windows 10/11
- Python 3.6+
- 约100MB可用磁盘空间

#### Linux系统
- Ubuntu 18.04+ / CentOS 7+
- Python 3.6+
- tkinter支持

### 安装步骤

#### 方法一：使用启动脚本（推荐）

**Mac/Linux用户：**
```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd mars-log-analyzer

# 2. 添加执行权限
chmod +x run_analyzer.sh

# 3. 运行程序（自动安装依赖）
./run_analyzer.sh
```

**Windows用户：**
```cmd
# 1. 克隆或下载项目
git clone <repository-url>
cd mars-log-analyzer

# 2. 双击运行 run_analyzer.bat
# 或在命令行运行：
run_analyzer.bat
```

#### 方法二：手动安装

```bash
# 1. 安装Python（如未安装）
# Mac: brew install python3
# Windows: 从 python.org 下载安装
# Linux: sudo apt-get install python3 python3-pip python3-tk

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行程序
python mars_log_analyzer_pro.py
```

## 📖 使用指南

### iOS代码混淆工具 🆕

#### 功能概述
专业级iOS代码混淆工具，帮助开发者应对App Store的4.3、2.1等机器审核问题。支持Objective-C和Swift代码混淆。

#### 核心特性
- **符号混淆**：类名、方法名、属性名、协议名、枚举名、常量名
- **高级混淆**：垃圾代码生成、字符串加密、方法顺序打乱、资源文件修改
- **智能白名单**：内置500+系统API白名单，自动检测第三方库
- **确定性混淆**：支持固定种子，版本迭代时保持一致性
- **增量混淆**：支持增量编译，仅处理变更文件
- **双接口支持**：GUI图形界面和CLI命令行工具

#### GUI使用方法
1. 启动主程序：`./scripts/run_analyzer.sh`
2. 切换到"iOS代码混淆"标签页
3. 选择项目路径和输出目录
4. 配置混淆选项（使用模板或自定义）
5. 点击"开始混淆"执行

#### CLI使用方法
```bash
# 基础混淆（使用标准模板）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --template standard

# 自定义混淆配置
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --class-names \
    --method-names \
    --property-names \
    --insert-garbage-code \
    --string-encryption \
    --prefix "WHC" \
    --seed "my_project_v1.0"

# 增量混淆（仅处理变更）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --incremental \
    --mapping /path/to/old_mapping.json

# 只分析不混淆
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --analyze-only \
    --report /path/to/analysis_report.json
```

#### 配置模板
- **minimal**：最小化混淆（仅类名和方法名）
- **standard**：标准混淆（平衡的混淆策略）
- **aggressive**：激进混淆（最强混淆力度）

#### 注意事项
1. **备份代码**：混淆前务必备份原始代码
2. **测试验证**：混淆后完整测试应用功能
3. **保存映射**：妥善保存名称映射文件（用于调试和增量混淆）
4. **白名单管理**：根据项目需要自定义白名单

更多详细文档请参考：
- 技术文档：`gui/modules/obfuscation/CLAUDE.md`
- 开发路线图：`docs/technical/IOS_OBFUSCATION_ROADMAP.md`

---

### 1. 加载日志文件

#### 支持的文件格式
- **仅支持 `.xlog` 格式**：Mars/微信专用的二进制日志格式
- 不支持普通文本日志（.log、.txt等）
- 不支持其他格式的日志文件

#### 选择文件夹
- 点击"选择文件夹"按钮
- 选择包含`.xlog`文件的目录
- 系统会自动扫描并分组相似文件
- 忽略非.xlog格式的文件

#### 选择单个文件
- 点击"选择文件"按钮
- 文件选择器只显示`.xlog`文件
- 无法选择其他格式的文件

#### 文件分组
- 勾选"合并相似文件名"自动分组
- 例如：`app_20250101.xlog`和`app_20250101_1.xlog`会被分为一组

### 2. 解析日志

点击"开始解析"按钮：
- 进度条显示解析进度
- 支持并行处理多个文件
- 解析完成后自动加载第一个文件组

### 3. 日志查看

#### 全局过滤
- **关键词搜索**：支持普通文本和正则表达式
- **时间范围**：输入开始和结束时间
- **日志级别**：选择要显示的级别
- **模块过滤**：选择特定模块

点击"应用过滤"执行组合过滤。

### 4. 模块分组

切换到"模块分组"标签：
- 左侧显示所有模块列表
- 显示每个模块的日志数量和错误/警告统计
- 点击模块查看详细日志

#### 模块内过滤
- 模块内搜索：支持关键词和正则
- 时间范围过滤：同全局过滤
- 点击"应用过滤"查看结果

### 5. 统计分析

切换到"统计分析"标签查看：
- 日志级别分布饼图
- 模块分布统计
- 文件解析统计
- 错误/警告趋势

### 6. 时间分布

切换到"时间分布"标签：
- 按小时统计日志分布
- 柱状图可视化
- 识别高峰时段

### 7. 导出功能

#### 日志查看页
- **导出当前视图**：导出过滤后的日志
- **导出分组报告**：按模块分组导出
- **导出完整报告**：导出所有分析结果

#### 模块分组页
- **导出当前模块**：导出选中模块的所有日志
- **导出过滤结果**：导出过滤后的日志
- **导出所有模块**：批量导出到目录

## 🎯 使用场景

### 场景1：查找特定时间段的错误
1. 在时间范围输入：`10:00:00` 至 `11:00:00`
2. 日志级别选择：`ERROR`
3. 点击"应用过滤"

### 场景2：分析特定模块问题
1. 切换到"模块分组"
2. 选择问题模块（如`mars::stn`）
3. 搜索关键词如"timeout"或"failed"

### 场景3：导出错误报告
1. 日志级别选择`ERROR`和`FATAL`
2. 应用过滤
3. 点击"导出当前视图"

### 场景4：批量分析多天日志
1. 选择包含多天日志的文件夹
2. 勾选"合并相似文件名"
3. 开始解析后查看时间分布

## ⚙️ 高级功能

### 正则表达式搜索
搜索模式选择"正则"，支持复杂模式匹配：
- `error.*timeout` - 查找包含error和timeout的行
- `\d{3,}ms` - 查找响应时间超过100ms的日志
- `(failed|error|exception)` - 查找任一关键词

### 时间格式灵活性
- `2025-01-15 10:30:00` - 精确时间点
- `10:30:00` - 今天的10:30
- `2025-01-15` - 整天的日志

### 性能优化
- 懒加载：大文件分批加载显示
- 并行解析：多文件同时处理
- 内存优化：智能管理内存使用

## 🔧 故障排除

### 问题：程序无法启动

**Mac/Linux：**
```bash
# 检查Python版本
python3 --version

# 安装tkinter
# Mac: brew install python-tk
# Linux: sudo apt-get install python3-tk
```

**Windows：**
- 确保Python安装时勾选了"Add to PATH"
- 重新安装Python并选择"Install for all users"

### 问题：解析失败或乱码

可能原因：
1. 文件不是.xlog格式（系统只支持.xlog）
2. xlog文件已加密（需要密钥）
3. 文件损坏
4. 不支持的Mars日志格式版本

解决方法：
- 确认文件扩展名是.xlog
- 确认xlog文件未加密
- 尝试其他xlog文件
- 检查文件完整性

### 问题：内存不足

对于超大文件（>1GB）：
1. 关闭其他程序释放内存
2. 分批处理文件
3. 使用过滤功能减少显示内容

### 问题：中文显示问题

Windows系统：
1. 控制面板 → 区域 → 管理 → 更改系统区域设置
2. 勾选"使用UTF-8提供全球语言支持"
3. 重启计算机

## 📊 性能指标

- 解析速度：约50-100MB/秒（取决于CPU）
- 内存使用：约为文件大小的2-3倍
- 并行处理：最多4个文件同时解析
- UI响应：支持百万级日志流畅显示

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 报告问题
请包含以下信息：
- 操作系统版本
- Python版本
- 错误信息截图
- 问题复现步骤

### 功能建议
- 使用场景描述
- 期望的功能效果
- 可能的实现方案

## 📄 许可证

MIT License - 详见LICENSE文件

## 🙏 致谢

- Mars/微信团队的xlog格式
- Python社区的优秀库
- 所有贡献者和用户

## 📮 联系方式

- Issue：[GitHub Issues](https://github.com/your-repo/issues)
- Email：your-email@example.com

---

**版本：** 2.2.0
**最后更新：** 2025年10月14日

## 🆕 最新更新 (v2.2.0)

### iOS代码混淆模块完成 🎉
- ✅ 核心功能100%完成（9个核心模块）
- ✅ P2高级功能完成：垃圾代码生成、字符串加密、增量编译
- ✅ GUI和CLI双接口支持
- ✅ 完整的测试验证和文档
- ✅ 支持Objective-C和Swift混淆
- ✅ 内置500+系统API白名单
- ✅ 三种配置模板（minimal/standard/aggressive）
- ✅ 确定性混淆和增量混淆支持