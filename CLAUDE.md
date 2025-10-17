# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目用途
此代码库包含用于解码和分析 Mars xlog 文件的完整工具套件 - Mars 是腾讯的日志框架，xlog 是其使用的压缩和加密日志文件格式。
项目提供了从基础解码到高级分析的全方位解决方案，包括命令行工具、模块化GUI应用、IPS崩溃分析和iOS推送测试工具。

## 快速开始

### 一键启动（macOS）
```bash
# 1. 下载或克隆项目到任意目录
# 2. 进入项目目录
cd /path/to/project

# 3. 运行启动脚本（自动处理所有环境配置）
./scripts/run_analyzer.sh
```

首次运行会自动：
- ✅ 创建Python虚拟环境
- ✅ 安装所有必要依赖
- ✅ 启动主程序

## 最新更新

### 2025-10-16
- **AI智能诊断功能** 🤖✨ - 完整的AI驱动日志分析系统 (Phase 1-3完成)
  - **多AI服务支持**: Claude Code（推荐）、Claude API、OpenAI、Ollama本地模型
  - **智能分析能力**:
    - 🔥 崩溃分析：自动识别崩溃堆栈并提供修复建议
    - ⚡ 性能诊断：检测性能瓶颈和资源使用问题
    - 📊 问题总结：生成完整的问题报告和优先级建议
    - 🔍 智能搜索：基于AI的语义搜索和日志关联
    - 💬 自由对话：针对日志内容的交互式问答
  - **AI助手侧边栏**:
    - 4个快捷操作按钮（崩溃分析/性能诊断/问题总结/智能搜索）
    - 实时聊天界面with历史记录
    - 自由问答输入框
    - 状态管理和进度反馈
  - **右键菜单增强**:
    - 🤖 AI分析此日志：分析选中的日志条目
    - 🤖 AI解释错误原因：深度分析错误成因
    - 🤖 AI查找相关日志：智能关联日志搜索
  - **隐私保护**:
    - 自动过滤敏感信息（手机号/邮箱/IP/身份证等）
    - 内置白名单机制
    - 可自定义过滤规则
  - **日志预处理**:
    - 崩溃提取器：自动提取崩溃堆栈和上下文
    - 错误模式识别：识别10种常见错误模式
    - 日志摘要生成：智能压缩日志内容
  - **灵活配置**:
    - GUI配置对话框：服务选择、API Key管理、模型配置
    - 自动检测：优先级自动选择最佳可用服务
    - 环境变量支持：API Key通过环境变量配置
  - **异步处理**：所有AI请求异步执行，不阻塞UI
  - **核心模块** 🆕:
    - `gui/modules/ai_diagnosis/` - AI诊断核心（5个模块，约2240行）
    - `gui/modules/ai_assistant_panel.py` - AI助手面板（600行）
    - `gui/modules/ai_diagnosis_settings.py` - AI设置对话框（400行）
  - **完整文档**:
    - `docs/technical/AI_INTEGRATION_COMPLETE.md` - 总体完成报告
    - `gui/modules/ai_diagnosis/CLAUDE.md` - 技术文档
    - `docs/technical/AI_INTEGRATION_PROGRESS.md` - 进度跟踪
  - **使用简单**:
    ```bash
    # 启动主程序
    ./scripts/run_analyzer.sh

    # 右侧AI助手面板自动显示
    # 1. 点击"AI设置"配置服务（推荐使用自动检测）
    # 2. 点击快捷操作按钮进行分析
    # 3. 或在输入框中自由提问
    # 4. 右键日志可快速AI分析
    ```

### 2025-10-15
- **模块列表搜索功能** 🔍 - 快速定位目标模块
  - **实时搜索**: 输入即搜索，无需点击按钮
  - **智能过滤**: 不区分大小写的部分匹配
  - **保持排序**: Crash模块始终置顶，其他按字母排序
  - **统计完整**: 保留每个模块的日志数、崩溃数、错误数统计
  - **一键清除**: "×"按钮快速恢复显示全部模块
  - **选择保持**: 当前选中模块仍在过滤结果中时自动保持选中
  - **位置**: 模块分组标签页 > 模块列表上方
  - **Python 3.13兼容**: 使用 `trace_add()` 替代旧的 `trace()` 方法
  - **技术文档**: `docs/technical/MODULE_LIST_SEARCH.md`
- **iOS代码混淆性能验证** 🚀⚡ - 并行处理功能完整验证 (v2.3.0)
  - **多线程并行解析**: 智能阈值自动选择串行/并行，性能提升 **3-5x**
  - **多进程代码转换**: 绕过Python GIL，处理超大文件性能提升 **2-6x**
  - **两级缓存系统**: 内存+磁盘缓存，重复构建性能提升 **100-300x**
  - **测试验证**: 14/15测试通过（1个跳过），综合加速比 **103x**
  - **使用简单**: 配置文件默认启用，无需手动配置
  - **技术文档**: `docs/technical/PARALLEL_PROCESSING_VALIDATION.md`

### 2025-10-14
- **iOS代码混淆功能** 🔐 - 应对App Store审核(4.3/2.1)的完整解决方案
  - **核心功能完成** (v2.2.0): 完整的混淆引擎，支持ObjC/Swift
    - 15个核心模块：配置管理、白名单、名称生成、项目分析、代码解析/转换等
    - 内置1500+系统API白名单（UIKit/Foundation/CoreGraphics等）
    - 四种命名策略：随机/前缀/模式/词典
    - 确定性混淆：固定种子保证版本迭代一致性
    - 增量混淆：仅混淆新增代码，减少变更影响
  - **P2高级资源处理**: 应对二进制特征检测
    - 图片像素微调：修改RGB值但保持视觉一致
    - Assets.xcassets处理：Contents.json同步更新
    - 音频文件hash修改：metadata和静音段处理
    - 字体文件处理：内部表和元数据修改
  - **代码混淆能力**:
    - ✅ 类名/方法名/属性名/协议名混淆
    - ✅ 垃圾代码生成器（3种复杂度级别）
    - ✅ 字符串加密器（4种加密算法）
    - ✅ 方法重载和重写智能处理
    - ✅ XIB/Storyboard类名同步更新
  - **双界面支持**:
    - GUI界面：配置预设、实时进度、映射查看
    - CLI工具：命令行批量处理、Jenkins/CI集成
  - **企业级特性**:
    - 混淆历史管理和版本控制
    - 增量编译管理（MD5变化检测）
    - 性能分析和统计报告
  - **技术文档**:
    - `gui/modules/obfuscation/CLAUDE.md` - 完整技术文档
    - `docs/technical/IOS_OBFUSCATION_ROADMAP.md` - 后续开发计划
    - 80+个测试用例验证
  - **使用示例**:
    ```bash
    # GUI启动
    ./scripts/run_analyzer.sh
    # 切换到"iOS代码混淆"标签页

    # CLI使用
    python -m gui.modules.obfuscation.obfuscation_cli \
      --project /path/to/project \
      --output /path/to/obfuscated \
      --template standard
    ```

