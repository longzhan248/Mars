# CLAUDE.md - UI组件模块

## 模块概述
iOS代码混淆工具的UI组件层，提供配置、进度、映射管理和白名单编辑等界面。基于tkinter构建，采用委托模式设计。

## 核心组件

### 1. config_panel.py (497行) - 配置面板
混淆参数配置界面。

#### 主要功能
- **快速模板**: minimal/standard/aggressive三种预设
- **项目路径**: 输入/输出路径选择
- **混淆选项**: 类名/方法名/属性名/协议名开关
- **资源处理**: 图片/音频/字体修改选项
- **高级配置**: 垃圾代码、字符串加密、并行处理

#### ConfigPanel类
```python
class ConfigPanel(ttk.Frame):
    def __init__(self, parent, tab):
        """
        Args:
            parent: 父容器
            tab: ObfuscationTab实例（用于访问配置变量）
        """

    def create_widgets(self):
        """创建UI组件"""
        - 模板选择器（ttk.Combobox）
        - 路径输入框（Entry + Button）
        - 配置复选框（Checkbutton）
        - 数值调节器（Scale/Spinbox）

    def load_template(self, template_name):
        """加载预设模板"""
```

**配置变量**（存储在tab实例中）:
- `obfuscate_classes`, `obfuscate_methods`, `obfuscate_properties`, `obfuscate_protocols`
- `modify_resources`, `modify_images`, `modify_audio`
- `insert_garbage_code`, `string_encryption`
- `enable_parse_cache`, `parallel_processing`

---

### 2. whitelist_panel.py (37行) - 白名单面板
统一的白名单管理入口，采用委托模式。

#### WhitelistManager类
```python
class WhitelistManager:
    def __init__(self, parent, tab_main):
        self.symbol_manager = SymbolWhitelistManager(...)
        self.string_manager = StringWhitelistManager(...)

    def manage_symbol_whitelist(self):
        """打开符号白名单编辑器"""
        self.symbol_manager.manage_symbol_whitelist()

    def manage_string_whitelist(self):
        """打开字符串白名单编辑器"""
        self.string_manager.manage_string_whitelist()
```

**设计模式**: Facade Pattern（外观模式）
- 简化接口，隐藏复杂的子系统
- 统一管理两种白名单类型
- 委托给专门的管理器处理细节

---

### 3. symbol_whitelist_manager.py (287行) - 符号白名单UI
管理类名、方法名、属性名白名单。

#### SymbolWhitelistManager类
```python
class SymbolWhitelistManager:
    def manage_symbol_whitelist(self):
        """打开符号白名单编辑窗口"""
        - 系统API白名单展示（只读）
        - 自定义白名单编辑
        - 导入/导出JSON功能
        - 通配符支持（*和?）

    def add_symbol(self):
        """添加符号到白名单"""

    def remove_symbol(self):
        """移除选中符号"""

    def load_custom_whitelist(self):
        """加载自定义白名单JSON"""

    def save_custom_whitelist(self):
        """保存自定义白名单JSON"""
```

**白名单格式**:
```json
{
    "classes": ["NSObject", "Custom*"],
    "methods": ["init", "dealloc", "viewDid*"],
    "properties": ["delegate", "dataSource"]
}
```

---

### 4. string_whitelist_manager.py (288行) - 字符串白名单UI
管理加密字符串白名单。

#### StringWhitelistManager类
```python
class StringWhitelistManager:
    def manage_string_whitelist(self):
        """打开字符串白名单编辑窗口"""
        - 常见系统字符串展示
        - 自定义字符串编辑
        - 正则表达式支持
        - JSON导入导出

    def add_string(self):
        """添加字符串到白名单"""

    def remove_string(self):
        """移除字符串"""
```

**用途**: 防止加密关键字符串导致运行时错误
- Bundle Identifier
- URL Scheme
- 系统通知名称
- Keychain标识符

---

### 5. progress_panel.py (122行) - 进度显示面板
实时显示混淆进度和日志。

#### ProgressPanel类
```python
class ProgressPanel(ttk.Frame):
    def __init__(self, parent):
        # 进度条（ttk.Progressbar）
        # 状态标签（ttk.Label）
        # 日志文本框（scrolledtext.ScrolledText）

    def update_progress(self, percent, message):
        """更新进度"""

    def append_log(self, message, level='INFO'):
        """追加日志"""
        # 支持颜色标记（ERROR/WARNING/INFO）

    def clear_logs(self):
        """清空日志"""
```

**日志级别**:
- `INFO`: 黑色文本
- `WARNING`: 橙色文本
- `ERROR`: 红色文本

---

### 6. mapping_panel.py (308行) - 映射管理面板
查看和管理符号映射表。

