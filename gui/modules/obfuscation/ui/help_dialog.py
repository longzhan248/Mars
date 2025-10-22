"""
参数帮助对话框

提供混淆参数的详细说明和使用指南。

Classes:
    ParameterHelpDialog: 参数帮助对话框主类
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os


# 参数帮助内容
PARAMETER_HELP_CONTENT = """
=== iOS代码混淆参数详细说明 ===

📝 基础混淆选项

• 类名混淆 (class_names)
• 说明：将OC/Swift类名替换为随机字符串
• 适用场景：被审核拒绝(4.3/2.1)，需要改变代码指纹
• 示例：
  原始：@interface UserManager : NSObject
  混淆：@interface WHCa7f2b : NSObject
• ✅ 推荐：标准审核应对必选项

• 方法名混淆 (method_names)
• 说明：混淆方法名（包括实例方法和类方法）
• 适用场景：深度代码混淆，增加逆向难度
• 示例：
  原始：- (void)login:(NSString *)username
  混淆：- (void)m_a3c4d:(NSString *)p_f7e2b
• ⚠️ 注意：需要确保所有调用点都被正确更新

• 属性名混淆 (property_names)
• 说明：混淆@property声明的属性名
• 适用场景：保护数据模型结构
• 示例：
  原始：@property (nonatomic, strong) NSString *userName;
  混淆：@property (nonatomic, strong) NSString *p_h8d3f;

• 协议名混淆 (protocol_names)
• 说明：混淆@protocol协议名
• 适用场景：保护接口设计
• 示例：
  原始：@protocol UserManagerDelegate
  混淆：@protocol WHCp_e9f2a

🎨 高级混淆功能

• 插入垃圾代码 (insert_garbage_code)
• 说明：在项目中插入无实际功能的代码
• 工作原理：生成合法但无用的类和方法，增加代码体积
• 推荐值：5-20个类（标准）、20-50个类（激进）
• ✅ 优点：显著改变代码特征，难以识别
• ⚠️ 注意：会增加包体积，需权衡

• 字符串加密 (string_encryption)
• 说明：对字符串常量进行加密
• 工作原理：将字符串编译时加密，运行时解密
• 加密算法：XOR（推荐）、Base64、移位、ROT13
• 适用场景：保护敏感字符串（API Key、密钥等）
• ⚠️ 注意：会轻微影响性能，建议只加密关键字符串

⚡ 性能优化选项

• 并行处理 (parallel_processing)
• 说明：使用多线程/多进程加速混淆过程
• 推荐值：启用（默认）
• 性能提升：3-6倍（大型项目）
• 适用场景：超过100个源文件的项目

• 解析缓存 (enable_parse_cache)
• 说明：缓存文件解析结果，加速重复构建
• 推荐值：启用（默认）
• 性能提升：100-300倍（重复构建）
• 检测方式：自动检测文件变化（MD5）

🔤 命名规则

• 前缀 (prefix)
• 说明：混淆后符号的前缀
• 推荐值：2-4个大写字母，如"WHC"、"APP"
• 作用：避免与系统API冲突，便于调试识别
• 示例：WHCa3f2b、APPd7e9c

• 种子值 (seed)
• 说明：随机数生成器的种子
• 推荐值：留空（随机）或固定值（确定性）
• 适用场景：
  - 空值：每次混淆结果不同（推荐）
  - 固定值：每次混淆结果相同（便于对比）

🛡️ 白名单管理

• 符号白名单
• 说明：不希望被混淆的类名、方法名等
• 内置保护：系统API、第三方库自动保护
• 自定义：可添加自己的符号白名单
• 操作方式：点击"白名单管理"按钮

• 字符串白名单
• 说明：不希望被加密的字符串
• 适用场景：系统API名称、配置键等
• 操作方式：点击"字符串白名单"按钮

✅ 推荐配置方案

标准方案（平衡）：
• 类名混淆：✓
• 方法名混淆：✓
• 属性名混淆：✓
• 垃圾代码：5-10个类
• 字符串加密：关键字符串
• 并行处理：✓

激进方案（最强）：
• 类名混淆：✓
• 方法名混淆：✓
• 属性名混淆：✓
• 协议名混淆：✓
• 垃圾代码：20-50个类
• 字符串加密：所有字符串
• 并行处理：✓

快速方案（测试）：
• 类名混淆：✓
• 垃圾代码：0个
• 其他：关闭
• 并行处理：✓

⚠️ 常见问题

Q: 混淆后编译失败？
A: 检查白名单配置，确保第三方库符号未被混淆

Q: 运行时崩溃？
A: 检查是否有动态调用的方法被混淆，添加到白名单

Q: 混淆速度慢？
A: 启用并行处理和缓存，减少垃圾代码数量

Q: 如何恢复原始代码？
A: 查看生成的映射文件（mapping.json），包含所有符号对应关系

💡 最佳实践

1. 首次使用建议使用"标准方案"
2. 混淆后务必完整测试应用功能
3. 保存好映射文件，便于调试和还原
4. 为每个版本保留独立的映射文件
5. 持续集成时使用固定种子值，便于对比
6. 关键功能模块可添加到白名单避免混淆

=== 技术支持 ===

