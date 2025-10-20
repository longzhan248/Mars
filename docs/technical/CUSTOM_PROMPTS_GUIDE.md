# 自定义Prompt功能使用指南

**版本**: v1.0.0
**创建日期**: 2025-10-20
**更新日期**: 2025-10-20

---

## 功能概述

自定义Prompt功能允许用户创建和管理自己的AI提示词模板，实现针对特定场景的日志分析。例如：
- **语音问题分析**：专门针对音频录制、播放、编解码问题
- **网络问题诊断**：专门针对HTTP请求、连接、超时问题
- **UI卡顿分析**：专门针对渲染性能、布局问题
- **自定义业务场景**：根据项目特点自定义分析规则

### 核心特性

✅ **灵活的模板系统**
- 支持变量替换 `{variable_name}`
- 自动提取模板变量
- 支持Markdown格式

✅ **完整的CRUD操作**
- 创建、编辑、删除、复制模板
- 启用/禁用控制
- 分类管理

✅ **持久化存储**
- JSON格式存储
- 支持导入/导出
- 自动保存

✅ **GUI友好**
- 直观的管理界面
- 实时变量预览
- 模板搜索过滤

---

## 快速开始

### 1. 打开自定义Prompt管理器

1. 启动主程序：`./scripts/run_analyzer.sh`
2. 在AI助手面板的标题栏，点击 **📝** 按钮
3. 弹出"自定义Prompt模板管理"对话框

### 2. 使用内置模板

首次运行会自动创建2个示例模板：
- **语音问题专项分析**：分析音频相关问题
- **网络问题专项分析**：分析网络请求问题

直接在列表中双击模板即可查看和编辑。

### 3. 创建新模板

点击"➕ 新建"按钮，填写以下信息：

#### 基本信息
- **名称***：模板显示名称（如"UI卡顿分析"）
- **分类***：选择分类（崩溃分析、性能诊断、自定义分析等）
- **描述**：简要说明模板用途
- **启用状态**：勾选后模板可用

#### 模板内容

在编辑器中输入Prompt模板，支持变量语法：

```markdown
你是{专业领域}专家...

## 任务
分析以下{问题类型}问题：

**相关日志**:
```
{logs}
```

## 分析要求
1. ...
2. ...
```

**变量示例**：
- `{timestamp}` - 时间戳
- `{module_name}` - 模块名
- `{logs}` - 日志内容
- `{issue_type}` - 问题类型
- `{url}` - URL地址

底部会实时显示检测到的变量。

### 4. 使用自定义模板

1. 加载日志文件到主程序
2. 在AI助手面板，点击 **📝** 按钮
3. 选择要使用的模板，双击或点击"使用"
4. 填写变量值（如果模板有变量）
5. 点击"开始分析"

AI将使用你的自定义Prompt进行分析！

---

## 详细功能说明

### 模板管理

#### 列表操作

**过滤和搜索**：
- **分类过滤**：下拉选择分类，仅显示该分类的模板
- **关键词搜索**：输入关键词实时过滤（搜索名称和描述）
- **一键清除**：点击搜索框的"×"按钮

**树形列表**：
- 显示列：名称、分类、状态（✓启用 / ✗禁用）
- 排序：按创建时间倒序（新的在前）
- 双击：查看/编辑模板

**右键菜单**：
- 编辑：修改模板
- 复制：创建副本
- 启用/禁用：切换状态
- 删除：删除模板（不可恢复）

#### 编辑模板

**基本信息**：
- ID：自动生成，不可修改
- 名称、分类、描述、启用状态：可修改

**模板内容**：
- 多行文本编辑器
- 支持Markdown语法
- 实时变量检测

**操作按钮**：
- **💾 保存**：保存修改
- **🔄 重置**：恢复到选中状态

### 变量系统

#### 变量语法

使用 `{variable_name}` 格式定义变量：

```markdown
**时间**: {timestamp}
**模块**: {module_name}
**日志**:
{logs}
```