### 2025-10-11
- **阶段二性能优化集成完成** 🚀⚡⚡⚡ - 核心性能突破已全面应用到主程序
  - **自动索引构建**: 加载日志文件后自动异步构建索引，无需手动操作
  - **智能过滤切换**: 索引就绪时自动使用索引过滤，否则降级到普通过滤
  - **实时进度反馈**: 索引构建过程显示实时进度和统计信息
  - **性能指示器**: 界面显示⚡索引或普通状态，让用户了解当前性能模式
  - **无缝体验**: 索引构建在后台进行，不影响正常使用
  - **测试验证**: 所有优化功能通过综合测试，搜索性能提升93%
- **阶段二性能优化完成** 🚀⚡⚡ - 核心性能突破，搜索和加载质的飞跃
  - **倒排索引系统** 🔍: 搜索性能平均提升 **92.8%**
    - 索引构建速度: 79,012 条/秒
    - 搜索响应时间: < 1ms（目标50ms）
    - 级别/模块过滤提升: 99.7%+
    - 关键词搜索提升: 75.3%
    - 测试验证: `tests/test_phase_two_optimization.py` ✅
  - **流式文件加载** 💾: 大文件加载能力大幅提升
    - 编码检测: 0.15ms（原方案秒级）
    - 加载速度: 1200万行/秒
    - 内存优化: 峰值 < 文件大小2倍
    - 支持GB级文件: 无大小限制
    - 智能加载策略: <10MB直接加载，>=10MB流式加载
  - **核心模块** 🆕:
    - `gui/modules/log_indexer.py` - 倒排索引器（388行）
    - `gui/modules/stream_loader.py` - 流式加载器（270行）
  - **完整文档**:
    - `docs/technical/PHASE_TWO_OPTIMIZATION_REPORT.md` - 详细实施报告
  - **用户体验提升**:
    - ⚡ 搜索即时响应 (从秒级降到毫秒级)
    - 💾 支持超大文件 (GB级文件无压力)
    - 🔄 实时进度显示 (索引构建、文件加载)
    - 📊 多维索引加速 (词、模块、级别、时间)
- **阶段一性能优化完成** 🚀⚡ - 全面提升系统性能和用户体验
  - **内存优化 (LogEntry.__slots__)**: 内存占用减少 **69.8%**
    - 100万条日志: 328MB → 99MB (节省229MB)
    - 单个对象: 344字节 → 104字节
    - 测试验证: `tests/test_memory_optimization.py` ✅
  - **搜索优化 (正则预编译缓存)**: 搜索速度提升 **37.2%**
    - 100万条正则搜索: 0.071秒 → 0.045秒
    - 缓存命中时速度提升更明显 (69%)
    - 测试验证: `tests/test_regex_optimization.py` ✅
  - **UI渲染优化 (批量渲染)**: 渲染速度提升 **65%**
    - 500条日志: 1.0秒 → 0.35秒
    - 5000条日志: 0.025秒 (超快响应)
    - 测试验证: `tests/test_ui_rendering.py` ✅
  - **结构化日志系统**: 全新的日志记录和性能监控系统
    - 自动性能日志记录
    - 文件和控制台双输出
    - 日志自动轮转管理
    - 装饰器和上下文管理器支持
  - **Bug修复**: 修复过滤功能中的 keyword_lower 问题
    - 测试验证: `tests/test_bugfix_filter.py` ✅
  - **完整文档**:
    - `docs/technical/OPTIMIZATION_ANALYSIS.md` - 详细优化分析
    - `docs/technical/PHASE_ONE_OPTIMIZATION_REPORT.md` - 实施报告
    - `docs/technical/BUGFIX_PHASE_ONE.md` - Bug修复记录
  - **用户体验提升**:
    - ⚡ 更快的启动速度 (内存占用减少)
    - 🔍 更快的搜索响应 (正则搜索接近即时)
    - 📜 更流畅的滚动体验 (无卡顿感)
    - 🐛 更好的问题追踪 (完整日志系统)
- **dSYM模块化重构** 🏗️ - 文件管理、UUID解析、符号化职责分离
  - **模块拆分**：508行单文件拆分为3个独立模块
  - **dsym_file_manager.py**：负责xcarchive/dSYM文件管理
  - **dsym_uuid_parser.py**：使用dwarfdump提取UUID和架构信息
  - **dsym_symbolizer.py**：使用atos进行崩溃地址符号化和IPA导出
  - **代码简化**：dsym_tab.py 从508行缩减到392行
  - **架构优化**：采用文件加载→UUID解析→符号化的数据流设计
  - **文档完善**：新增详细的CLAUDE.md技术文档
- **LinkMap模块化重构** 🏗️ - 解析、分析、格式化职责分离
  - **模块拆分**：651行单文件拆分为3个独立模块
  - **linkmap_parser.py**：专注LinkMap文件解析
  - **linkmap_analyzer.py**：数据统计、分组、过滤分析
  - **linkmap_formatter.py**：格式化输出和报告生成
  - **代码简化**：linkmap_tab.py 从651行缩减到360行
  - **架构优化**：采用解析→分析→格式化的数据流设计
  - **文档完善**：新增详细的CLAUDE.md技术文档
- **iOS沙盒浏览性能优化** ⚡ - 应用权限检测速度提升5倍
  - **多线程并发检测**：5个线程同时检测，大幅提升速度
  - **超时保护**：单个应用检测不超过2秒，避免卡顿
  - **实时进度更新**：边检测边显示，无需等待全部完成
  - **性能提升**：30个应用从60-90秒缩短到12-18秒
