# AI诊断助手改进计划

**文档版本**: v1.0
**创建日期**: 2025-10-17
**状态**: 待实施

---

## 📋 审核总结

经过全面审核，AI诊断助手已经很好地集成到Mars日志分析系统中，实现了崩溃分析、性能诊断、问题总结等核心功能。但在Mars日志特性的深度利用、多文件场景支持、分析结果可视化等方面还有提升空间。

### 当前评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 功能完整性 | ⭐⭐⭐⭐⭐ | 核心功能齐全，支持4种AI服务 |
| Mars特性支持 | ⭐⭐⭐☆☆ | 基础支持，但未深度利用模块分组等特性 |
| 多文件场景 | ⭐⭐☆☆☆ | 仅支持单文件分析，缺少对比功能 |
| 结果可视化 | ⭐⭐⭐☆☆ | 文本展示为主，缺少跳转和高亮 |
| 用户体验 | ⭐⭐⭐⭐⭐ | 侧边栏集成、快捷操作、右键菜单完善 |
| **综合评分** | **⭐⭐⭐⭐☆** | **优秀，有改进空间** |

---

## 🎯 改进目标

### 目标1: 深度利用Mars日志特性

**当前问题**：
- LogPreprocessor未利用Mars模块分组（`<Chair>`, `[Plugin]`等）
- 未使用自定义模块规则功能
- 模块级别分析不够精准

**改进方案**：

#### 1.1 增强LogPreprocessor的Mars感知

```python
# 文件: gui/modules/ai_diagnosis/log_preprocessor.py
# 新增方法

class LogPreprocessor:

    def extract_module_specific_logs(self, entries: List[LogEntry],
                                     module: str) -> List[LogEntry]:
        """
        提取特定模块的日志（支持Mars模块分组）

        Args:
            entries: 日志条目列表
            module: 模块名称

        Returns:
            指定模块的日志列表
        """
        return [e for e in entries if e.module == module]

    def get_module_health(self, entries: List[LogEntry]) -> Dict[str, Dict]:
        """
        分析各模块健康状况（Mars特有）

        Returns:
            模块健康统计字典:
            {
                'ModuleName': {
                    'total': 100,
                    'errors': 5,
                    'warnings': 10,
                    'crashes': 0,
                    'health_score': 0.85
                }
            }
        """
        module_stats = {}

        # 获取所有模块
        modules = set(e.module for e in entries)

        for module in modules:
            module_logs = self.extract_module_specific_logs(entries, module)

            error_count = sum(1 for e in module_logs if e.level == 'ERROR')
            warning_count = sum(1 for e in module_logs if e.level == 'WARNING')
            crash_count = sum(1 for e in module_logs if e.is_crash)

            # 计算健康分数 (0-1)
            total = len(module_logs)
            if total == 0:
                health_score = 1.0
            else:
                # 崩溃权重最高，错误次之，警告最低
                penalty = (crash_count * 10 + error_count * 5 + warning_count * 1) / total
                health_score = max(0, 1 - penalty / 10)

            module_stats[module] = {
                'total': total,
                'errors': error_count,
                'warnings': warning_count,
                'crashes': crash_count,
                'health_score': round(health_score, 2)
            }

        return module_stats

    def get_unhealthy_modules(self, entries: List[LogEntry],
                             threshold: float = 0.7) -> List[str]:
        """
        获取不健康的模块列表

        Args:
            entries: 日志条目列表
            threshold: 健康分数阈值，低于此值视为不健康

        Returns:
            不健康模块名称列表，按健康分数升序排列
        """
        health_stats = self.get_module_health(entries)

        unhealthy = [
            (module, stats['health_score'])
            for module, stats in health_stats.items()
            if stats['health_score'] < threshold
        ]

        # 按健康分数升序排序（最不健康的在前）
        unhealthy.sort(key=lambda x: x[1])

        return [module for module, score in unhealthy]
```

#### 1.2 在AI助手面板中添加模块分析按钮

```python
# 文件: gui/modules/ai_assistant_panel.py
# 在create_widgets()的快捷操作区域添加

# 第五行 - 模块健康分析
("🏥 模块健康", self.analyze_module_health),
("🔬 问题模块", self.analyze_unhealthy_modules),
```

#### 1.3 实现模块健康分析方法