#### 常用变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `timestamp` | 时间戳 | 2025-10-20 10:00:00 |
| `module_name` | 模块名 | VoiceRecorder |
| `issue_type` | 问题类型 | 录音失败 |
| `logs` | 日志内容 | 多行日志摘要 |
| `url` | URL地址 | https://api.example.com |
| `error_msg` | 错误信息 | Connection timeout |

#### 自动填充

某些变量会自动填充：
- `logs`：如果用户未填写，自动生成当前日志摘要（最多5000字符）

### 导入/导出

#### 导出模板

1. 点击底部"📤 导出"按钮
2. 选择要导出的模板（选中状态），或留空导出全部
3. 选择保存位置
4. 保存为JSON文件

**导出格式**：
```json
{
  "custom_prompts": [
    {
      "id": "voice_issue_analysis",
      "name": "语音问题专项分析",
      "category": "自定义分析",
      "description": "...",
      "template": "...",
      "enabled": true,
      "created_at": "2025-10-20T10:00:00",
      "modified_at": "2025-10-20T10:00:00",
      "variables": ["timestamp", "module_name", "logs"]
    }
  ]
}
```

#### 导入模板

1. 点击底部"📥 导入"按钮
2. 选择JSON文件
3. 自动导入模板到列表

**ID冲突处理**：
如果导入的模板ID已存在，会自动重命名为 `{id}_1`, `{id}_2` ...

---

## 高级使用

### 场景化模板示例

#### 1. 语音问题专项分析

```markdown
你是拥有10年以上经验的音频和语音处理专家...

## 语音问题信息
**时间**: {timestamp}
**模块**: {module_name}
**问题类型**: {issue_type}

**相关日志**:
```
{logs}
```

## 专项分析要求
### 1. 问题识别
- 录音问题？（权限、硬件、采样率）
- 播放问题？（解码、缓冲、音频焦点）
- 编解码问题？（格式、参数）
- 音质问题？（噪音、回声、音量）

### 2. 技术分析
- 音频参数：采样率、位深度、声道数
- 编解码器：使用的codec及配置
- 硬件状态：麦克风、扬声器状态

### 3. 解决方案
- 临时方案：快速缓解问题
- 根治方案：彻底解决问题
- 代码示例：具体实现
```

**变量**：`timestamp`, `module_name`, `issue_type`, `logs`

#### 2. 网络问题专项分析

```markdown
你是网络通信专家，精通HTTP/HTTPS、TCP/IP...

## 网络问题信息
**时间**: {timestamp}
**请求URL**: {url}

**相关日志**:
```
{logs}
```

## 分析要求
### 1. 问题类型识别
- 连接失败？（DNS、握手、超时）
- 请求失败？（状态码、超时、中断）
- 响应异常？（格式错误、不完整）

### 2. 网络层分析
- DNS解析、TCP连接、TLS握手
- HTTP请求/响应详情

### 3. 优化建议
- 超时配置优化
- 重试策略调整
- 缓存策略改进
```

**变量**：`timestamp`, `module_name`, `url`, `logs`

### 最佳实践

#### ✅ DO

1. **清晰的角色定位**
   ```markdown
   你是{专业领域}专家，精通...
   ```

2. **结构化分析要求**
   使用Markdown标题和列表组织分析步骤

3. **引用日志格式**
   ```markdown
   在分析中引用日志时，使用可点击格式：
   - 时间戳：[2025-10-20 10:00:00]
   - 行号：#123
   - 模块：@ModuleName
   ```

4. **可操作的建议**
   提供具体的修复方案和代码示例

5. **合理的变量数量**
   3-5个变量最佳，不要超过10个

#### ❌ DON'T

1. **❌ 避免过度通用**
   ```markdown
   分析这个问题... (太模糊)
   ```

2. **❌ 避免变量名冲突**
   不要使用Python关键字作为变量名（如 `class`, `for`, `if`）

3. **❌ 避免过长的模板**
   控制在2000字符以内，过长会影响AI响应

4. **❌ 避免硬编码信息**
   使用变量代替固定值，提高复用性