如遇到问题，请查看：
• 项目文档：gui/modules/obfuscation/CLAUDE.md
• 使用指南：gui/modules/obfuscation/P2_USAGE_GUIDE.md
• GitHub Issues：提交问题和建议
"""


class ParameterHelpDialog:
    """参数帮助对话框"""

    def __init__(self, parent):
        """
        初始化参数帮助对话框

        Args:
            parent: 父窗口
        """
        self.parent = parent

    def show(self):
        """显示帮助对话框"""
        # 创建对话框窗口
        help_window = tk.Toplevel(self.parent)
        help_window.title("❓ 混淆参数详细说明")
        help_window.geometry("850x650")

        # 创建主容器
        main_container = ttk.Frame(help_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            title_frame,
            text="📖 iOS代码混淆参数说明",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

        ttk.Label(
            title_frame,
            text="新手指南：了解每个参数的含义和使用场景",
            font=("Arial", 9),
            foreground="gray"
        ).pack(side=tk.LEFT, padx=10)

        # 创建带滚动条的Text组件
        text_frame = ttk.Frame(main_container)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            padx=10,
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签样式
        text_widget.tag_config("title", font=("Arial", 12, "bold"), foreground="#2c3e50", spacing1=10, spacing3=5)
        text_widget.tag_config("subtitle", font=("Arial", 11, "bold"), foreground="#34495e", spacing1=8, spacing3=3)
        text_widget.tag_config("param", font=("Arial", 10, "bold"), foreground="#3498db")
        text_widget.tag_config("desc", font=("Arial", 10), foreground="#555555")
        text_widget.tag_config("example", font=("Consolas", 9) if os.name == 'nt' else ("Monaco", 9), foreground="#16a085", background="#ecf0f1")
        text_widget.tag_config("tip", font=("Arial", 9), foreground="#e67e22", background="#fef9e7")
        text_widget.tag_config("warning", font=("Arial", 9), foreground="#e74c3c", background="#fadbd8")
        text_widget.tag_config("section", font=("Arial", 10, "bold"), foreground="#8e44ad")

        # 插入内容
        content = PARAMETER_HELP_CONTENT
        for line in content.split('\n'):
            if line.startswith('==='):
                text_widget.insert(tk.END, line + '\n', 'title')
            elif line.startswith('📝') or line.startswith('🎨') or line.startswith('⚡') or line.startswith('🔤') or line.startswith('🛡️'):
                text_widget.insert(tk.END, line + '\n', 'subtitle')
            elif line.startswith('• 说明：') or line.startswith('• 适用场景：') or line.startswith('• 工作原理：') or line.startswith('• 检测方式：') or line.startswith('• 推荐值：') or line.startswith('• 使用场景：') or line.startswith('• 操作方式：') or line.startswith('• 内置保护：') or line.startswith('• 自定义：') or line.startswith('• 作用：') or line.startswith('• 性能提升：') or line.startswith('• 加密算法：'):
                text_widget.insert(tk.END, line + '\n', 'param')
            elif line.startswith('• 示例：') or line.startswith('  原始：') or line.startswith('  混淆：'):
                text_widget.insert(tk.END, line + '\n', 'example')
            elif line.startswith('• ⚠️') or line.startswith('⚠️'):
                text_widget.insert(tk.END, line + '\n', 'warning')
            elif line.startswith('• ✅') or line.startswith('• 💡') or line.startswith('✅') or line.startswith('💡'):
                text_widget.insert(tk.END, line + '\n', 'tip')
            elif line.startswith('Q:') or line.startswith('A:'):
                text_widget.insert(tk.END, line + '\n', 'section')
            else:
                text_widget.insert(tk.END, line + '\n', 'desc')

        # 设置只读
        text_widget.config(state=tk.DISABLED)

        # 底部工具栏
        toolbar_frame = ttk.Frame(main_container)
        toolbar_frame.pack(fill=tk.X, pady=(10, 0))

        # 快速查找功能
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.LEFT)

        ttk.Label(search_frame, text="快速查找:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
        search_entry.pack(side=tk.LEFT)

        def search_text(event=None):
            """搜索文本"""
            # 临时启用编辑
            text_widget.config(state=tk.NORMAL)

            # 移除之前的高亮
            text_widget.tag_remove('search', '1.0', tk.END)

            query = search_var.get()
            if not query:
                text_widget.config(state=tk.DISABLED)
                return

            # 搜索并高亮
            start = '1.0'
            while True:
                pos = text_widget.search(query, start, stopindex=tk.END, nocase=True)
                if not pos:
                    break

                end = f"{pos}+{len(query)}c"
                text_widget.tag_add('search', pos, end)
                start = end

            # 跳转到第一个匹配
            first_match = text_widget.search(query, '1.0', stopindex=tk.END, nocase=True)
            if first_match:
                text_widget.see(first_match)

            # 恢复只读
            text_widget.config(state=tk.DISABLED)

        search_entry.bind('<Return>', search_text)
        ttk.Button(search_frame, text="搜索", command=search_text, width=6).pack(side=tk.LEFT, padx=3)

        # 配置搜索高亮标签
        text_widget.tag_config('search', background='yellow', foreground='black')

        # 关闭按钮
        ttk.Button(
            toolbar_frame,
            text="关闭",
            command=help_window.destroy,
            width=10
        ).pack(side=tk.RIGHT)