```python
# 文件: gui/modules/ai_assistant_panel.py
# 新增方法

def analyze_module_health(self):
    """分析各模块健康状况"""
    if not self.main_app.log_entries:
        messagebox.showwarning("警告", "请先加载日志文件")
        return

    if self.is_processing:
        messagebox.showinfo("提示", "AI正在处理中，请稍候")
        return

    self.is_processing = True
    self.stop_flag = False
    self.set_status("正在分析模块健康...")
    self.append_chat("user", "分析模块健康状况")
    self.main_app.root.after(0, self.show_stop_button)
    self.main_app.root.after(0, self.show_progress)

    def _analyze():
        try:
            if self.stop_flag:
                return
            _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

            preprocessor = LogPreprocessor()

            # 获取模块健康统计
            module_health = preprocessor.get_module_health(self.main_app.log_entries)

            # 格式化健康报告
            health_report = []
            for module, stats in sorted(module_health.items(),
                                       key=lambda x: x[1]['health_score']):
                health_icon = '🟢' if stats['health_score'] >= 0.8 else \
                             '🟡' if stats['health_score'] >= 0.6 else '🔴'
                health_report.append(
                    f"{health_icon} {module}: "
                    f"健康度{stats['health_score']:.0%} "
                    f"(崩溃{stats['crashes']}, 错误{stats['errors']}, 警告{stats['warnings']})"
                )

            # 构建提示词
            prompt = f"""
请分析以下Mars日志系统中各模块的健康状况：

## 模块健康报告
{chr(10).join(health_report)}

## 总体统计
- 总日志数: {len(self.main_app.log_entries)}
- 模块数量: {len(module_health)}

请提供：
1. 最需要关注的问题模块（健康度<60%）
2. 各问题模块的主要问题类型
3. 改进建议和优先级排序
4. 是否存在模块间的关联问题
"""

            # 调用AI
            if not self.ai_client:
                self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                return

            response = self.ai_client.ask(prompt)

            # 显示结果
            self.main_app.root.after(0, self.append_chat, "assistant", response)

        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.main_app.root.after(0, self.append_chat, "system", error_msg)

        finally:
            self.is_processing = False
            self.main_app.root.after(0, self.hide_stop_button)
            self.main_app.root.after(0, self.hide_progress)
            self.main_app.root.after(0, self.set_status, "就绪")

    threading.Thread(target=_analyze, daemon=True).start()

def analyze_unhealthy_modules(self):
    """深度分析不健康的模块"""
    if not self.main_app.log_entries:
        messagebox.showwarning("警告", "请先加载日志文件")
        return

    if self.is_processing:
        messagebox.showinfo("提示", "AI正在处理中，请稍候")
        return

    self.is_processing = True
    self.stop_flag = False
    self.set_status("正在深度分析问题模块...")
    self.append_chat("user", "深度分析问题模块")
    self.main_app.root.after(0, self.show_stop_button)
    self.main_app.root.after(0, self.show_progress)

    def _analyze():
        try:
            if self.stop_flag:
                return
            _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

            preprocessor = LogPreprocessor()

            # 获取不健康模块
            unhealthy_modules = preprocessor.get_unhealthy_modules(
                self.main_app.log_entries,
                threshold=0.7
            )

            if not unhealthy_modules:
                self.main_app.root.after(0, self.append_chat, "system",
                    "所有模块健康状况良好！✅")
                return

            # 对每个问题模块提取详细日志
            module_details = []
            for module in unhealthy_modules[:3]:  # 只分析最严重的3个
                module_logs = preprocessor.extract_module_specific_logs(
                    self.main_app.log_entries,
                    module
                )

                # 提取该模块的错误和崩溃
                errors = [e for e in module_logs if e.level == 'ERROR'][:10]
                crashes = [e for e in module_logs if e.is_crash]

                module_details.append({
                    'name': module,
                    'errors': preprocessor.summarize_logs(errors, max_tokens=1000),
                    'crashes': preprocessor.summarize_logs(crashes, max_tokens=500) if crashes else "无崩溃",
                    'total': len(module_logs)
                })

            # 构建提示词
            prompt = f"""
发现{len(unhealthy_modules)}个问题模块，以下是最严重的{len(module_details)}个模块的详细分析：

"""
            for detail in module_details:
                prompt += f"""
## 模块: {detail['name']} (共{detail['total']}条日志)

### 错误日志
{detail['errors']}

### 崩溃日志
{detail['crashes']}

---
"""

            prompt += """
请对每个问题模块提供：
1. 核心问题诊断（是什么问题？为什么发生？）
2. 影响范围评估（严重程度、影响用户数）
3. 修复建议（具体代码层面的建议）
4. 临时缓解方案（如果无法立即修复）
"""

            # 调用AI
            if not self.ai_client:
                self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                return

            response = self.ai_client.ask(prompt)

            # 显示结果
            self.main_app.root.after(0, self.append_chat, "assistant", response)

        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            self.main_app.root.after(0, self.append_chat, "system", error_msg)

        finally:
            self.is_processing = False
            self.main_app.root.after(0, self.hide_stop_button)
            self.main_app.root.after(0, self.hide_progress)
            self.main_app.root.after(0, self.set_status, "就绪")

    threading.Thread(target=_analyze, daemon=True).start()
```