- **iOS沙盒浏览改进** 📷 - 图片文件"打开"功能优化
  - **UI层面限制**：图片文件不再显示"打开"选项，避免连接断开
  - **动态右键菜单**：根据文件类型自动调整菜单项
  - **友好提示**：点击"打开文件"按钮时引导用户使用"预览"或"导出"
  - **用户体验改进**：彻底解决图片打开导致的界面刷新和目录折叠问题
  - 保留"预览"（程序内查看）和"导出"（保存到本地）两种查看方式

### 2025-10-10
- **iOS沙盒浏览优化** 🚀 - 智能应用过滤和自动加载
  - **应用列表智能过滤**：加载应用列表时预先检测访问权限，只显示可访问的应用
  - **实时检测进度**：显示访问权限检测进度（已检测 n/total）
  - **过滤统计信息**：显示已加载和已过滤的应用数量
  - **自动加载首个应用**：首次进入标签页时自动加载第一个可访问的应用
  - **避免无效选择**：用户不会看到或选择到无法访问的应用
  - 解决 InstallationLookupFailed 错误困扰
- **自定义模块分组规则** 🎯 - 用户可自定义模块分组逻辑
  - 新增"自定义规则"按钮，GUI界面管理规则（添加/编辑/删除）
  - 支持两种匹配模式：
    - **字符串模式**：简单包含匹配，检查内容是否包含指定字符串
    - **正则模式**：正则表达式匹配，支持捕获组提取清理后的内容
  - 规则持久化到 `gui/custom_module_rules.json` 文件
  - 动态应用：自动应用到所有新加载的日志文件
  - 优先级：内置模块标识 > 自定义规则 > 默认模块标签

### 2025-10-09
- **UI交互体验优化** 🎨 - 文本选择和界面布局改进
  - 修复文本组件选择高亮问题，支持 Cmd+C/Ctrl+C 复制
  - 移除标签背景色避免覆盖选择高亮
  - 优化只读保护机制，允许复制操作同时阻止编辑
  - 搜索与过滤区域移至日志查看标签页内，界面更清晰
  - 紧凑布局：从4行压缩为2行，非全屏模式完整显示
- **日志模块分组增强** ✨ - 支持更多模块分组格式
  - 新增支持 `<Chair>` 格式：`[<Chair> 日志内容]`
  - 新增支持 `[Plugin]` 格式：`[[Plugin] 日志内容]`
  - 保持原有 `<AnimationCenter>` 格式支持
  - 自动提取并归类到对应模块
- **崩溃日志检测优化** 🔧 - 修复懒加载导致的崩溃检测问题
  - 修复多行崩溃堆栈合并导致的检测失败
  - 每个堆栈行单独创建LogEntry，确保正确识别
  - iOS堆栈格式完全支持（包括 `*** First throw call stack` 和地址格式）
  - Crash模块自动置顶显示，方便快速定位崩溃信息
  - 崩溃日志去重功能，基于时间戳+内容自动去除重复
- **代码架构优化** 🏗️ - 统一LogEntry数据模型
  - 移除重复的LogEntry类定义
  - 统一使用 `gui/modules/data_models.py` 中的LogEntry
  - 避免代码重复和维护问题

### 2025-09-29
- **dSYM文件分析功能** 🆕 - iOS崩溃符号化和代码定位工具
  - 自动加载本地Xcode Archives文件
  - 支持手动加载.dSYM文件（macOS原生文件选择器）
  - 使用dwarfdump获取UUID信息
  - 使用atos进行崩溃地址符号化
  - 支持多架构（armv7/arm64等）
  - 导出IPA功能
- **LinkMap文件分析功能** 🆕 - iOS应用二进制大小分析工具
  - 解析Link Map文件，统计代码大小
  - 符号大小统计和排序
  - 未使用代码（Dead Code）分析
  - 按库分组统计功能
  - 搜索和过滤功能
  - 格式化输出和导出报告

### 2025-09-28
- **iOS沙盒浏览功能** 🆕 - 完整的iOS应用沙盒文件浏览器
  - 设备管理：自动检测iOS设备，显示设备名称和型号
  - 应用列表：列出所有用户应用
  - 文件浏览：树形结构展示应用沙盒文件系统，支持多级目录
  - 文件操作：预览、导出、打开、删除文件
  - 文件预览：支持文本、图片、JSON、十六进制等多种格式
- **PyInstaller打包支持** - 使用PyInstaller替代py2app创建独立应用
- **一键打包脚本** - `./scripts/build_app.sh` 自动化打包流程
- **完整打包文档** - 详细的打包、分发和故障排除指南
- **独立运行** - 生成的.app文件无需Python环境即可运行

### 2025-09-27
- **模块化重构完成** - 将3784行单文件拆分为清晰的模块结构
- **集成iOS推送测试功能** - 完整的APNS推送测试工具已集成到主程序
- **统一的GUI界面** - Mars日志分析、IPS崩溃解析、iOS推送测试四合一
- **智能依赖管理** - 自动检测和安装所有必要的依赖包
- **完全可移植** - 项目可放置在任何路径下运行
- **时间过滤增强** - 支持带时区的时间格式，Enter键快速应用过滤

## 核心组件

### 解码器系列 (decoders/)
- `decode_mars_nocrypt_log_file.py` - 原始 Python 2 版本解码脚本
- `decode_mars_nocrypt_log_file_py3.py` - Python 3 兼容版本
  - 支持多种压缩格式（MAGIC_COMPRESS_START、MAGIC_NO_COMPRESS_START 等）
  - 支持加密（4字节或64字节密钥）和非加密日志格式
  - 使用 zlib 进行解压缩
  - 验证日志缓冲区完整性并优雅处理损坏的数据
- `fast_decoder.py` - 高性能解码器
  - 优化的解码算法，提升解析速度
  - 减少内存占用
  - 适合批量处理大文件
- `optimized_decoder.py` - 优化版解码器
  - 改进的错误处理机制
  - 更好的内存管理
  - 支持流式处理

### GUI分析系统 (gui/)

#### 主程序
- `mars_log_analyzer_modular.py` - 模块化版本（当前使用）
  - 继承自原始版本，逐步重构
  - 使用模块化组件
  - 保持100%功能兼容
- `mars_log_analyzer_pro.py` - 原始专业版（作为基类保留）
  - 完整功能实现
  - 单文件3784行
  - 作为模块化版本的基类

