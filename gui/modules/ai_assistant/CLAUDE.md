# AI智能诊断模块

## 模块概述
AI驱动的日志分析工具，支持多AI服务(OpenAI/Claude/DeepSeek/Doubao)，提供崩溃分析、性能诊断、智能搜索等功能。

## 核心功能
- 自动化日志分析和问题定位
- 智能问答和专业诊断建议
- 可定制Prompt模板系统
- 完整的日志跳转和导航体验

## 架构 (重构后 v2.0.0)

```
gui/modules/ai_assistant/
├── panel_main.py (393行)           # 主控制器
├── ui/
│   ├── chat_panel.py (440行)          # 聊天面板
│   ├── toolbar_panel.py (235行)       # 工具栏
│   ├── navigation_helper.py (365行)   # 日志导航
│   └── prompt_panel.py (235行)        # Prompt管理
├── controllers/                        # 控制器(预留)
└── utils/                              # 工具函数(预留)
```

**重构成果**: 1955行→1798行 (5个文件,重构率92%)

## 核心组件

### 1. panel_main.py - 主控制器
**职责**: AI客户端管理、Token优化、AI提问核心逻辑
**关键方法**:
- `ask_question()`: AI提问处理
- `smart_search()`: 智能搜索
- `analyze_module_health()`: 模块健康分析
- `get_context_params()`: 上下文参数配置

### 2. chat_panel.py - 聊天面板
**职责**: 对话显示、消息输入、搜索、导出
**特性**:
- 可点击的日志链接 (timestamp/index/module)
- 消息样式化 (user/assistant/system/error)
- 实时搜索高亮
- 多格式导出 (Markdown/Text)

### 3. toolbar_panel.py - 工具栏
**职责**: 快捷按钮、导航历史、设置管理
**快捷功能**:
- 智能搜索、模块健康分析
- 异常模块分析、自定义Prompt

### 4. navigation_helper.py - 日志导航
**职责**: 日志跳转、预览、历史管理
**跳转类型**:
- `LOG_INDEX:123` - 按索引跳转
- `TIMESTAMP:2024-10-22 10:30:00` - 按时间戳
- `LINE:456` - 按行号
- `MODULE:NetworkModule` - 跳转到模块

### 5. prompt_panel.py - Prompt管理
**职责**: 自定义Prompt模板管理、执行
**支持变量**:
- `{selected_log}`, `{context_logs}`, `{module_name}`, `{timestamp}`

## 快速使用

### AI服务配置
配置文件: `~/.mars_analyzer/ai_config.json`
```json
{
    "service": "openai",
    "api_key": "sk-xxx",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
}
```

支持服务: OpenAI, Claude, DeepSeek, Doubao

### 自定义Prompt模板
存储: `~/.mars_analyzer/prompt_templates.json`
```json
{
    "id": "crash_analysis",
    "name": "崩溃分析",
    "content": "分析以下崩溃日志: {selected_log}",
    "description": "深度分析崩溃原因",
    "category": "crash"
}
```

## 数据流

### 提问流程
```
用户输入 → ChatPanel → panel_main.ask_question()
→ 获取上下文 → AI调用 → 处理响应 → 显示结果
```

### 日志跳转流程
```
点击链接 → ChatPanel → NavigationHelper.jump_to_log()
→ 定位日志 → 高亮动画 → 更新历史 → 更新按钮状态
```

## 核心功能详解

### 1. 智能搜索
- 关键词搜索 + 语义搜索
- 时间范围和模块过滤
- 入口: `panel_main.smart_search()`

### 2. 模块健康分析
- ERROR/WARNING日志统计
- 日志频率异常检测
- 崩溃相关性分析
- 入口: `panel_main.analyze_module_health()`

### 3. 上下文参数配置
三种模式（简化/标准/详细）:
- crash_before/after: 上下文行数 (10/20/40)
- search_logs: 搜索日志数 (500/1000/2000)
- search_tokens: Token限制 (4k/8k/16k)

## 开发指南

### 添加新AI服务
在 `ai_service_client.py` 中:
1. 添加服务配置
2. 实现API调用逻辑
3. 更新服务选择

### 添加快捷按钮
在 `toolbar_panel.py` 中:
```python
buttons = [
    {'text': '新功能', 'command': self.panel.new_feature}
]
```

### 自定义跳转类型
在 `navigation_helper.py` 中扩展 `_on_link_click()`

## 性能优化建议
1. **大量日志**: 分页加载、限制上下文数量
2. **UI响应性**: AI调用使用线程、延迟跳转
3. **内存管理**: 限制chat_history长度、清理jump_history

## 已知限制
- AI上下文长度受token限制
- 日志跳转仅支持当前加载的日志
- 一次只能处理一个AI请求

## 版本历史

**v2.0.0** (2025-10-22) - Phase 2 重构
- ✅ UI模块化 (1955行→5个模块,重构率92%)
- ✅ 所有功能100%兼容
- ✅ 完整的日志跳转导航体验

**相关文档**:
- API文档: `gui/modules/ai_diagnosis/CLAUDE.md`
- 重构记录: `docs/technical/REFACTORING_LARGE_FILES.md`
- Phase 2总结: `docs/technical/PHASE2_COMPLETION_SUMMARY.md`

---

**版本**: 2.0.0 | **更新**: 2025-10-22 | **状态**: ✅ Phase 2 完成