---

### 目标2: AI分析结果可视化和跳转

**当前问题**：
- AI分析结果只在对话框中显示文本
- 无法从AI分析结果直接跳转到日志位置
- 缺少分析结果的高亮和标记

**改进方案**：

#### 2.1 实现日志引用解析和跳转

```python
# 文件: gui/modules/ai_assistant_panel.py
# 修改append_chat方法

def append_chat(self, role: str, message: str):
    """
    添加对话到历史（增强版：支持日志跳转）

    Args:
        role: 角色（"user", "assistant", "system"）
        message: 消息内容
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    self.chat_history.append({
        'role': role,
        'message': message,
        'timestamp': timestamp
    })

    # 更新UI
    self.chat_text.config(state=tk.NORMAL)

    # 添加时间戳
    self.chat_text.insert(tk.END, f"[{timestamp}] ", "timestamp")

    # 添加角色标签
    role_labels = {
        "user": "用户",
        "assistant": "AI助手",
        "system": "系统"
    }
    label = role_labels.get(role, role)
    self.chat_text.insert(tk.END, f"{label}: ", role)

    # 解析消息中的日志引用并创建可点击链接
    if role == "assistant":
        self._insert_message_with_links(message)
    else:
        # 普通消息
        self.chat_text.insert(tk.END, f"{message}\n\n", "content")

    self.chat_text.config(state=tk.DISABLED)
    self.chat_text.see(tk.END)  # 滚动到底部

def _insert_message_with_links(self, message: str):
    """
    插入带日志跳转链接的消息

    解析格式：[时间戳] 或 日志#索引
    """
    import re

    # 匹配时间戳格式: [2025-09-21 13:09:49]
    timestamp_pattern = r'\[([\d\-: +\.]+)\]'

    parts = []
    last_end = 0

    for match in re.finditer(timestamp_pattern, message):
        # 添加匹配前的文本
        if match.start() > last_end:
            parts.append(('text', message[last_end:match.start()]))

        # 添加时间戳链接
        timestamp = match.group(1)
        parts.append(('link', timestamp, match.group(0)))

        last_end = match.end()

    # 添加剩余文本
    if last_end < len(message):
        parts.append(('text', message[last_end:]))

    # 插入到Text组件
    for part in parts:
        if part[0] == 'text':
            self.chat_text.insert(tk.END, part[1], "content")
        elif part[0] == 'link':
            timestamp, display_text = part[1], part[2]

            # 创建唯一tag
            tag_name = f"link_{id(part)}"

            # 插入链接文本
            start_idx = self.chat_text.index(tk.END + "-1c")
            self.chat_text.insert(tk.END, display_text, ("content", "log_link", tag_name))
            end_idx = self.chat_text.index(tk.END + "-1c")

            # 绑定点击事件
            self.chat_text.tag_bind(
                tag_name,
                "<Button-1>",
                lambda e, ts=timestamp: self._jump_to_log_by_timestamp(ts)
            )

            # 设置链接样式
            self.chat_text.tag_config(tag_name,
                foreground="#0066CC",
                underline=True,
                font=("Arial", 11, "bold"))

            # 设置鼠标悬停效果
            self.chat_text.tag_bind(tag_name, "<Enter>",
                lambda e, tag=tag_name: self.chat_text.config(cursor="hand2"))
            self.chat_text.tag_bind(tag_name, "<Leave>",
                lambda e: self.chat_text.config(cursor=""))

    self.chat_text.insert(tk.END, "\n\n")

def _jump_to_log_by_timestamp(self, timestamp: str):
    """
    根据时间戳跳转到日志并高亮

    Args:
        timestamp: 日志时间戳
    """
    try:
        # 在日志列表中查找匹配的时间戳
        log_index = None
        for i, entry in enumerate(self.main_app.log_entries):
            if entry.timestamp == timestamp:
                log_index = i
                break

        if log_index is None:
            # 尝试模糊匹配（去除时区、毫秒等）
            timestamp_short = timestamp.split('.')[0].split('+')[0].strip()
            for i, entry in enumerate(self.main_app.log_entries):
                if entry.timestamp.startswith(timestamp_short):
                    log_index = i
                    break

        if log_index is not None:
            self._jump_to_log(log_index)
        else:
            self.append_chat("system", f"未找到时间戳为 {timestamp} 的日志")

    except Exception as e:
        print(f"跳转失败: {str(e)}")

def _jump_to_log(self, log_index: int):
    """
    跳转到指定日志并高亮显示

    Args:
        log_index: 日志索引
    """
    try:
        # 确保日志查看器可见
        if hasattr(self.main_app, 'notebook'):
            # 切换到日志查看标签页
            self.main_app.notebook.select(0)

        # 滚动到目标日志
        # 使用improved_lazy_text的scroll_to_line方法
        if hasattr(self.main_app.log_text, 'scroll_to_line'):
            self.main_app.log_text.scroll_to_line(log_index)
        else:
            # 后备方案：使用see方法
            self.main_app.log_text.see(f"{log_index + 1}.0")

        # 高亮显示（3秒后消失）
        if hasattr(self.main_app.log_text, 'text_widget'):
            text_widget = self.main_app.log_text.text_widget
        else:
            text_widget = self.main_app.log_text

        # 配置高亮标签
        text_widget.tag_config("ai_highlight",
            background="#FFFF00",  # 黄色背景
            foreground="#000000")

        # 添加高亮
        line_num = log_index + 1
        text_widget.tag_add("ai_highlight", f"{line_num}.0", f"{line_num}.end")

        # 3秒后移除高亮
        self.main_app.root.after(3000, lambda:
            text_widget.tag_remove("ai_highlight", "1.0", "end"))

        # 提示用户
        self.set_status(f"已跳转到第 {log_index + 1} 行日志")

    except Exception as e:
        print(f"跳转到日志失败: {str(e)}")
        self.append_chat("system", f"跳转失败: {str(e)}")
```