#### 模块化组件 (gui/modules/)
- `data_models.py` - 数据模型（阶段一优化 ✅）
  - LogEntry: 日志条目类（使用__slots__优化）
  - FileGroup: 文件分组类
- `file_operations.py` - 文件操作
  - 文件加载和解码
  - 多格式导出（TXT/JSON/CSV）
- `filter_search.py` - 过滤搜索（阶段一优化 ✅）
  - 统一的过滤逻辑
  - 时间解析和比较
  - 正则表达式预编译缓存
- `log_indexer.py` - 倒排索引系统（阶段二新增 🆕）
  - 多维索引（词、模块、级别、时间）
  - Trigram模糊搜索
  - 异步索引构建
  - 增量索引更新
- `stream_loader.py` - 流式文件加载（阶段二新增 🆕）
  - 快速编码检测
  - 分块流式读取
  - 内存受限模式
  - 智能加载策略
- `logging_config.py` - 结构化日志系统（阶段一新增 🆕）
  - 性能监控装饰器
  - 日志轮转管理
  - 上下文管理器
- `ai_assistant_panel.py` - AI助手面板（2025-10-16新增 🤖🆕）
  - AI助手侧边栏UI（600行）
  - 4个快捷操作按钮
  - 聊天历史显示
  - 自由问答输入
- `ai_diagnosis_settings.py` - AI设置对话框（2025-10-16新增 🤖🆕）
  - AI服务配置对话框（400行）
  - API Key管理
  - 自动检测功能
  - 测试连接
- `ai_diagnosis/` - AI诊断核心模块（2025-10-16新增 🤖🆕）
  - `ai_client.py` - AI客户端抽象层和工厂（590行）
  - `config.py` - 配置管理（245行）
  - `log_preprocessor.py` - 日志预处理器（610行）
  - `prompt_templates.py` - 提示词模板库（515行）
  - `claude_code_client.py` - Claude Code代理客户端（433行）
  - 技术文档：`CLAUDE.md`
- `ips_tab.py` - IPS崩溃分析标签页
  - iOS崩溃报告解析
  - 符号化支持
- `push_tab.py` - iOS推送测试标签页
  - APNS推送发送
  - 证书管理
- `sandbox_tab.py` - iOS沙盒浏览标签页
  - 设备和应用管理
  - 文件系统浏览
  - 文件预览和操作
- `dsym_tab.py` - dSYM文件分析标签页（重构版） 🆕
  - 使用模块化组件架构
  - 代码从508行缩减到392行
  - dsym/ 子模块:
    - `dsym_file_manager.py` - xcarchive/dSYM文件管理
    - `dsym_uuid_parser.py` - UUID和架构信息解析
    - `dsym_symbolizer.py` - 崩溃地址符号化和IPA导出
    - `CLAUDE.md` - 技术文档
- `linkmap_tab.py` - LinkMap分析标签页（重构版） 🆕
  - 使用模块化组件架构
  - 代码从651行缩减到360行
  - linkmap/ 子模块:
    - `linkmap_parser.py` - LinkMap文件解析
    - `linkmap_analyzer.py` - 数据统计和分析
    - `linkmap_formatter.py` - 格式化输出
    - `CLAUDE.md` - 技术文档

#### UI组件 (gui/components/)
- `improved_lazy_text.py` - 改进版懒加载文本组件
  - 虚拟滚动实现
  - LRU缓存策略
  - 支持百万级数据
  - 支持文本选择和复制（Cmd+C/Ctrl+C）
  - 智能只读保护（阻止编辑但允许复制）
  - 可配置选择高亮颜色
- `scrolled_text_with_lazy_load.py` - 懒加载滚动文本组件
  - 基础懒加载实现
  - 作为备用方案
  - 同样支持文本选择和复制

### 辅助工具 (tools/)
- `ips_parser.py` - IPS崩溃日志解析器
  - 解析iOS崩溃报告
  - 符号化堆栈跟踪
  - 提取关键崩溃信息

### 启动和打包脚本 (scripts/)
- `run_analyzer.sh` - 主程序启动脚本（自动创建虚拟环境和安装依赖）
- `run_push_tool.sh` - iOS推送工具独立启动脚本
- `build_app.sh` - PyInstaller一键打包脚本（创建独立应用）
- `setup.py` - py2app打包配置（已弃用，保留作参考）

### iOS推送测试工具 (push_tools/)
- iOS APNS推送测试模块（**已集成到主程序**）
  - `apns_push.py` - 推送核心逻辑实现
    - 证书管理（支持.p12/.pem/.cer格式）
    - HTTP/2推送发送
    - 推送历史记录
    - 沙盒和生产环境支持
  - `apns_gui.py` - 推送测试GUI界面
    - 友好的图形界面
    - Payload模板快速选择
    - 实时日志和历史记录
    - **可独立运行或嵌入主程序标签页**
  - `test_push.py` - 功能测试脚本
  - `requirements.txt` - 推送工具依赖

### 文档 (docs/)
- `README_CN.md` - 中文说明文档
- `README_EN.md` - 英文说明文档
- `BUILD.md` - 打包和分发指南
- `technical/` - 技术文档目录 🆕
  - `OPTIMIZATION_ANALYSIS.md` - 性能优化分析报告（28KB）
  - `PHASE_ONE_OPTIMIZATION_REPORT.md` - 阶段一优化实施报告（11KB）
  - `PHASE_TWO_OPTIMIZATION_REPORT.md` - 阶段二优化实施报告
  - `BUGFIX_PHASE_ONE.md` - 阶段一Bug修复记录（4.4KB）
  - `SANDBOX_BUGFIX.md` - iOS沙盒浏览Bug修复记录
  - `SANDBOX_REFACTORING.md` - iOS沙盒浏览模块重构总结
  - `DSYM_LINKMAP.md` - dSYM和LinkMap分析技术文档
  - `PARALLEL_PROCESSING_VALIDATION.md` - 并行处理功能验证报告
  - `MODULE_LIST_SEARCH.md` - 模块列表搜索功能技术文档
  - `AI_INTEGRATION_COMPLETE.md` - AI集成总体完成报告 🤖🆕
  - `AI_INTEGRATION_PROGRESS.md` - AI集成进度跟踪
  - `AI_INTEGRATION_PHASE1_SUMMARY.md` - AI集成Phase 1总结
  - `AI_INTEGRATION_PHASE2_COMPLETE.md` - AI集成Phase 2完成报告
  - `AI_INTEGRATION_PHASE3_COMPLETE.md` - AI集成Phase 3完成报告

