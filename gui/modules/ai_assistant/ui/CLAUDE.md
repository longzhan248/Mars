# AI助手UI组件

## 组件概述
AI助手模块的UI层实现，包含4个独立组件，负责聊天显示、工具栏、日志导航和Prompt管理。

## 组件列表

### 1. chat_panel.py (440行)
**职责**: 聊天对话显示和用户输入

**核心类**: `ChatPanel(ttk.Frame)`

**主要功能**:
- 对话历史显示（支持样式化）
- 消息输入框和发送
- 实时搜索和高亮
- 对话导出（Markdown/Text）

**关键方法**:
```python
def append_chat(role, message)          # 添加消息
def _insert_message_with_links(text)    # 插入带链接的消息
def search_chat()                       # 搜索对话
def export_chat()                       # 导出对话
def clear_chat()                        # 清空对话
```

**特殊功能**:
- 可点击链接: `LOG_INDEX:123`, `TIMESTAMP:xxx`, `MODULE:xxx`
- 消息样式: user(蓝色), assistant(绿色), system(灰色), error(红色)

---

### 2. toolbar_panel.py (235行)
**职责**: 工具栏按钮和导航控制

**核心类**: `ToolbarPanel(ttk.Frame)`

**主要功能**:
- 标题和导航按钮（后退/前进）
- 功能按钮（设置/清空/导出/Prompt）
- 快捷操作按钮（动态加载自定义Prompt）

**关键方法**:
```python
def update_navigation_buttons(back, forward)  # 更新导航状态
def confirm_clear_chat()                      # 确认清空对话
def show_settings()                           # 显示设置对话框
def show_custom_prompts()                     # Prompt管理
def _load_shortcut_buttons()                  # 加载快捷按钮
```

**导入修复记录**:
- 设置对话框: `AISettingsDialog` (来自 `gui.modules.ai_diagnosis_settings`)

---

### 3. navigation_helper.py (365行)
**职责**: 日志跳转和导航历史管理

**核心类**: `NavigationHelper`

**主要功能**:
- 日志跳转（按索引/时间戳/行号/模块）
- 日志预览窗口
- 跳转历史（后退/前进）
- 高亮动画效果

**关键方法**:
```python
def _jump_to_log(log_index)                # 跳转到日志
def _jump_to_log_by_timestamp(timestamp)   # 按时间戳跳转
def _jump_to_log_by_line_number(line)      # 按行号跳转
def _jump_to_module(module_name)           # 跳转到模块
def _show_log_preview(event, value, type)  # 显示预览
def _hide_log_preview()                    # 隐藏预览
def jump_back()                            # 后退
def jump_forward()                         # 前进
```

**跳转链接格式**:
- `LOG_INDEX:123` - 索引跳转
- `TIMESTAMP:2024-10-22 10:30:00` - 时间戳跳转
- `LINE:456` - 行号跳转
- `MODULE:NetworkModule` - 模块跳转

**数据结构**:
```python
jump_history: List[int]        # 跳转历史记录
jump_history_index: int        # 当前历史位置
preview_window: tk.Toplevel    # 预览窗口实例
```

---

### 4. prompt_panel.py (235行)
**职责**: 自定义Prompt模板管理

**核心类**: `PromptPanel`

**主要功能**:
- Prompt选择器对话框
- Prompt执行和变量替换
- Prompt管理窗口（CRUD操作）

**关键方法**:
```python
def show_selector()                         # 显示Prompt选择器
def use_prompt(prompt_id, context_log)      # 使用Prompt
def _execute_prompt(name, formatted_prompt) # 执行Prompt
def show_management_window()                # Prompt管理窗口
```

**支持的变量替换**:
- `{selected_log}` - 当前选中的日志
- `{context_logs}` - 上下文日志
- `{module_name}` - 模块名称
- `{timestamp}` - 时间戳

**数据存储**: `~/.mars_analyzer/prompt_templates.json`

---

## 组件依赖关系

```
panel_main (主控制器)
├── navigation_helper (辅助类，无UI)
├── prompt_panel (辅助类，无UI)
├── chat_panel (UI组件) ← 依赖 navigation_helper
└── toolbar_panel (UI组件) ← 依赖 navigation_helper, chat_panel
```

**创建顺序**（重要）:
1. `navigation_helper` - 无UI依赖
2. `prompt_panel` - 无UI依赖
3. `chat_panel` - 需要 navigation
4. `toolbar_panel` - 需要 chat_panel 和 navigation

---

## 数据流示例

### 消息发送流程
```
用户输入 → chat_panel.question_var
→ panel_main.ask_question()
→ AI处理
→ chat_panel.append_chat("assistant", response)
```

### 日志跳转流程
```
用户点击链接 → chat_panel._on_link_click(value, type)
→ navigation_helper._jump_to_log(index)
→ main_app.tree.see(item)
→ navigation_helper._animate_highlight()
→ toolbar_panel.update_navigation_buttons()
```

### Prompt执行流程
```
用户选择Prompt → prompt_panel.show_selector()
→ 用户确认 → prompt_panel.use_prompt(id)
→ 变量替换 → panel_main.ask_question(filled_content)
```

---

## 开发注意事项

### 组件创建顺序问题
**错误**:
```python
self.toolbar = ToolbarPanel(self.frame, self)  # ❌ chat_panel还未创建
self.chat_panel = ChatPanel(self.frame, self)
```

**正确**:
```python
# 先创建辅助组件
self.navigation = NavigationHelper(self)
self.prompt_panel = PromptPanel(self)

# 再创建UI组件
self.chat_panel = ChatPanel(self.frame, self)
self.toolbar = ToolbarPanel(self.frame, self)
self.toolbar.pack(before=self.chat_panel)  # 确保正确的布局顺序
```

### 常见引用路径
- 访问问题输入框: `self.chat_panel.question_var`
- 访问导航功能: `self.navigation.jump_back()`
- 访问Prompt功能: `self.prompt_panel.use_prompt()`

### 导入修复记录
1. **设置对话框** (toolbar_panel.py:225-242):
   - 原错误: `from ..ai_diagnosis.settings_dialog import show_settings_dialog`
   - 修复为: `from ai_diagnosis_settings import AISettingsDialog`

2. **Prompt方法命名** (panel_main.py:215-217):
   - 委托方法: `use_custom_prompt()` → `prompt_panel.use_prompt()`

---

## 版本历史

**v2.0.0** (2025-10-22) - Phase 2 重构
- ✅ 从1955行单文件拆分为5个模块
- ✅ 重构率92%
- ✅ 修复组件创建顺序问题
- ✅ 修复导入路径问题
- ✅ 添加缺失的委托方法

---

**更新**: 2025-10-22 | **状态**: ✅ 稳定