#### 2.2 优化AI响应格式以支持引用

```python
# 文件: gui/modules/ai_diagnosis/prompt_templates.py
# 修改提示词模板，要求AI返回时间戳引用

CRASH_ANALYSIS_PROMPT = """
你是一个专业的崩溃日志分析专家。

## 崩溃信息
- 崩溃时间: {crash_time}
- 崩溃模块: {crash_module}
- 异常类型: {crash_exception}

## 崩溃堆栈
{crash_stack}

## 崩溃前上下文
{context_before}

## 崩溃后上下文
{context_after}

## 分析要求
1. 确定崩溃的根本原因
2. 分析崩溃的触发条件
3. 提供修复建议
4. 评估影响范围

**重要**: 在分析中引用日志时，请使用完整的时间戳格式，例如: [2025-09-21 13:09:49]
这样用户可以点击时间戳直接跳转到对应日志。
"""
```

---

### 目标3: 多文件对比分析

**当前问题**：
- 只能分析单个文件
- 无法对比不同版本/时间段的日志
- 缺少趋势分析能力

**改进方案**：

#### 3.1 添加多文件对比分析功能

```python
# 文件: gui/modules/ai_assistant_panel.py
# 在快捷操作区域添加

# 第六行 - 多文件分析（仅在有多个文件时显示）
if hasattr(self.main_app, 'file_groups') and len(self.main_app.file_groups) > 1:
    ("📊 文件对比", self.compare_files),
    ("📈 趋势分析", self.analyze_trends),
```

#### 3.2 实现文件对比分析