## 使用命令

### 启动GUI分析系统（推荐）：
```bash
# 使用启动脚本（推荐，自动处理依赖和环境）
./scripts/run_analyzer.sh

# 或手动启动（需要先激活虚拟环境）
source venv/bin/activate
python3 gui/mars_log_analyzer_modular.py
```

#### 功能说明
主程序包含七个标签页 + AI助手侧边栏：
1. **Mars日志分析** - 解码和分析xlog文件 + **AI助手侧边栏** 🤖🆕
   - 左侧（75%）：传统日志查看、搜索、过滤功能
   - 右侧（25%）：AI智能诊断助手
     - 崩溃分析、性能诊断、问题总结、智能搜索
     - 自由对话、右键菜单AI分析
2. **IPS崩溃解析** - 解析iOS崩溃报告
3. **iOS推送测试** - APNS推送测试工具
4. **iOS沙盒浏览** - iOS应用沙盒文件浏览器
5. **dSYM分析** - iOS崩溃符号化和代码定位
6. **LinkMap分析** - iOS应用二进制大小分析
7. **iOS代码混淆** - iOS项目代码混淆工具

### 独立启动iOS推送工具：
```bash
# 独立启动推送工具GUI
./scripts/run_push_tool.sh

# 或直接运行
python3 push_tools/apns_gui.py

# 命令行使用
python3 push_tools/apns_push.py --cert cert.p12 --token "device_token" --message "测试消息" --sandbox
```

### 命令行解码：

#### 基础解码
```bash
# Python 3版本解码单个文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py mizhua_20250915.xlog

# 批量解码当前目录所有xlog文件
python3 decoders/decode_mars_nocrypt_log_file_py3.py

# 解码指定目录
python3 decoders/decode_mars_nocrypt_log_file_py3.py /path/to/xlog/directory/
```

#### 高性能解码
```bash
# 使用快速解码器（大文件推荐）
python3 decoders/fast_decoder.py input.xlog

# 使用优化解码器（内存优化）
python3 decoders/optimized_decoder.py input.xlog
```

### IPS崩溃日志分析：
```bash
# 解析iOS崩溃报告
python3 tools/ips_parser.py crash.ips
```

### 打包成独立应用：
```bash
# 一键打包（推荐）
./scripts/build_app.sh

# 手动打包
source venv/bin/activate
pyinstaller --clean MarsLogAnalyzer.spec

# 打包结果
# dist/MarsLogAnalyzer.app - 可在任何Mac上运行的独立应用
```

详细的打包和分发说明请参考 [BUILD.md](docs/BUILD.md)

### iOS代码混淆：

#### GUI使用
```bash
# 启动主程序
./scripts/run_analyzer.sh

# 在主程序中选择"iOS代码混淆"标签页
# 1. 选择项目和输出目录
# 2. 配置混淆选项（或使用快速配置模板）
# 3. 点击"开始混淆"
# 4. 查看实时进度和日志
# 5. 混淆完成后查看/导出映射文件
```

#### CLI使用
```bash
# 基础混淆（使用标准模板）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/ios/project \
    --output /path/to/obfuscated \
    --template standard

# 自定义配置
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --class-names \
    --method-names \
    --property-names \
    --prefix "WHC" \
    --seed "my_project_v1.0"

# 增量混淆（保持旧版本映射）
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --output /path/to/output \
    --incremental \
    --mapping /path/to/old_mapping.json

# 只分析不混淆
python -m gui.modules.obfuscation.obfuscation_cli \
    --project /path/to/project \
    --analyze-only \
    --report analysis_report.json
```

详细的混淆功能说明请参考：
- 技术文档：`gui/modules/obfuscation/CLAUDE.md`
- 开发计划：`docs/technical/IOS_OBFUSCATION_ROADMAP.md`

## 重要说明

### 系统要求
- Python 3.6+ （推荐3.8+）
- GUI系统需要 tkinter 和 matplotlib 库
- 原始脚本支持 Python 2，但推荐使用 Python 3 版本

### 性能建议
- 小文件（<10MB）：使用基础解码器即可
- 大文件（>10MB）：推荐使用 `fast_decoder.py` 或 `optimized_decoder.py`
- 批量处理：使用 `mars_log_analyzer_pro.py` GUI工具
- 内存限制环境：使用 `optimized_decoder.py` 的流式处理

### 技术特性
- 自动检测并处理各种 Mars 日志格式版本
- 验证序列号以检测丢失的日志条目
- 支持压缩和加密日志的解码
- GUI系统采用懒加载技术，可处理GB级日志文件
- 所有解码器都具有完善的错误处理机制

## 日志格式详情

### Mars xlog 格式规范
- 魔数字节表示压缩和加密状态：
  - 0x03, 0x04, 0x05：4字节密钥格式
  - 0x06, 0x07, 0x08, 0x09：64字节密钥格式
- 头部结构：magic_start (1字节) + seq (2字节) + begin_hour (1字节) + end_hour (1字节) + length (4字节) + crypt_key
- 每个日志条目以 MAGIC_END (0x00) 结尾

### 支持的日志级别
- ERROR: 错误日志
- WARNING: 警告日志
- INFO: 信息日志
- DEBUG: 调试日志
- VERBOSE: 详细日志

## 环境管理

### 项目可移植性
项目设计为完全可移植，可以放置在任何路径下运行：
- **无硬编码路径** - 所有路径都是相对于项目根目录
- **自动环境管理** - 启动脚本自动处理虚拟环境
- **智能依赖检测** - 自动检查并安装缺失的依赖

### 虚拟环境
项目使用Python虚拟环境隔离依赖：
```bash
# 自动方式（推荐）
./scripts/run_analyzer.sh  # 自动创建venv并安装依赖

# 手动方式
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 依赖管理
所有项目依赖都在`requirements.txt`中定义：
- **matplotlib** - 图表绘制
- **cryptography** - 证书处理
- **httpx** - HTTP/2客户端
- **pyjwt** - JWT处理
- **h2** - HTTP/2协议
- **pyinstaller** - 应用打包工具（可选，仅打包时需要）

### 常见问题

#### Q: 提示"No module named 'cryptography'"？
**解决方案**：
1. 确保在项目根目录（包含venv文件夹的目录）
2. 激活虚拟环境：`source venv/bin/activate`
3. 重新安装依赖：`pip install -r requirements.txt`

#### Q: 虚拟环境路径混乱？
**解决方案**：
```bash
# 删除旧的虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv

