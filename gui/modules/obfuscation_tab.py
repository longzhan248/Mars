"""
iOS代码混淆标签页 - GUI界面

提供完整的iOS项目代码混淆功能，包括：
1. 项目选择和配置
2. 实时进度显示
3. 映射查看和导出
4. 白名单管理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from pathlib import Path
import threading
import json
from datetime import datetime

# 导入辅助模块
from .parameter_help_content import PARAMETER_HELP_CONTENT
from .obfuscation_templates import OBFUSCATION_TEMPLATES, get_template
from .whitelist_ui_helper import WhitelistUIHelper


class ObfuscationTab(ttk.Frame):
    """iOS代码混淆标签页"""

    def __init__(self, parent, main_app):
        """
        初始化混淆标签页

        Args:
            parent: 父窗口
            main_app: 主应用程序实例
        """
        super().__init__(parent)
        self.main_app = main_app

        # 延迟导入，避免启动时加载
        self.config_manager = None
        self.obfuscation_engine = None

        # 当前状态
        self.project_path = None
        self.output_path = None
        self.current_config = None
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        """创建UI组件"""

        # 顶部信息栏 - 使用Frame包装标题和说明，添加背景色
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 标题
        title_label = ttk.Label(
            header_frame,
            text="🔐 iOS代码混淆工具",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor=tk.W)

        # 说明文本 - 更简洁的表述
        desc_text = "应对App Store审核(4.3/2.1)，支持ObjC/Swift符号混淆，智能保护系统API和第三方库"
        desc_label = ttk.Label(
            header_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(2, 0))

        # 创建主容器（使用PanedWindow实现上下分割）
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 上半部分：配置区域 ===
        config_frame = ttk.Frame(paned)
        paned.add(config_frame, weight=1)

        # 快速配置模板选择
        template_frame = ttk.Frame(config_frame)
        template_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(template_frame, text="⚡ 快速配置:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        template_buttons = [
            ("最小化", "minimal", "仅混淆类名和方法名"),
            ("标准", "standard", "平衡的混淆策略"),
            ("激进", "aggressive", "最强混淆力度")
        ]

        for label, template, tooltip in template_buttons:
            btn = ttk.Button(
                template_frame,
                text=label,
                command=lambda t=template: self.load_template(t),
                width=8
            )
            btn.pack(side=tk.LEFT, padx=2)
            # TODO: 添加tooltip支持

        # 项目路径选择 - 更紧凑的布局
        path_frame = ttk.LabelFrame(config_frame, text="📁 项目配置", padding=10)
        path_frame.pack(fill=tk.X, pady=5)

        # 输入项目路径
        input_frame = ttk.Frame(path_frame)
        input_frame.pack(fill=tk.X, pady=3)

        ttk.Label(input_frame, text="源项目:", width=8).pack(side=tk.LEFT)
        self.project_path_var = tk.StringVar()
        self.project_entry = ttk.Entry(
            input_frame,
            textvariable=self.project_path_var
        )
        self.project_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            input_frame,
            text="📂 浏览",
            command=self.select_project,
            width=8
        ).pack(side=tk.LEFT)

        # 输出路径
        output_frame = ttk.Frame(path_frame)
        output_frame.pack(fill=tk.X, pady=3)

        ttk.Label(output_frame, text="输出目录:", width=8).pack(side=tk.LEFT)
        self.output_path_var = tk.StringVar()
        self.output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_path_var
        )
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            output_frame,
            text="📂 浏览",
            command=self.select_output,
            width=8
        ).pack(side=tk.LEFT)

        # 配置选项 - 使用Canvas实现滚动（限制高度避免按钮被挤出视图）
        options_container = ttk.LabelFrame(config_frame, text="⚙️ 混淆选项", padding=5)
        options_container.pack(fill=tk.X, pady=5)  # 不使用expand，确保按钮区域可见

        # 创建Canvas和Scrollbar - 减小高度确保按钮可见
        canvas = tk.Canvas(options_container, highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(options_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮支持（仅在Canvas区域内）
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        # 使用三列布局以节省空间
        left_options = ttk.Frame(scrollable_frame)
        left_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        middle_options = ttk.Frame(scrollable_frame)
        middle_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        right_options = ttk.Frame(scrollable_frame)
        right_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 左列 - 基本混淆选项
        ttk.Label(left_options, text="📝 基本混淆", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.obfuscate_classes = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_options,
            text="类名",
            variable=self.obfuscate_classes
        ).pack(anchor=tk.W, pady=1)

        self.obfuscate_methods = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_options,
            text="方法名",
            variable=self.obfuscate_methods
        ).pack(anchor=tk.W, pady=1)

        self.obfuscate_properties = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_options,
            text="属性名",
            variable=self.obfuscate_properties
        ).pack(anchor=tk.W, pady=1)

        self.obfuscate_protocols = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_options,
            text="协议名",
            variable=self.obfuscate_protocols
        ).pack(anchor=tk.W, pady=1)

        # 中列 - 资源处理选项
        ttk.Label(middle_options, text="🎨 资源处理", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.modify_resources = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            middle_options,
            text="XIB/Storyboard",
            variable=self.modify_resources
        ).pack(anchor=tk.W, pady=1)

        self.modify_images = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            middle_options,
            text="图片像素修改",
            variable=self.modify_images
        ).pack(anchor=tk.W, pady=1)

        self.modify_audio = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            middle_options,
            text="音频hash修改",
            variable=self.modify_audio
        ).pack(anchor=tk.W, pady=1)

        self.modify_fonts = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            middle_options,
            text="字体文件处理",
            variable=self.modify_fonts
        ).pack(anchor=tk.W, pady=1)

        # 自动添加到Xcode项目
        self.auto_add_to_xcode = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            middle_options,
            text="自动添加到Xcode",
            variable=self.auto_add_to_xcode
        ).pack(anchor=tk.W, pady=1)

        # 右列 - 高级选项
        ttk.Label(right_options, text="⚡ 高级选项", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.auto_detect_third_party = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            right_options,
            text="自动检测第三方库",
            variable=self.auto_detect_third_party
        ).pack(anchor=tk.W, pady=1)

        self.use_fixed_seed = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right_options,
            text="确定性混淆",
            variable=self.use_fixed_seed
        ).pack(anchor=tk.W, pady=1)

        # P2高级混淆选项
        self.insert_garbage_code = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right_options,
            text="插入垃圾代码 🆕",
            variable=self.insert_garbage_code
        ).pack(anchor=tk.W, pady=1)

        self.string_encryption = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            right_options,
            text="字符串加密 🆕",
            variable=self.string_encryption
        ).pack(anchor=tk.W, pady=1)

        # P2垃圾代码配置（当checkbox启用时生效）
        garbage_config_frame = ttk.Frame(right_options)
        garbage_config_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        # 垃圾类数量
        ttk.Label(garbage_config_frame, text="垃圾类数:", width=8, font=("Arial", 8)).pack(side=tk.LEFT)
        self.garbage_count = tk.IntVar(value=20)
        garbage_count_spinbox = ttk.Spinbox(
            garbage_config_frame,
            from_=5,
            to=100,
            textvariable=self.garbage_count,
            width=6
        )
        garbage_count_spinbox.pack(side=tk.LEFT, padx=2)

        # 垃圾复杂度
        ttk.Label(garbage_config_frame, text="复杂度:", width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        self.garbage_complexity = tk.StringVar(value="moderate")
        complexity_combo = ttk.Combobox(
            garbage_config_frame,
            textvariable=self.garbage_complexity,
            values=["simple", "moderate", "complex"],
            state="readonly",
            width=8
        )
        complexity_combo.pack(side=tk.LEFT, padx=2)

        # P2.3调用关系生成配置（第二行）
        call_config_frame = ttk.Frame(right_options)
        call_config_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        # 启用调用关系
        self.enable_call_relationships = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            call_config_frame,
            text="调用关系 🔗",
            variable=self.enable_call_relationships,
            width=10
        ).pack(side=tk.LEFT)

        # 调用密度
        ttk.Label(call_config_frame, text="密度:", width=5, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        self.call_density = tk.StringVar(value="medium")
        density_combo = ttk.Combobox(
            call_config_frame,
            textvariable=self.call_density,
            values=["low", "medium", "high"],
            state="readonly",
            width=6
        )
        density_combo.pack(side=tk.LEFT, padx=2)

        # P2字符串加密配置（当checkbox启用时生效）
        string_config_frame = ttk.Frame(right_options)
        string_config_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        # 加密算法
        ttk.Label(string_config_frame, text="加密:", width=8, font=("Arial", 8)).pack(side=tk.LEFT)
        self.encryption_algorithm = tk.StringVar(value="xor")
        algorithm_combo = ttk.Combobox(
            string_config_frame,
            textvariable=self.encryption_algorithm,
            values=["xor", "base64", "shift", "rot13", "aes128", "aes256"],
            state="readonly",
            width=8
        )
        algorithm_combo.pack(side=tk.LEFT, padx=2)

        # 最小长度
        ttk.Label(string_config_frame, text="最小:", width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        self.string_min_length = tk.IntVar(value=4)
        min_length_spinbox = ttk.Spinbox(
            string_config_frame,
            from_=1,
            to=20,
            textvariable=self.string_min_length,
            width=4
        )
        min_length_spinbox.pack(side=tk.LEFT, padx=2)

        # 字符串加密白名单按钮（第二行）
        string_whitelist_frame = ttk.Frame(right_options)
        string_whitelist_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Button(
            string_whitelist_frame,
            text="🛡️ 加密白名单",
            command=self.manage_string_whitelist,
            width=14
        ).pack(side=tk.LEFT)

        # 分隔线
        ttk.Separator(right_options, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # 命名配置区域
        ttk.Label(right_options, text="🔤 命名配置", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        # 命名策略
        strategy_frame = ttk.Frame(right_options)
        strategy_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Label(strategy_frame, text="策略:", width=5).pack(side=tk.LEFT)
        self.naming_strategy = tk.StringVar(value="random")
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.naming_strategy,
            values=["random", "prefix", "pattern", "dictionary"],
            state="readonly",
            width=12
        )
        strategy_combo.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # 名称前缀
        prefix_frame = ttk.Frame(right_options)
        prefix_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Label(prefix_frame, text="前缀:", width=5).pack(side=tk.LEFT)
        self.name_prefix = tk.StringVar(value="WHC")
        prefix_entry = ttk.Entry(
            prefix_frame,
            textvariable=self.name_prefix,
            width=12
        )
        prefix_entry.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # 图片修改强度
        intensity_frame = ttk.Frame(middle_options)
        intensity_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        ttk.Label(intensity_frame, text="强度:", width=5).pack(side=tk.LEFT)
        self.image_intensity = tk.DoubleVar(value=0.02)
        intensity_spinbox = ttk.Spinbox(
            intensity_frame,
            from_=0.005,
            to=0.10,
            increment=0.005,
            textvariable=self.image_intensity,
            width=8,
            format="%.3f"
        )
        intensity_spinbox.pack(side=tk.LEFT, padx=3)

        # 操作按钮区域 - 更清晰的分组
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=8)

        # 左侧：执行按钮
        action_frame = ttk.Frame(button_frame)
        action_frame.pack(side=tk.LEFT)

        self.start_button = ttk.Button(
            action_frame,
            text="▶️ 开始混淆",
            command=self.start_obfuscation,
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=3)

        self.stop_button = ttk.Button(
            action_frame,
            text="⏹️ 停止",
            command=self.stop_obfuscation,
            state=tk.DISABLED,
            width=10
        )
        self.stop_button.pack(side=tk.LEFT, padx=3)

        # 中间：白名单管理和参数说明
        whitelist_frame = ttk.Frame(button_frame)
        whitelist_frame.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            whitelist_frame,
            text="🛡️ 管理白名单",
            command=self.manage_whitelist,
            width=14
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            whitelist_frame,
            text="❓ 参数说明",
            command=self.show_parameter_help,
            width=12
        ).pack(side=tk.LEFT, padx=3)

        # 右侧：映射管理按钮
        mapping_frame = ttk.Frame(button_frame)
        mapping_frame.pack(side=tk.RIGHT)

        ttk.Button(
            mapping_frame,
            text="📋 查看映射",
            command=self.view_mapping,
            width=12
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            mapping_frame,
            text="💾 导出映射",
            command=self.export_mapping,
            width=12
        ).pack(side=tk.LEFT, padx=3)

        # === 下半部分：日志和进度 ===
        log_frame = ttk.Frame(paned)
        paned.add(log_frame, weight=2)

        # 进度条区域 - 更紧凑和美观
        progress_frame = ttk.LabelFrame(log_frame, text="📊 执行进度", padding=8)
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        # 进度条和百分比
        progress_inner = ttk.Frame(progress_frame)
        progress_inner.pack(fill=tk.X)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_inner,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.progress_label = ttk.Label(
            progress_inner,
            text="0%",
            font=("Arial", 10, "bold"),
            width=5
        )
        self.progress_label.pack(side=tk.LEFT)

        # 状态文本
        self.status_label = ttk.Label(
            progress_frame,
            text="就绪",
            font=("Arial", 8),
            foreground="gray"
        )
        self.status_label.pack(anchor=tk.W, pady=(3, 0))

        # 日志输出区域
        log_label_frame = ttk.LabelFrame(log_frame, text="📝 执行日志", padding=5)
        log_label_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_label_frame,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 9) if os.name == 'nt' else ("Monaco", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志文本标签（用于颜色高亮）
        self.log_text.tag_config("success", foreground="#28a745")
        self.log_text.tag_config("error", foreground="#dc3545")
        self.log_text.tag_config("warning", foreground="#ffc107")
        self.log_text.tag_config("info", foreground="#17a2b8")
        self.log_text.tag_config("header", foreground="#6c757d", font=("Consolas", 9, "bold") if os.name == 'nt' else ("Monaco", 9, "bold"))

    def load_template(self, template_name):
        """加载配置模板"""
        t = get_template(template_name)

        if t:
            self.obfuscate_classes.set(t["class_names"])
            self.obfuscate_methods.set(t["method_names"])
            self.obfuscate_properties.set(t["property_names"])
            self.obfuscate_protocols.set(t["protocol_names"])
            self.modify_resources.set(t["resources"])
            self.modify_images.set(t["images"])
            self.modify_audio.set(t["audio"])
            self.modify_fonts.set(t["fonts"])
            self.auto_add_to_xcode.set(t.get("auto_add_to_xcode", True))  # P2高级资源处理配置
            self.auto_detect_third_party.set(t["auto_detect"])
            self.use_fixed_seed.set(t["fixed_seed"])

            # 加载P2高级混淆选项
            self.insert_garbage_code.set(t.get("insert_garbage_code", False))
            self.garbage_count.set(t.get("garbage_count", 20))
            self.garbage_complexity.set(t.get("garbage_complexity", "moderate"))
            self.string_encryption.set(t.get("string_encryption", False))
            self.encryption_algorithm.set(t.get("encryption_algorithm", "xor"))
            self.string_min_length.set(t.get("string_min_length", 4))

            self.log(f"✅ 已加载 '{template_name}' 配置模板")

    def select_project(self):
        """选择项目目录"""
        directory = filedialog.askdirectory(
            title="选择iOS项目目录"
        )
        if directory:
            self.project_path = directory
            self.project_path_var.set(directory)

            # 自动设置输出路径
            if not self.output_path:
                output_dir = os.path.join(
                    os.path.dirname(directory),
                    f"{os.path.basename(directory)}_obfuscated"
                )
                self.output_path = output_dir
                self.output_path_var.set(output_dir)

            self.log(f"📁 已选择项目: {directory}")

    def select_output(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录"
        )
        if directory:
            self.output_path = directory
            self.output_path_var.set(directory)
            self.log(f"📂 输出目录: {directory}")

    def start_obfuscation(self):
        """开始混淆"""
        # 验证输入
        if not self.project_path:
            messagebox.showerror("错误", "请先选择项目目录")
            return

        if not self.output_path:
            messagebox.showerror("错误", "请先选择输出目录")
            return

        if not os.path.exists(self.project_path):
            messagebox.showerror("错误", "项目目录不存在")
            return

        # 确认开始
        if not messagebox.askyesno(
            "确认",
            f"即将对以下项目进行混淆:\n\n"
            f"输入: {self.project_path}\n"
            f"输出: {self.output_path}\n\n"
            f"是否继续？"
        ):
            return

        # 重置状态
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)

        self.log("="*80)
        self.log("开始iOS代码混淆")
        self.log("="*80)
        self.log(f"项目路径: {self.project_path}")
        self.log(f"输出路径: {self.output_path}")
        self.log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("")

        # 在后台线程执行混淆
        threading.Thread(
            target=self._run_obfuscation,
            daemon=True
        ).start()

    def _run_obfuscation(self):
        """在后台线程执行混淆（避免阻塞UI）"""
        try:
            # 延迟导入模块
            if self.config_manager is None:
                self.log("加载混淆模块...")
                from .obfuscation.config_manager import ObfuscationConfig, ConfigManager
                from .obfuscation.obfuscation_engine import ObfuscationEngine, ObfuscationResult
                from .obfuscation.xcode_project_manager import check_pbxproj_availability

                self.config_manager = ConfigManager
                self.obfuscation_engine_class = ObfuscationEngine
                self.obfuscation_config_class = ObfuscationConfig
                self.obfuscation_result_class = ObfuscationResult
                self.check_pbxproj = check_pbxproj_availability

            # 加载自定义白名单
            custom_whitelist = []
            whitelist_file = os.path.join(
                os.path.dirname(__file__),
                "obfuscation",
                "custom_whitelist.json"
            )

            if os.path.exists(whitelist_file):
                try:
                    with open(whitelist_file, 'r', encoding='utf-8') as f:
                        whitelist_data = json.load(f)
                        custom_whitelist = [item['name'] for item in whitelist_data.get('items', [])]

                    if custom_whitelist:
                        self.log(f"📋 已加载 {len(custom_whitelist)} 个自定义白名单项")
                except Exception as e:
                    self.log(f"⚠️  加载自定义白名单失败: {str(e)}")

            # 创建配置
            self.log("创建混淆配置...")
            config = self.obfuscation_config_class(
                name="gui_obfuscation",
                class_names=self.obfuscate_classes.get(),
                method_names=self.obfuscate_methods.get(),
                property_names=self.obfuscate_properties.get(),
                protocol_names=self.obfuscate_protocols.get(),
                naming_strategy=self.naming_strategy.get(),
                name_prefix=self.name_prefix.get(),
                auto_detect_third_party=self.auto_detect_third_party.get(),
                modify_resource_files=self.modify_resources.get(),
                use_fixed_seed=self.use_fixed_seed.get(),
                fixed_seed=f"gui_seed_{datetime.now().timestamp()}" if self.use_fixed_seed.get() else None,
                custom_whitelist=custom_whitelist  # 添加自定义白名单
            )

            # 添加P2高级资源处理配置
            config.modify_color_values = self.modify_images.get()
            config.image_intensity = self.image_intensity.get()
            config.modify_audio_files = self.modify_audio.get()
            config.modify_font_files = self.modify_fonts.get()
            config.auto_add_to_xcode = self.auto_add_to_xcode.get()  # 自动添加到Xcode项目

            # 检查pbxproj库依赖
            if config.auto_add_to_xcode and not self.check_pbxproj():
                self.log("⚠️  警告: auto_add_to_xcode已启用，但pbxproj库未安装")
                self.log("ℹ️  安装方法: pip install pbxproj")
                self.log("ℹ️  或者: source venv/bin/activate && pip install pbxproj")
                self.log("ℹ️  文件将生成但不会自动添加到Xcode项目，需手动添加")
                self.log("")

            # 加载字符串加密白名单
            string_whitelist = []
            string_whitelist_file = os.path.join(
                os.path.dirname(__file__),
                "obfuscation",
                "string_encryption_whitelist.json"
            )

            if os.path.exists(string_whitelist_file):
                try:
                    with open(string_whitelist_file, 'r', encoding='utf-8') as f:
                        whitelist_data = json.load(f)
                        string_whitelist = [item['content'] for item in whitelist_data.get('strings', [])]

                    if string_whitelist:
                        self.log(f"🛡️ 已加载 {len(string_whitelist)} 个字符串加密白名单项")
                except Exception as e:
                    self.log(f"⚠️  加载字符串加密白名单失败: {str(e)}")

            # 添加P2高级混淆配置
            config.insert_garbage_code = self.insert_garbage_code.get()
            config.garbage_count = self.garbage_count.get()
            config.garbage_complexity = self.garbage_complexity.get()
            config.string_encryption = self.string_encryption.get()
            config.encryption_algorithm = self.encryption_algorithm.get()
            config.string_min_length = self.string_min_length.get()
            config.string_whitelist_patterns = string_whitelist  # 添加字符串加密白名单

            # 添加P2.3调用关系生成配置
            config.enable_call_relationships = self.enable_call_relationships.get()
            config.call_density = self.call_density.get()
            config.max_call_depth = 3  # 固定深度为3

            # 创建混淆引擎
            engine = self.obfuscation_engine_class(config)

            # 执行混淆（带进度回调）
            def progress_callback(progress, message):
                if not self.is_running:
                    raise InterruptedError("用户取消")

                self.update_progress(progress * 100, message)

            self.log("开始混淆流程...")
            result = engine.obfuscate(
                self.project_path,
                self.output_path,
                progress_callback=progress_callback
            )

            # 显示结果
            self.log("")
            self.log("="*80)
            if result.success:
                self.log("✅ 混淆成功完成！")
                self.log(f"处理文件: {result.files_processed} 个")
                self.log(f"失败文件: {result.files_failed} 个")
                self.log(f"总替换次数: {result.total_replacements}")
                self.log(f"耗时: {result.elapsed_time:.2f} 秒")
                self.log(f"映射文件: {result.mapping_file}")

                # 显示统计信息
                stats = engine.get_statistics()
                self.log("")
                self.log("详细统计:")
                self.log(f"  - 项目类型: {stats['project']['type']}")
                self.log(f"  - 总文件数: {stats['project']['total_files']}")
                self.log(f"  - 总代码行数: {stats['project']['total_lines']}")
                self.log(f"  - 白名单项: {stats['whitelist'].get('total_items', 0)}")
                self.log(f"  - 生成映射: {stats['generator'].get('total_mappings', 0)}")

                # 显示P2高级资源处理统计
                if 'advanced_resources' in stats and stats['advanced_resources']:
                    adv_stats = stats['advanced_resources']
                    if adv_stats.get('files_processed', 0) > 0:
                        self.log("")
                        self.log("P2高级资源处理:")
                        self.log(f"  - 处理文件总数: {adv_stats['files_processed']}")
                        self.log(f"  - 成功: {adv_stats['success_count']}")
                        self.log(f"  - 失败: {adv_stats['failure_count']}")
                        if adv_stats.get('images_modified', 0) > 0:
                            self.log(f"  - 图片修改: {adv_stats['images_modified']}")
                        if adv_stats.get('audios_modified', 0) > 0:
                            self.log(f"  - 音频修改: {adv_stats['audios_modified']}")
                        if adv_stats.get('fonts_processed', 0) > 0:
                            self.log(f"  - 字体处理: {adv_stats['fonts_processed']}")
                        if adv_stats.get('assets_processed', 0) > 0:
                            self.log(f"  - Assets处理: {adv_stats['assets_processed']}")

                messagebox.showinfo(
                    "成功",
                    f"混淆成功完成！\n\n"
                    f"处理文件: {result.files_processed} 个\n"
                    f"总替换次数: {result.total_replacements}\n"
                    f"耗时: {result.elapsed_time:.2f} 秒\n\n"
                    f"输出目录: {result.output_dir}"
                )
            else:
                self.log("❌ 混淆失败")
                for error in result.errors:
                    self.log(f"错误: {error}")

                messagebox.showerror(
                    "失败",
                    f"混淆失败\n\n错误信息:\n" + "\n".join(result.errors[:5])
                )

            self.log("="*80)

        except InterruptedError:
            self.log("\n⚠️  混淆已取消")
            messagebox.showwarning("取消", "混淆已被用户取消")

        except Exception as e:
            self.log(f"\n❌ 发生异常: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("错误", f"混淆过程发生异常:\n{str(e)}")

        finally:
            # 恢复按钮状态
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(100, "完成")

    def stop_obfuscation(self):
        """停止混淆"""
        if messagebox.askyesno("确认", "确定要停止混淆吗？"):
            self.is_running = False
            self.log("\n正在停止...")

    def view_mapping(self):
        """查看映射文件"""
        if not self.output_path:
            messagebox.showinfo("提示", "请先执行混淆生成映射文件")
            return

        mapping_file = os.path.join(self.output_path, "obfuscation_mapping.json")

        if not os.path.exists(mapping_file):
            messagebox.showinfo("提示", "映射文件不存在，请先执行混淆")
            return

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

            # 创建查看窗口
            view_window = tk.Toplevel(self)
            view_window.title("混淆映射")
            view_window.geometry("800x600")

            # 统计信息
            if 'metadata' in mappings:
                info_frame = ttk.Frame(view_window)
                info_frame.pack(fill=tk.X, padx=10, pady=5)

                metadata = mappings['metadata']
                info_text = (
                    f"策略: {metadata.get('strategy', 'N/A')}  |  "
                    f"前缀: {metadata.get('prefix', 'N/A')}  |  "
                    f"总映射: {metadata.get('total_mappings', 0)}"
                )
                ttk.Label(info_frame, text=info_text).pack()

            # 映射列表
            tree_frame = ttk.Frame(view_window)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # 创建Treeview
            columns = ("原始名称", "混淆名称", "类型", "文件")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=200)

            # 添加滚动条
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # 填充数据
            if 'mappings' in mappings:
                for mapping in mappings['mappings']:
                    tree.insert('', tk.END, values=(
                        mapping.get('original', ''),
                        mapping.get('obfuscated', ''),
                        mapping.get('type', ''),
                        os.path.basename(mapping.get('source_file', ''))
                    ))

            # 按钮
            button_frame = ttk.Frame(view_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Button(
                button_frame,
                text="关闭",
                command=view_window.destroy
            ).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("错误", f"无法读取映射文件:\n{str(e)}")

    def export_mapping(self):
        """导出映射文件"""
        if not self.output_path:
            messagebox.showinfo("提示", "请先执行混淆生成映射文件")
            return

        mapping_file = os.path.join(self.output_path, "obfuscation_mapping.json")

        if not os.path.exists(mapping_file):
            messagebox.showinfo("提示", "映射文件不存在，请先执行混淆")
            return

        # 选择保存位置
        save_path = filedialog.asksaveasfilename(
            title="导出映射文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if save_path:
            try:
                import shutil
                shutil.copy2(mapping_file, save_path)
                messagebox.showinfo("成功", f"映射文件已导出到:\n{save_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{str(e)}")

    def manage_whitelist(self):
        """管理自定义白名单"""
        # 创建白名单管理窗口
        whitelist_window = tk.Toplevel(self)
        whitelist_window.title("🛡️ 自定义白名单管理")
        whitelist_window.geometry("700x550")

        # 说明文本
        desc_frame = ttk.Frame(whitelist_window)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)

        desc_text = ("自定义白名单用于保护不希望被混淆的符号（类名、方法名、属性名等）。\n"
                    "系统API和第三方库已自动保护，无需手动添加。")
        ttk.Label(
            desc_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # 工具栏
        toolbar = ttk.Frame(whitelist_window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            toolbar,
            text="➕ 添加",
            command=lambda: self.add_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="✏️ 编辑",
            command=lambda: self.edit_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="🗑️ 删除",
            command=lambda: self.delete_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📂 导入",
            command=lambda: self.import_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="💾 导出",
            command=lambda: self.export_whitelist_file(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        # 白名单列表
        list_frame = ttk.LabelFrame(whitelist_window, text="白名单项", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建Treeview
        columns = ("名称", "类型", "备注")
        tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", selectmode="browse")

        # 配置列
        tree.heading("#0", text="")
        tree.column("#0", width=30)
        tree.heading("名称", text="名称")
        tree.column("名称", width=200)
        tree.heading("类型", text="类型")
        tree.column("类型", width=100)
        tree.heading("备注", text="备注")
        tree.column("备注", width=300)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载自定义白名单
        self.load_custom_whitelist(tree)

        # 双击编辑
        tree.bind("<Double-1>", lambda e: self.edit_whitelist_item(tree))

        # 统计信息
        stats_frame = ttk.Frame(whitelist_window)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        stats_label = ttk.Label(stats_frame, text="", font=("Arial", 9))
        stats_label.pack(side=tk.LEFT)

        # 更新统计
        def update_stats():
            count = len(tree.get_children())
            stats_label.config(text=f"共 {count} 个自定义白名单项")

        update_stats()

        # 关闭按钮
        button_frame = ttk.Frame(whitelist_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="关闭",
            command=whitelist_window.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # 保存刷新统计的引用
        tree.update_stats = update_stats

    def load_custom_whitelist(self, tree):
        """加载自定义白名单"""
        whitelist_file = WhitelistUIHelper.get_whitelist_file_path(os.path.dirname(__file__))
        WhitelistUIHelper.load_whitelist(tree, whitelist_file, self.log)

    def save_custom_whitelist(self, tree):
        """保存自定义白名单"""
        whitelist_file = WhitelistUIHelper.get_whitelist_file_path(os.path.dirname(__file__))
        return WhitelistUIHelper.save_whitelist(tree, whitelist_file, self.log)

    def add_whitelist_item(self, tree):
        """添加白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self)
        dialog.title("添加白名单项")
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()

        # 名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(name_frame, text="符号名称:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        name_entry.focus()

        # 类型
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(type_frame, text="类型:", width=10).pack(side=tk.LEFT)
        type_var = tk.StringVar(value="class")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "enum", "constant", "custom"],
            state="readonly"
        )
        type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入符号名称", parent=dialog)
                return

            # 添加到列表
            tree.insert('', tk.END, values=(
                name,
                type_var.get(),
                reason_var.get()
            ))

            # 保存
            self.save_custom_whitelist(tree)
            tree.update_stats()

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    def edit_whitelist_item(self, tree):
        """编辑白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要编辑的项")
            return

        item_id = selection[0]
        values = tree.item(item_id, 'values')

        # 创建编辑对话框
        dialog = tk.Toplevel(self)
        dialog.title("编辑白名单项")
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()

        # 名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(name_frame, text="符号名称:", width=10).pack(side=tk.LEFT)
        name_var = tk.StringVar(value=values[0])
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        name_entry.focus()

        # 类型
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(type_frame, text="类型:", width=10).pack(side=tk.LEFT)
        type_var = tk.StringVar(value=values[1])
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=["class", "method", "property", "protocol", "enum", "constant", "custom"],
            state="readonly"
        )
        type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar(value=values[2])
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入符号名称", parent=dialog)
                return

            # 更新列表
            tree.item(item_id, values=(
                name,
                type_var.get(),
                reason_var.get()
            ))

            # 保存
            self.save_custom_whitelist(tree)

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    def delete_whitelist_item(self, tree):
        """删除白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的白名单项吗？"):
            for item_id in selection:
                tree.delete(item_id)

            # 保存
            self.save_custom_whitelist(tree)
            tree.update_stats()

    def import_whitelist(self, tree):
        """导入白名单"""
        file_path = filedialog.askopenfilename(
            title="导入白名单",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    items = data.get('items', [])
                else:
                    # 文本文件，每行一个名称
                    items = [{'name': line.strip(), 'type': 'custom', 'reason': '从文件导入'}
                             for line in f if line.strip()]

            # 添加到列表
            for item in items:
                tree.insert('', tk.END, values=(
                    item.get('name', ''),
                    item.get('type', 'custom'),
                    item.get('reason', '')
                ))

            # 保存
            self.save_custom_whitelist(tree)
            tree.update_stats()

            messagebox.showinfo("成功", f"已导入 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{str(e)}")

    def export_whitelist_file(self, tree):
        """导出白名单"""
        if not tree.get_children():
            messagebox.showinfo("提示", "白名单为空，无需导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出白名单",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            items = []
            for item_id in tree.get_children():
                values = tree.item(item_id, 'values')
                items.append({
                    'name': values[0],
                    'type': values[1],
                    'reason': values[2]
                })

            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump({
                        'version': '1.0',
                        'exported': datetime.now().isoformat(),
                        'items': items
                    }, f, indent=2, ensure_ascii=False)
                else:
                    # 文本文件，每行一个名称
                    for item in items:
                        f.write(item['name'] + '\n')

            messagebox.showinfo("成功", f"已导出 {len(items)} 个白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")

    def update_progress(self, progress, message):
        """更新进度（在主线程中调用）"""
        def _update():
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress:.0f}%")
            self.status_label.config(text=message)
            self.log(f"[{progress:.0f}%] {message}")

        self.after(0, _update)

    def log(self, message):
        """添加日志（在主线程中调用）- 支持颜色高亮"""
        def _log():
            # 根据消息内容添加颜色标签
            tag = None
            if "✅" in message or "成功" in message:
                tag = "success"
            elif "❌" in message or "错误" in message or "失败" in message:
                tag = "error"
            elif "⚠️" in message or "警告" in message:
                tag = "warning"
            elif message.startswith("="):
                tag = "header"
            elif message.startswith("["):
                tag = "info"

            self.log_text.insert(tk.END, message + "\n", tag)
            self.log_text.see(tk.END)

        self.after(0, _log)

    def show_parameter_help(self):
        """显示参数说明对话框"""
        help_window = tk.Toplevel(self)
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

        # 参数说明内容
        content = PARAMETER_HELP_CONTENT

        # 插入内容
        for line in content.split('\n'):
            if line.startswith('==='):
                text_widget.insert(tk.END, line + '\n', 'title')
            elif line.startswith('📝') or line.startswith('🎨') or line.startswith('⚡') or line.startswith('🔤') or line.startswith('🛡️'):
                text_widget.insert(tk.END, line + '\n', 'subtitle')
            elif line.startswith('• 说明：') or line.startswith('• 适用场景：') or line.startswith('• 工作原理：') or line.startswith('• 检测方式：') or line.startswith('• 推荐值：') or line.startswith('• 使用场景：') or line.startswith('• 操作方式：'):
                text_widget.insert(tk.END, line + '\n', 'param')
            elif line.startswith('• 示例：') or line.startswith('  原始：') or line.startswith('  混淆：'):
                text_widget.insert(tk.END, line + '\n', 'example')
            elif line.startswith('• ⚠️'):
                text_widget.insert(tk.END, line + '\n', 'warning')
            elif line.startswith('• ✅') or line.startswith('• 💡'):
                text_widget.insert(tk.END, line + '\n', 'tip')
            elif line.startswith('✅') or line.startswith('⚠️'):
                text_widget.insert(tk.END, line + '\n', 'section')
            else:
                text_widget.insert(tk.END, line + '\n', 'desc')

        # 设置只读
        text_widget.config(state=tk.DISABLED)

        # 关闭按钮
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="关闭",
            command=help_window.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # 快速查找功能
        search_frame = ttk.Frame(button_frame)
        search_frame.pack(side=tk.LEFT)

        ttk.Label(search_frame, text="快速查找:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
        search_entry.pack(side=tk.LEFT)

        def search_text(event=None):
            """搜索文本"""
            # 移除之前的高亮
            text_widget.tag_remove('search', '1.0', tk.END)

            query = search_var.get()
            if not query:
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

        search_entry.bind('<Return>', search_text)
        ttk.Button(search_frame, text="搜索", command=search_text, width=6).pack(side=tk.LEFT, padx=3)

        # 配置搜索高亮标签
        text_widget.tag_config('search', background='yellow', foreground='black')

    def manage_string_whitelist(self):
        """管理字符串加密白名单"""
        # 创建白名单管理窗口
        whitelist_window = tk.Toplevel(self)
        whitelist_window.title("🛡️ 字符串加密白名单管理")
        whitelist_window.geometry("700x550")

        # 说明文本
        desc_frame = ttk.Frame(whitelist_window)
        desc_frame.pack(fill=tk.X, padx=10, pady=10)

        desc_text = ("字符串加密白名单用于保护不希望被加密的字符串常量。\n"
                    "例如：系统API名称、第三方SDK调用、配置键名等不应加密的字符串。")
        ttk.Label(
            desc_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # 工具栏
        toolbar = ttk.Frame(whitelist_window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            toolbar,
            text="➕ 添加",
            command=lambda: self.add_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="✏️ 编辑",
            command=lambda: self.edit_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="🗑️ 删除",
            command=lambda: self.delete_string_whitelist_item(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="📂 导入",
            command=lambda: self.import_string_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            toolbar,
            text="💾 导出",
            command=lambda: self.export_string_whitelist(tree),
            width=10
        ).pack(side=tk.LEFT, padx=3)

        # 白名单列表
        list_frame = ttk.LabelFrame(whitelist_window, text="字符串白名单", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建Treeview
        columns = ("字符串", "备注")
        tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", selectmode="browse")

        # 配置列
        tree.heading("#0", text="")
        tree.column("#0", width=30)
        tree.heading("字符串", text="字符串内容")
        tree.column("字符串", width=350)
        tree.heading("备注", text="备注说明")
        tree.column("备注", width=250)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载字符串加密白名单
        self.load_string_whitelist(tree)

        # 双击编辑
        tree.bind("<Double-1>", lambda e: self.edit_string_whitelist_item(tree))

        # 统计信息
        stats_frame = ttk.Frame(whitelist_window)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        stats_label = ttk.Label(stats_frame, text="", font=("Arial", 9))
        stats_label.pack(side=tk.LEFT)

        # 更新统计
        def update_stats():
            count = len(tree.get_children())
            stats_label.config(text=f"共 {count} 个字符串白名单项")

        update_stats()

        # 关闭按钮
        button_frame = ttk.Frame(whitelist_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="关闭",
            command=whitelist_window.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # 保存刷新统计的引用
        tree.update_stats = update_stats

    def load_string_whitelist(self, tree):
        """加载字符串加密白名单"""
        whitelist_file = os.path.join(
            os.path.dirname(__file__),
            "obfuscation",
            "string_encryption_whitelist.json"
        )

        if not os.path.exists(whitelist_file):
            return

        try:
            with open(whitelist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get('strings', [])

            for item in items:
                tree.insert('', tk.END, values=(
                    item.get('content', ''),
                    item.get('reason', '')
                ))
        except Exception as e:
            self.log(f"⚠️  加载字符串白名单失败: {str(e)}")

    def save_string_whitelist(self, tree):
        """保存字符串加密白名单"""
        whitelist_file = os.path.join(
            os.path.dirname(__file__),
            "obfuscation",
            "string_encryption_whitelist.json"
        )

        try:
            items = []
            for item_id in tree.get_children():
                values = tree.item(item_id, 'values')
                items.append({
                    'content': values[0],
                    'reason': values[1]
                })

            # 确保目录存在
            os.makedirs(os.path.dirname(whitelist_file), exist_ok=True)

            with open(whitelist_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '1.0',
                    'updated': datetime.now().isoformat(),
                    'strings': items
                }, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            self.log(f"⚠️  保存字符串白名单失败: {str(e)}")
            return False

    def add_string_whitelist_item(self, tree):
        """添加字符串白名单项"""
        # 创建添加对话框
        dialog = tk.Toplevel(self)
        dialog.title("添加字符串白名单")
        dialog.geometry("500x200")
        dialog.transient(self)
        dialog.grab_set()

        # 字符串内容
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(content_frame, text="字符串内容:", width=10).pack(side=tk.LEFT)
        content_var = tk.StringVar()
        content_entry = ttk.Entry(content_frame, textvariable=content_var)
        content_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        content_entry.focus()

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注说明:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            content = content_var.get().strip()
            if not content:
                messagebox.showwarning("提示", "请输入字符串内容", parent=dialog)
                return

            # 添加到列表
            tree.insert('', tk.END, values=(
                content,
                reason_var.get()
            ))

            # 保存
            self.save_string_whitelist(tree)
            tree.update_stats()

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    def edit_string_whitelist_item(self, tree):
        """编辑字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要编辑的项")
            return

        item_id = selection[0]
        values = tree.item(item_id, 'values')

        # 创建编辑对话框
        dialog = tk.Toplevel(self)
        dialog.title("编辑字符串白名单")
        dialog.geometry("500x200")
        dialog.transient(self)
        dialog.grab_set()

        # 字符串内容
        content_frame = ttk.Frame(dialog)
        content_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(content_frame, text="字符串内容:", width=10).pack(side=tk.LEFT)
        content_var = tk.StringVar(value=values[0])
        content_entry = ttk.Entry(content_frame, textvariable=content_var)
        content_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        content_entry.focus()

        # 备注
        reason_frame = ttk.Frame(dialog)
        reason_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(reason_frame, text="备注说明:", width=10).pack(side=tk.LEFT, anchor=tk.N)
        reason_var = tk.StringVar(value=values[1])
        reason_entry = ttk.Entry(reason_frame, textvariable=reason_var)
        reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def on_confirm():
            content = content_var.get().strip()
            if not content:
                messagebox.showwarning("提示", "请输入字符串内容", parent=dialog)
                return

            # 更新列表
            tree.item(item_id, values=(
                content,
                reason_var.get()
            ))

            # 保存
            self.save_string_whitelist(tree)

            dialog.destroy()

        ttk.Button(
            button_frame,
            text="确定",
            command=on_confirm,
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT)

        # Enter键确认
        dialog.bind('<Return>', lambda e: on_confirm())

    def delete_string_whitelist_item(self, tree):
        """删除字符串白名单项"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的项")
            return

        if messagebox.askyesno("确认", "确定要删除选中的字符串白名单项吗？"):
            for item_id in selection:
                tree.delete(item_id)

            # 保存
            self.save_string_whitelist(tree)
            tree.update_stats()

    def import_string_whitelist(self, tree):
        """导入字符串白名单"""
        file_path = filedialog.askopenfilename(
            title="导入字符串白名单",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    items = data.get('strings', [])
                else:
                    # 文本文件，每行一个字符串
                    items = [{'content': line.strip(), 'reason': '从文件导入'}
                             for line in f if line.strip()]

            # 添加到列表
            for item in items:
                tree.insert('', tk.END, values=(
                    item.get('content', ''),
                    item.get('reason', '')
                ))

            # 保存
            self.save_string_whitelist(tree)
            tree.update_stats()

            messagebox.showinfo("成功", f"已导入 {len(items)} 个字符串白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{str(e)}")

    def export_string_whitelist(self, tree):
        """导出字符串白名单"""
        if not tree.get_children():
            messagebox.showinfo("提示", "字符串白名单为空，无需导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出字符串白名单",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            items = []
            for item_id in tree.get_children():
                values = tree.item(item_id, 'values')
                items.append({
                    'content': values[0],
                    'reason': values[1]
                })

            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump({
                        'version': '1.0',
                        'exported': datetime.now().isoformat(),
                        'strings': items
                    }, f, indent=2, ensure_ascii=False)
                else:
                    # 文本文件，每行一个字符串
                    for item in items:
                        f.write(item['content'] + '\n')

            messagebox.showinfo("成功", f"已导出 {len(items)} 个字符串白名单项")

        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("iOS混淆工具测试")
    root.geometry("900x700")

    class MockApp:
        pass

    tab = ObfuscationTab(root, MockApp())
    tab.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