```python
# 文件: gui/modules/ai_assistant_panel.py

def compare_files(self):
    """对比多个文件的问题"""
    if not hasattr(self.main_app, 'file_groups'):
        messagebox.showinfo("提示", "当前只有单个文件")
        return

    file_groups = self.main_app.file_groups
    if len(file_groups) < 2:
        messagebox.showinfo("提示", "至少需要2个文件才能对比")
        return

    if self.is_processing:
        messagebox.showinfo("提示", "AI正在处理中，请稍候")
        return

    self.is_processing = True
    self.stop_flag = False
    self.set_status("正在对比文件...")
    self.append_chat("user", f"对比 {len(file_groups)} 个日志文件")
    self.main_app.root.after(0, self.show_stop_button)
    self.main_app.root.after(0, self.show_progress)

    def _compare():
        try:
            if self.stop_flag:
                return
            _, _, LogPreprocessor, PromptTemplates = safe_import_ai_diagnosis()

            preprocessor = LogPreprocessor()

            # 分别分析每个文件
            file_summaries = []
            for i, group in enumerate(file_groups):
                stats = preprocessor.get_statistics(group.entries)
                summary = preprocessor.summarize_logs(group.entries[:100], max_tokens=1500)

                file_summaries.append({
                    'index': i + 1,
                    'name': group.get_display_name(),
                    'stats': stats,
                    'summary': summary
                })

            # 构建对比提示词
            prompt = f"""
请对比以下 {len(file_summaries)} 个日志文件，找出差异和趋势：

"""
            for fs in file_summaries:
                prompt += f"""
## 文件 {fs['index']}: {fs['name']}
- 总日志数: {fs['stats']['total']}
- 崩溃数: {fs['stats']['crashes']}
- 错误数: {fs['stats']['errors']}
- 警告数: {fs['stats']['warnings']}
- 时间范围: {fs['stats']['time_range']}
- 主要模块: {', '.join([f"{k}({v})" for k, v in list(fs['stats']['modules'].items())[:3]])}

### 日志摘要
{fs['summary']}

---
"""

            prompt += """
请提供：
1. 文件间的主要差异（新增/减少的问题）
2. 问题的演进趋势（变好/变坏/持平）
3. 每个文件的独有问题
4. 共性问题（所有文件都存在的）
5. 建议关注的优先级
"""

            # 调用AI
            if not self.ai_client:
                self.main_app.root.after(0, self.append_chat, "system", "AI服务初始化失败")
                return

            response = self.ai_client.ask(prompt)

            # 显示结果
            self.main_app.root.after(0, self.append_chat, "assistant", response)

        except Exception as e:
            error_msg = f"对比失败: {str(e)}"
            self.main_app.root.after(0, self.append_chat, "system", error_msg)

        finally:
            self.is_processing = False
            self.main_app.root.after(0, self.hide_stop_button)
            self.main_app.root.after(0, self.hide_progress)
            self.main_app.root.after(0, self.set_status, "就绪")

    threading.Thread(target=_compare, daemon=True).start()
```

---

## 📅 实施时间表

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|----------|--------|
| Week 1 | 增强LogPreprocessor的Mars模块感知 | 2小时 | 🔴 高 |
| Week 1 | 实现模块健康分析功能 | 3小时 | 🔴 高 |
| Week 2 | AI结果可视化和跳转功能 | 4小时 | 🔴 高 |
| Week 3 | 多文件对比分析 | 4小时 | 🟡 中 |
| Week 3 | Mars特定提示词优化 | 2小时 | 🟡 中 |
| Week 4 | AI分析历史和缓存 | 6小时 | 🟢 低 |
| Week 5 | 自定义AI分析模板 | 4小时 | 🟢 低 |

**总预计工时**: 25小时
**建议实施周期**: 5周

---

## ✅ 验收标准

### 目标1: Mars特性支持
- [ ] `get_module_health()`方法实现并测试通过
- [ ] GUI中添加"模块健康"和"问题模块"按钮
- [ ] AI分析能正确识别Mars模块分组
- [ ] 健康分数计算合理（测试3个不同日志文件）

### 目标2: 可视化和跳转
- [ ] 点击AI响应中的时间戳能跳转到日志
- [ ] 跳转后有3秒黄色高亮
- [ ] 支持模糊时间戳匹配
- [ ] 测试跨标签页跳转功能

### 目标3: 多文件对比
- [ ] 能对比2个及以上文件
- [ ] 对比结果包含差异、趋势、独有问题
- [ ] 动态显示/隐藏对比按钮
- [ ] 测试不同文件数量场景（2/3/5个文件）

---

## 📈 成功指标

- **功能完整度**: 所有改进项100%实现
- **Mars特性利用率**: 从30%提升到80%
- **多文件场景支持**: 从0到完整支持
- **用户满意度**: 分析结果可操作性提升50%+
- **性能影响**: AI分析响应时间增加<20%

---

## 🔗 相关文档

- [AI诊断功能总体完成报告](./AI_INTEGRATION_COMPLETE.md)
- [AI诊断模块技术文档](../gui/modules/ai_diagnosis/CLAUDE.md)
- [Mars日志分析器技术指南](../gui/CLAUDE.md)
- [数据模型模块文档](../gui/modules/CLAUDE.md)

---

**下一步行动**:
1. 与团队讨论改进优先级
2. 分配开发任务
3. 开始Week 1的高优先级实施

**文档维护者**: Claude Code AI Team
**最后更新**: 2025-10-17