# 安装依赖
source venv/bin/activate
pip install -r requirements.txt
```

#### Q: iOS推送功能无法加载？
**解决方案**：
使用`./scripts/run_analyzer.sh`启动，它会自动处理所有依赖。

## 技术文档目录说明 🆕

项目中所有重构文档、Bug修复记录、技术说明等文档统一存放在 `docs/technical/` 目录下，便于集中管理和查阅。

### 文档分类

#### Bug修复记录
- **SANDBOX_BUGFIX.md** - iOS沙盒浏览功能的Bug修复详细记录
  - 记录问题症状和触发场景
  - 分析问题根本原因
  - 详细的解决方案和代码修改
  - 修复后的测试验证结果

#### 重构总结
- **SANDBOX_REFACTORING.md** - iOS沙盒浏览模块化重构总结
  - 重构前后的代码行数对比
  - 模块拆分的架构设计
  - 重构带来的优势说明
  - 未来优化建议

#### 技术文档
- **DSYM_LINKMAP.md** - dSYM文件分析和LinkMap文件分析技术文档
  - 功能概述和使用流程
  - 核心技术实现细节
  - 集成方式和依赖要求
  - 故障排查和最佳实践

### 文档规范

所有技术文档应遵循以下规范：
1. **标题清晰**：使用描述性的标题，一目了然
2. **结构完整**：包含问题描述、分析、解决方案、测试验证
3. **代码示例**：提供清晰的代码示例和对比
4. **版本信息**：记录文档创建/更新日期和版本
5. **统一格式**：使用Markdown格式，遵循项目风格

### 新增技术文档指南

当需要添加新的技术文档时：
1. 在 `docs/technical/` 目录创建Markdown文件
2. 使用描述性的文件名（大写+下划线分隔）
3. 遵循现有文档的结构模板
4. 在主CLAUDE.md中更新文档列表
5. 提交时使用 `docs:` 前缀标记

## 开发指南

### 项目结构
```
.
├── decoders/                                 # 解码器核心模块
│   ├── decode_mars_nocrypt_log_file_py3.py  # 基础解码器
│   ├── decode_mars_nocrypt_log_file.py      # Python 2版解码器
│   ├── fast_decoder.py                       # 高性能解码器
│   └── optimized_decoder.py                  # 优化解码器
├── gui/                                      # GUI应用程序
│   ├── mars_log_analyzer_modular.py          # 模块化版本（当前使用）
│   ├── mars_log_analyzer_pro.py              # 原始专业版（基类）
│   ├── modules/                              # 模块化组件
│   │   ├── data_models.py                    # 数据模型
│   │   ├── file_operations.py                # 文件操作
│   │   ├── filter_search.py                  # 过滤搜索
│   │   ├── ips_tab.py                        # IPS标签页
│   │   ├── push_tab.py                       # 推送标签页
│   │   ├── sandbox_tab.py                    # 沙盒浏览标签页
│   │   ├── dsym_tab.py                       # dSYM分析标签页（重构版）
│   │   ├── linkmap_tab.py                    # LinkMap分析标签页（重构版）
│   │   ├── obfuscation_tab.py                # iOS代码混淆标签页 🆕
│   │   ├── dsym/                             # dSYM模块化组件
│   │   │   ├── dsym_file_manager.py          # 文件管理器
│   │   │   ├── dsym_uuid_parser.py           # UUID解析器
│   │   │   ├── dsym_symbolizer.py            # 符号化器
│   │   │   └── CLAUDE.md                     # 模块技术文档
│   │   ├── linkmap/                          # LinkMap模块化组件 🆕
│   │   │   ├── linkmap_parser.py             # LinkMap解析器
│   │   │   ├── linkmap_analyzer.py           # 数据分析器
│   │   │   ├── linkmap_formatter.py          # 格式化输出
│   │   │   └── CLAUDE.md                     # 模块技术文档
│   │   ├── sandbox/                          # 沙盒浏览模块化组件
│   │   │   ├── device_manager.py             # 设备管理
│   │   │   ├── app_manager.py                # 应用管理
│   │   │   ├── file_browser.py               # 文件浏览
│   │   │   ├── file_operations.py            # 文件操作
│   │   │   ├── file_preview.py               # 文件预览
│   │   │   ├── search_manager.py             # 搜索功能
│   │   │   └── CLAUDE.md                     # 模块技术文档
│   │   └── obfuscation/                      # iOS代码混淆模块化组件 🆕
│   │       ├── config_manager.py             # 配置管理器
│   │       ├── whitelist_manager.py          # 白名单管理器
│   │       ├── name_generator.py             # 名称生成器
│   │       ├── project_analyzer.py           # 项目分析器
│   │       ├── code_parser.py                # 代码解析器
│   │       ├── code_transformer.py           # 代码转换器
│   │       ├── resource_handler.py           # 资源文件处理器
│   │       ├── advanced_resource_handler.py  # 高级资源处理器
│   │       ├── obfuscation_engine.py         # 混淆引擎核心
│   │       ├── obfuscation_cli.py            # CLI命令行工具
│   │       ├── garbage_generator.py          # 垃圾代码生成器
│   │       ├── string_encryptor.py           # 字符串加密器
│   │       ├── incremental_manager.py        # 增量编译管理器
│   │       └── CLAUDE.md                     # 模块技术文档
│   └── components/                           # UI组件
│       ├── improved_lazy_text.py             # 改进版懒加载文本
│       └── scrolled_text_with_lazy_load.py   # 懒加载滚动文本
├── push_tools/                               # iOS推送测试工具（新增）
│   ├── __init__.py                           # 模块初始化
│   ├── apns_push.py                          # 推送核心逻辑
│   ├── apns_gui.py                           # 推送GUI界面
│   ├── test_push.py                          # 功能测试脚本
│   ├── requirements.txt                      # 推送工具依赖
│   └── README.md                             # 推送工具文档
├── tools/                                    # 工具脚本
│   └── ips_parser.py                         # IPS崩溃日志解析器
├── scripts/                                  # 启动和打包脚本
│   ├── run_analyzer.sh                       # 主程序启动脚本
│   ├── run_push_tool.sh                      # 推送工具启动脚本
│   ├── build_app.sh                          # PyInstaller打包脚本
│   └── setup.py                              # py2app打包配置（已弃用）
├── docs/                                     # 文档目录
│   ├── README_CN.md                          # 中文文档
│   ├── README_EN.md                          # 英文文档
│   ├── BUILD.md                              # 打包分发指南
│   ├── technical/                            # 技术文档目录
│   │   ├── OPTIMIZATION_ANALYSIS.md          # 性能优化分析报告
│   │   ├── PHASE_ONE_OPTIMIZATION_REPORT.md  # 阶段一优化实施报告
│   │   ├── PHASE_TWO_OPTIMIZATION_REPORT.md  # 阶段二优化实施报告
│   │   ├── BUGFIX_PHASE_ONE.md               # 阶段一Bug修复记录
│   │   ├── SANDBOX_BUGFIX.md                 # iOS沙盒浏览Bug修复记录
│   │   ├── SANDBOX_REFACTORING.md            # iOS沙盒浏览模块重构总结
│   │   ├── DSYM_LINKMAP.md                   # dSYM和LinkMap分析技术文档
│   │   ├── IOS_OBFUSCATION_PROGRESS.md       # iOS混淆开发进度报告
│   │   ├── IOS_OBFUSCATION_DESIGN.md         # iOS混淆设计文档
│   │   ├── IOS_OBFUSCATION_ROADMAP.md        # iOS混淆后续开发计划
│   │   ├── PARALLEL_PROCESSING_VALIDATION.md # 并行处理功能验证报告
│   │   └── MODULE_LIST_SEARCH.md             # 模块列表搜索功能 🆕
│   └── CLAUDE.md                             # 项目指南（本文件）
├── MarsLogAnalyzer.spec                      # PyInstaller配置文件
├── build/                                    # 构建临时文件（自动生成）
├── dist/                                     # 打包输出目录（自动生成）
└── venv/                                     # Python虚拟环境（自动生成）
```

### 贡献指南
1. 保持代码风格一致性
2. 添加适当的错误处理
3. 新功能需要更新相应文档
4. 性能优化需要提供基准测试结果

## 功能使用说明

### 界面布局
- **日志查看标签页**：包含完整的搜索与过滤功能
  - 关键词搜索（支持字符串/正则模式）
  - 日志级别过滤
  - 模块过滤
  - 时间范围过滤
  - 导出功能
- **模块分组标签页**：
  - 模块列表实时搜索：快速定位目标模块 🆕
  - 模块内搜索：在选定模块的日志中搜索
- 紧凑的2行布局设计，非全屏模式下完整显示所有功能

### 文本选择和复制
所有日志文本区域支持：
- ✅ **鼠标选择**：拖动鼠标选择文本，蓝色高亮显示
- ✅ **键盘快捷键**：Cmd+C (macOS) 或 Ctrl+C (Windows/Linux) 复制
- ✅ **全选**：Cmd+A 或 Ctrl+A
- ✅ **右键菜单**：系统原生的复制功能
- ✅ **失去焦点保持高亮**：浅蓝色显示选中区域
- ❌ **只读保护**：阻止键盘输入和粘贴，但不影响复制

### 时间过滤功能
GUI提供强大的时间过滤功能，支持多种时间格式输入：

#### 支持的时间格式
- **完整格式**: `2025-09-21 14:00:00` - 精确到秒
- **日期格式**: `2025-09-21` - 过滤整天的日志
- **时间格式**: `14:00:00` 或 `14:00` - 跨天过滤特定时间段
- **留空**: 开始时间留空表示从最早，结束时间留空表示到最后

#### 使用方法
1. 在时间范围输入框中输入开始和结束时间
2. 按Enter键或点击"应用过滤"按钮
3. 切换日志级别或模块会自动应用所有过滤条件

#### 支持的日志时间戳格式
- 带时区：`[2025-09-21 +8.0 13:09:49.038]`
- 无时区：`[2025-09-21 13:09:49.038]`
- 标准格式：`2025-09-21 13:09:49`

### 搜索功能
- **普通搜索**: 输入关键词进行字符串匹配
- **正则搜索**: 切换到"正则"模式使用正则表达式
- **快捷键**: 在搜索框按Enter键立即搜索
- **高亮显示**: 搜索结果自动高亮显示

### 自定义模块分组规则 🎯

#### 功能介绍
允许用户定义自己的日志模块分组规则，实现更灵活的日志分类。

#### 使用方法
1. 切换到"模块分组"标签页
2. 点击模块列表右上方的"自定义规则"按钮
3. 在弹出的规则管理对话框中：
   - **添加规则**：点击"添加"按钮，输入规则名称、匹配模式、目标模块名和匹配类型
   - **编辑规则**：选中规则后点击"编辑"按钮修改
   - **删除规则**：选中规则后点击"删除"按钮移除
   - **应用规则**：点击"应用规则"重新加载日志应用新规则

#### 匹配类型
- **字符串模式**：
  - 简单的包含匹配，检查日志内容中是否包含指定字符串
  - 示例：输入 `Animation` 可匹配所有包含"Animation"的日志
  - 不修改日志内容
- **正则模式**：
  - 使用正则表达式匹配
  - 支持捕获组提取并清理日志内容
  - 示例：`^\[<Chair>\s*(.*)$` 匹配 `[<Chair> xxx` 格式并提取 `xxx` 作为内容
  - 更灵活但需要正则表达式知识

#### 规则优先级
内置模块标识（如 `<Chair>`, `[Plugin]`）> 自定义规则 > 默认模块标签

#### 规则存储
- 规则保存在 `gui/custom_module_rules.json` 文件
- 格式示例：
```json
[
  {
    "name": "动画模块",
    "pattern": "Animation",
    "module": "Animation",
    "type": "字符串"
  },
  {
    "name": "Chair格式",
    "pattern": "^\\[<Chair>\\s*(.*)$",
    "module": "Chair",
    "type": "正则"
  }
]
```

### 模块列表搜索功能 🔍

#### 功能介绍
在模块分组标签页的模块列表上方提供实时搜索功能，帮助用户在大量模块中快速定位目标模块。

#### 使用方法
1. 切换到"模块分组"标签页
2. 在模块列表上方的搜索框中输入关键词
3. 列表自动过滤，只显示包含关键词的模块
4. 点击"×"按钮或清空搜索框恢复显示所有模块

#### 功能特性
- **实时搜索**: 输入即搜索，无需点击按钮
- **不区分大小写**: 自动忽略大小写进行匹配
- **部分匹配**: 只要模块名包含关键词即可匹配
- **保持排序**: Crash模块始终置顶，其他模块按字母排序
- **统计完整**: 保留每个模块的日志数、崩溃数、错误数、警告数统计
- **一键清除**: "×"按钮快速清空搜索并显示所有模块
- **选择保持**: 当前选中模块仍在过滤结果中时自动保持选中状态

#### 使用示例
```
搜索"net"    → 显示：NetworkManager, NetworkService
搜索"anim"   → 显示：AnimationCenter, AnimationEngine
搜索"cache"  → 显示：CacheManager
清空搜索     → 显示所有模块
```

#### 技术实现
- 位置：`gui/mars_log_analyzer_pro.py:306-317` (UI组件)
- 过滤方法：`gui/mars_log_analyzer_pro.py:1413-1471` (filter_module_list)
- Python 3.13兼容：使用 `trace_add('write')` 实现实时监听
- 详细文档：`docs/technical/MODULE_LIST_SEARCH.md`

### iOS沙盒浏览功能 🆕

#### 功能特性
- **设备管理**: 自动检测连接的iOS设备，显示完整设备名称和型号
- **智能应用列表** 🚀:
  - **预先过滤**：加载时自动检测访问权限，只显示可访问的应用
  - **实时进度**：显示访问权限检测进度（已检测 n/total）
  - **统计信息**：显示已加载和已过滤的应用数量
  - **自动加载**：首次进入时自动加载第一个可访问的应用
  - **避免错误**：用户不会看到无法访问的应用，杜绝 InstallationLookupFailed 错误
- **文件浏览**: 树形结构展示应用沙盒文件系统，支持多级目录
- **文件搜索**:
  - 🔍 支持文件名搜索：快速查找包含关键词的文件或目录
  - 📄 支持文件内容搜索：在文本文件内容中搜索关键词
  - 🚀 异步搜索：不阻塞UI的后台搜索
  - 🎯 结果高亮：搜索结果用蓝色显示，带[文件名]或[文件内容]标签
- **文件预览**:
  - 📝 文本文件：.txt, .log, .json, .xml, .plist, .html, .css, .js, .py, .md, .sh, .h, .m, .swift等
  - 🖼️ 图片文件：.png, .jpg, .jpeg, .gif, .bmp, .ico（需要Pillow库）
  - 🔢 十六进制：其他未识别格式显示hex dump
  - 💾 数据库：识别SQLite数据库文件
- **文件操作**:
  - 预览：在程序内查看文件内容（推荐用于图片）
  - 导出：将文件或目录导出到本地
  - 打开：使用系统默认程序打开文件（图片文件不支持，避免连接断开）
  - 删除：删除文件或目录（不可恢复）
  - 刷新：重新加载当前目录

#### 使用方法
1. 连接iOS设备到Mac
2. 打开"iOS沙盒浏览"标签页
3. 在设备下拉框选择设备（显示设备名称、型号和UDID）
4. 等待应用列表加载（会自动过滤不可访问的应用）
5. 应用列表中只显示可访问的应用，自动加载第一个应用
6. 点击目录左侧的▶箭头展开目录
7. 双击文件预览，右键显示更多操作

#### 依赖要求
```bash
pip install pymobiledevice3  # iOS设备通信
pip install Pillow           # 图片预览（可选）
```

## 常见问题

### Q: 解码后的文件在哪里？
A: 默认保存在原xlog文件同目录，文件名添加.log后缀

### Q: 如何处理加密的日志？
A: 当前工具主要处理非加密或标准加密格式，特殊加密需要提供密钥

### Q: GUI程序打不开怎么办？
A: 使用 run_analyzer.sh 脚本，它会自动安装所需依赖

### Q: 支持哪些操作系统？
A: macOS、Linux、Windows（需要Python环境）

### Q: iOS推送功能如何使用？
A: 有两种方式：
1. 在主程序中点击"iOS推送测试"标签页
2. 独立运行`./scripts/run_push_tool.sh`

### Q: 推送证书如何获取？
A: 从Apple开发者中心下载，导出为.p12格式（包含私钥）

### Q: iOS沙盒浏览中为什么图片文件不能使用"打开"功能？
A: 打开图片文件会导致系统预览程序保持文件句柄，引发iOS设备连接断开和界面刷新（目录折叠）。

**当前解决方案（v2.1.0）**：
- ✅ 图片文件右键菜单不显示"打开"选项
- ✅ 点击底部"打开文件"按钮时给出友好提示
- ✅ 引导用户使用"预览"（程序内查看）或"导出"（保存到本地）
- ✅ 彻底避免连接断开和界面刷新问题

**推荐操作**：
- 快速查看：使用"预览"功能在程序内查看图片
- 保存使用：使用"导出"功能保存到本地后查看

## 集成架构说明

### 模块化设计
项目采用模块化设计，各功能模块可独立运行或集成使用：

```
mars_log_analyzer_modular.py (主程序)
    ├── 继承 mars_log_analyzer_pro.py
    └── 使用模块化组件
        ├── modules/
        │   ├── data_models.py      # 数据结构
        │   ├── file_operations.py  # 文件处理
        │   ├── filter_search.py    # 过滤逻辑
        │   ├── ips_tab.py          # IPS界面
        │   └── push_tab.py         # 推送界面
        └── components/
            ├── improved_lazy_text.py
            └── scrolled_text_with_lazy_load.py
```

### 集成优势
1. **统一界面** - 所有iOS开发工具在一个窗口
2. **共享环境** - 统一的虚拟环境和依赖管理
3. **灵活使用** - 既可集成使用，也可独立运行
4. **易于维护** - 模块分离，便于单独更新

### 扩展开发
如需添加新功能模块：
1. 在独立目录创建模块（如`new_tool/`）
2. 在主程序中添加新标签页
3. 使用延迟导入避免启动依赖
4. 更新requirements.txt添加新依赖