#### MappingPanel类
```python
class MappingPanel(ttk.Frame):
    def create_widgets(self):
        # 映射表树形视图（ttk.Treeview）
        # 搜索框（ttk.Entry）
        # 导出按钮（ttk.Button）

    def load_mapping(self, mapping_dict):
        """加载映射数据到表格"""

    def search_mapping(self, keyword):
        """搜索映射表"""

    def export_mapping(self):
        """导出映射表为JSON"""
```

**映射表格式**:
```json
{
    "classes": {
        "UserManager": "A1B2C3",
        "NetworkService": "D4E5F6"
    },
    "methods": {
        "getUserInfo": "m1n2o3",
        "postRequest": "p4q5r6"
    }
}
```

---

### 7. help_dialog.py (309行) - 帮助对话框
参数说明和使用指南。

#### HelpDialog类
```python
class HelpDialog(tk.Toplevel):
    def show_help(self, topic):
        """显示指定主题的帮助"""
        - 混淆选项说明
        - 资源处理说明
        - 高级选项说明
        - 性能优化建议
```

**帮助主题**:
- **obfuscation**: 混淆选项详解
- **resources**: 资源处理说明
- **advanced**: 高级功能指南
- **performance**: 性能优化建议

---

## UI布局结构

```
ObfuscationTab (主标签页)
├── ConfigPanel (配置面板)
│   ├── 模板选择
│   ├── 路径配置
│   ├── 混淆选项
│   ├── 资源处理
│   └── 高级配置
├── ProgressPanel (进度面板)
│   ├── 进度条
│   ├── 状态标签
│   └── 日志文本框
├── MappingPanel (映射面板)
│   ├── 映射表格
│   ├── 搜索框
│   └── 导出按钮
└── WhitelistManager (白名单管理)
    ├── SymbolWhitelistManager
    └── StringWhitelistManager
```

## 组件交互流程

### 1. 配置流程
```
用户选择模板 → ConfigPanel.load_template()
            → 更新tab中的配置变量
            → UI控件同步更新
```

### 2. 混淆流程
```
用户点击"开始混淆" → tab_main.start_obfuscation()
                  → ProgressPanel.update_progress()
                  → 完成后 MappingPanel.load_mapping()
```

### 3. 白名单编辑
```
用户点击"管理白名单" → WhitelistManager.manage_xxx_whitelist()
                    → 专门的Manager打开编辑窗口
                    → 保存到custom_whitelist.json
```

## 开发指南

### 添加新配置项
```python
# 1. 在tab_main.py添加变量
self.new_option_var = tk.BooleanVar(value=False)

# 2. 在ConfigPanel.create_widgets()添加UI
ttk.Checkbutton(
    frame,
    text="新选项",
    variable=self.tab.new_option_var
).grid(...)

# 3. 在模板中添加默认值
'minimal': {'new_option': False}
```

### 自定义进度回调
```python
def custom_callback(progress, message):
    progress_panel.update_progress(progress, message)
    progress_panel.append_log(f"[{progress}%] {message}")

obfuscator.run(callback=custom_callback)
```

### 扩展白名单类型
```python
# 1. 创建新的Manager类
class NewWhitelistManager:
    def manage_new_whitelist(self):
        # 实现编辑界面
        pass

# 2. 在WhitelistManager中集成
self.new_manager = NewWhitelistManager(...)
```

## 最佳实践

### UI响应性
- 耗时操作使用多线程（避免阻塞主线程）
- 使用`root.after()`更新UI（线程安全）
- 提供取消功能（用户可中断操作）

### 数据验证
- 路径输入验证（检查目录是否存在）
- 配置参数范围检查（防止无效值）
- 白名单格式验证（JSON schema）

### 错误处理
```python
try:
    # 执行操作
    result = do_something()
except Exception as e:
    # 显示友好的错误消息
    messagebox.showerror("错误", f"操作失败: {str(e)}")
    # 记录到日志
    progress_panel.append_log(f"ERROR: {str(e)}", level='ERROR')
```

## 版本历史

**v2.4.0** (2025-10-23) - 代码质量优化
- ✅ whitelist_panel重构: 755行→37行（委托模式）
- ✅ 新增symbol_whitelist_manager.py (287行)
- ✅ 新增string_whitelist_manager.py (288行)
- ✅ 所有文件符合500行规范

**v2.3.2** (2025-10-22)
- ✅ 新增whitelist_panel.py (原755行)
- ✅ 新增help_dialog.py (309行)

**v2.3.1** (2025-10-22)
- ✅ 初始UI模块化

---

**版本**: 2.4.0 | **更新**: 2025-10-23 | **状态**: ✅ 生产就绪