---

## 存储格式

### 配置文件位置

```
项目根目录/gui/custom_prompts.json
```

### 文件结构

```json
{
  "custom_prompts": [
    {
      "id": "unique_id",
      "name": "模板名称",
      "category": "分类",
      "description": "描述",
      "template": "Prompt模板内容",
      "enabled": true,
      "created_at": "2025-10-20T10:00:00",
      "modified_at": "2025-10-20T10:00:00",
      "variables": ["var1", "var2"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 唯一标识符 |
| `name` | string | ✓ | 模板名称 |
| `category` | string | ✓ | 分类 |
| `description` | string | | 描述信息 |
| `template` | string | ✓ | Prompt模板内容 |
| `enabled` | boolean | | 是否启用（默认true） |
| `created_at` | string | | 创建时间（ISO格式） |
| `modified_at` | string | | 修改时间（ISO格式） |
| `variables` | array | | 变量列表（自动提取） |

---

## 故障排查

### 问题：模板列表为空

**症状**：打开管理器后列表显示为空

**解决方案**：
1. 检查配置文件：`gui/custom_prompts.json`
2. 如果文件不存在或损坏，删除后重启程序（会自动创建示例模板）
3. 检查文件权限，确保可读写

### 问题：变量未识别

**症状**：使用模板时提示变量未找到

**解决方案**：
1. 确认变量格式正确：`{variable_name}`
2. 检查是否有拼写错误
3. 查看模板详情中的"检测到的变量"列表

### 问题：导入失败

**症状**：导入JSON文件时报错

**解决方案**：
1. 检查JSON格式是否正确（使用JSON验证器）
2. 确认文件编码为UTF-8
3. 查看错误信息中的具体原因

### 问题：模板不生效

**症状**：使用模板后AI响应不符合预期

**解决方案**：
1. 检查模板是否启用
2. 确认变量值已正确填写
3. 查看AI助手对话历史中的实际Prompt
4. 调整模板的指令清晰度

---

## API参考

### Python代码调用

```python
# 导入管理器
from gui.modules.ai_diagnosis.custom_prompt_manager import (
    CustomPromptManager,
    CustomPrompt,
    get_custom_prompt_manager
)

# 获取单例管理器
manager = get_custom_prompt_manager()

# 列出所有模板
all_prompts = manager.list_all()
enabled_prompts = manager.list_all(enabled_only=True)
category_prompts = manager.list_all(category="自定义分析")

# 获取单个模板
prompt = manager.get("voice_issue_analysis")

# 创建新模板
new_prompt = CustomPrompt(
    id="custom_ui_lag",
    name="UI卡顿分析",
    category="性能诊断",
    description="分析UI渲染和布局性能问题",
    template="你是UI性能专家...\n\n{logs}",
    enabled=True
)
manager.add(new_prompt)

# 更新模板
manager.update("custom_ui_lag", description="更新后的描述")

# 删除模板
manager.delete("custom_ui_lag")

# 格式化模板
prompt = manager.get("voice_issue_analysis")
formatted = prompt.format(
    timestamp="2025-10-20 10:00:00",
    module_name="VoiceRecorder",
    issue_type="录音失败",
    logs="[ERROR] 麦克风权限被拒绝"
)
```

---

## 附录

### 支持的分类

- 崩溃分析
- 性能诊断
- 问题总结
- 交互问答
- 自定义分析

### Markdown支持

模板内容支持完整的Markdown语法：
- 标题（`#`, `##`, `###`）
- 列表（`-`, `1.`）
- 代码块（\`\`\`）
- 粗体/斜体（`**bold**`, `*italic*`）
- 链接（`[text](url)`）

### 变量命名规范

推荐使用 snake_case 风格：
- ✅ `module_name`
- ✅ `error_msg`
- ✅ `issue_type`
- ❌ `moduleName`（CamelCase不推荐）
- ❌ `error-msg`（kebab-case不支持）

---

**最后更新**: 2025-10-20
**维护者**: Mars Log Analyzer Team
