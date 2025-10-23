"""
配置面板UI组件

提供iOS代码混淆的配置界面，包括：
- 快速模板选择
- 项目路径配置
- 混淆选项配置
- 资源处理选项
- 高级选项
"""

import tkinter as tk
from tkinter import ttk


class ConfigPanel(ttk.Frame):
    """配置面板组件"""

    def __init__(self, parent, tab):
        """
        初始化配置面板

        Args:
            parent: 父容器
            tab: ObfuscationTab实例（用于回调）
        """
        super().__init__(parent)
        self.tab = tab

        # 配置变量（存储在tab实例中，保持兼容性）
        self.init_variables()

        # 创建UI
        self.create_widgets()

    def init_variables(self):
        """验证配置变量已初始化"""
        # 验证变量是否已在tab中初始化
        required_vars = [
            'project_path_var', 'output_path_var',
            'obfuscate_classes', 'obfuscate_methods', 'obfuscate_properties', 'obfuscate_protocols',
            'modify_resources', 'modify_images', 'modify_audio', 'modify_fonts', 'auto_add_to_xcode',
            'auto_detect_third_party', 'use_fixed_seed', 'insert_garbage_code', 'string_encryption',
            'enable_call_relationships', 'enable_parse_cache',
            'garbage_count', 'garbage_complexity', 'call_density', 'encryption_algorithm',
            'string_min_length', 'naming_strategy', 'name_prefix', 'image_intensity'
        ]

        missing_vars = []
        for var_name in required_vars:
            if not hasattr(self.tab, var_name):
                missing_vars.append(var_name)

        if missing_vars:
            raise AttributeError(f"缺少必要的配置变量: {missing_vars}")

        # 变量已验证存在，无需重复初始化

    def create_widgets(self):
        """创建配置面板UI"""
        # 快速配置模板选择
        self.create_template_section()

        # 项目路径配置
        self.create_path_section()

        # 混淆选项配置
        self.create_options_section()

        # 操作按钮
        self.create_button_section()

    def create_template_section(self):
        """创建模板选择区域"""
        template_frame = ttk.Frame(self)
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
                command=lambda t=template: self.tab.load_template(t),
                width=8
            )
            btn.pack(side=tk.LEFT, padx=2)

    def create_path_section(self):
        """创建项目路径配置区域"""
        path_frame = ttk.LabelFrame(self, text="📁 项目配置", padding=10)
        path_frame.pack(fill=tk.X, pady=5)

        # 输入项目路径
        input_frame = ttk.Frame(path_frame)
        input_frame.pack(fill=tk.X, pady=3)

        ttk.Label(input_frame, text="源项目:", width=8).pack(side=tk.LEFT)
        self.tab.project_entry = ttk.Entry(
            input_frame,
            textvariable=self.tab.project_path_var
        )
        self.tab.project_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            input_frame,
            text="📂 浏览",
            command=self.tab.select_project,
            width=8
        ).pack(side=tk.LEFT)

        # 输出路径
        output_frame = ttk.Frame(path_frame)
        output_frame.pack(fill=tk.X, pady=3)

        ttk.Label(output_frame, text="输出目录:", width=8).pack(side=tk.LEFT)
        self.tab.output_entry = ttk.Entry(
            output_frame,
            textvariable=self.tab.output_path_var
        )
        self.tab.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(
            output_frame,
            text="📂 浏览",
            command=self.tab.select_output,
            width=8
        ).pack(side=tk.LEFT)

    def create_options_section(self):
        """创建混淆选项配置区域"""
        options_container = ttk.LabelFrame(self, text="⚙️ 混淆选项", padding=5)
        options_container.pack(fill=tk.X, pady=5)

        # 创建Canvas和Scrollbar实现滚动
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

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        # 使用三列布局
        left_options = ttk.Frame(scrollable_frame)
        left_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        middle_options = ttk.Frame(scrollable_frame)
        middle_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        right_options = ttk.Frame(scrollable_frame)
        right_options.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 左列 - 基本混淆选项
        self.create_basic_options(left_options)

        # 中列 - 资源处理选项
        self.create_resource_options(middle_options)

        # 右列 - 高级选项
        self.create_advanced_options(right_options)

    def create_basic_options(self, parent):
        """创建基本混淆选项"""
        ttk.Label(parent, text="📝 基本混淆", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        ttk.Checkbutton(
            parent,
            text="类名",
            variable=self.tab.obfuscate_classes
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="方法名",
            variable=self.tab.obfuscate_methods
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="属性名",
            variable=self.tab.obfuscate_properties
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="协议名",
            variable=self.tab.obfuscate_protocols
        ).pack(anchor=tk.W, pady=1)

    def create_resource_options(self, parent):
        """创建资源处理选项"""
        ttk.Label(parent, text="🎨 资源处理", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        ttk.Checkbutton(
            parent,
            text="XIB/Storyboard",
            variable=self.tab.modify_resources
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="图片像素修改",
            variable=self.tab.modify_images
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="音频hash修改",
            variable=self.tab.modify_audio
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="字体文件处理",
            variable=self.tab.modify_fonts
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="自动添加到Xcode",
            variable=self.tab.auto_add_to_xcode
        ).pack(anchor=tk.W, pady=1)

        # 图片修改强度
        intensity_frame = ttk.Frame(parent)
        intensity_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        ttk.Label(intensity_frame, text="强度:", width=5).pack(side=tk.LEFT)
        intensity_spinbox = ttk.Spinbox(
            intensity_frame,
            from_=0.005,
            to=0.10,
            increment=0.005,
            textvariable=self.tab.image_intensity,
            width=8,
            format="%.3f"
        )
        intensity_spinbox.pack(side=tk.LEFT, padx=3)

    def create_advanced_options(self, parent):
        """创建高级选项"""
        ttk.Label(parent, text="⚡ 高级选项", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        ttk.Checkbutton(
            parent,
            text="自动检测第三方库",
            variable=self.tab.auto_detect_third_party
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="确定性混淆",
            variable=self.tab.use_fixed_seed
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="插入垃圾代码 🆕",
            variable=self.tab.insert_garbage_code
        ).pack(anchor=tk.W, pady=1)

        ttk.Checkbutton(
            parent,
            text="字符串加密 🆕",
            variable=self.tab.string_encryption
        ).pack(anchor=tk.W, pady=1)

        # 垃圾代码配置
        self.create_garbage_config(parent)

        # 调用关系配置
        self.create_call_relationship_config(parent)

        # 字符串加密配置
        self.create_string_encryption_config(parent)

        # 命名配置
        self.create_naming_config(parent)

        # 性能优化
        self.create_performance_config(parent)

    def create_garbage_config(self, parent):
        """创建垃圾代码配置"""
        garbage_config_frame = ttk.Frame(parent)
        garbage_config_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        ttk.Label(garbage_config_frame, text="垃圾类数:", width=8, font=("Arial", 8)).pack(side=tk.LEFT)
        garbage_count_spinbox = ttk.Spinbox(
            garbage_config_frame,
            from_=5,
            to=100,
            textvariable=self.tab.garbage_count,
            width=6
        )
        garbage_count_spinbox.pack(side=tk.LEFT, padx=2)

        ttk.Label(garbage_config_frame, text="复杂度:", width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        complexity_combo = ttk.Combobox(
            garbage_config_frame,
            textvariable=self.tab.garbage_complexity,
            values=["simple", "moderate", "complex"],
            state="readonly",
            width=8
        )
        complexity_combo.pack(side=tk.LEFT, padx=2)

    def create_call_relationship_config(self, parent):
        """创建调用关系配置"""
        call_config_frame = ttk.Frame(parent)
        call_config_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Checkbutton(
            call_config_frame,
            text="调用关系 🔗",
            variable=self.tab.enable_call_relationships,
            width=10
        ).pack(side=tk.LEFT)

        ttk.Label(call_config_frame, text="密度:", width=5, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        density_combo = ttk.Combobox(
            call_config_frame,
            textvariable=self.tab.call_density,
            values=["low", "medium", "high"],
            state="readonly",
            width=6
        )
        density_combo.pack(side=tk.LEFT, padx=2)

    def create_string_encryption_config(self, parent):
        """创建字符串加密配置"""
        string_config_frame = ttk.Frame(parent)
        string_config_frame.pack(anchor=tk.W, fill=tk.X, pady=5)

        ttk.Label(string_config_frame, text="加密:", width=8, font=("Arial", 8)).pack(side=tk.LEFT)
        algorithm_combo = ttk.Combobox(
            string_config_frame,
            textvariable=self.tab.encryption_algorithm,
            values=["xor", "base64", "shift", "rot13", "aes128", "aes256"],
            state="readonly",
            width=8
        )
        algorithm_combo.pack(side=tk.LEFT, padx=2)

        ttk.Label(string_config_frame, text="最小:", width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=(5, 0))
        min_length_spinbox = ttk.Spinbox(
            string_config_frame,
            from_=1,
            to=20,
            textvariable=self.tab.string_min_length,
            width=4
        )
        min_length_spinbox.pack(side=tk.LEFT, padx=2)

        # 字符串加密白名单按钮
        string_whitelist_frame = ttk.Frame(parent)
        string_whitelist_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Button(
            string_whitelist_frame,
            text="🛡️ 加密白名单",
            command=self.tab.manage_string_whitelist,
            width=14
        ).pack(side=tk.LEFT)

    def create_naming_config(self, parent):
        """创建命名配置"""
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(parent, text="🔤 命名配置", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        # 命名策略
        strategy_frame = ttk.Frame(parent)
        strategy_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Label(strategy_frame, text="策略:", width=5).pack(side=tk.LEFT)
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.tab.naming_strategy,
            values=["random", "prefix", "pattern", "dictionary"],
            state="readonly",
            width=12
        )
        strategy_combo.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        # 名称前缀
        prefix_frame = ttk.Frame(parent)
        prefix_frame.pack(anchor=tk.W, fill=tk.X, pady=2)

        ttk.Label(prefix_frame, text="前缀:", width=5).pack(side=tk.LEFT)
        prefix_entry = ttk.Entry(
            prefix_frame,
            textvariable=self.tab.name_prefix,
            width=12
        )
        prefix_entry.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

    def create_performance_config(self, parent):
        """创建性能优化配置"""
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        ttk.Label(parent, text="📦 性能优化", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(0, 5))

        ttk.Checkbutton(
            parent,
            text="解析缓存 🆕",
            variable=self.tab.enable_parse_cache
        ).pack(anchor=tk.W, pady=1)

    def create_button_section(self):
        """创建操作按钮区域"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=8)

        # 左侧：执行按钮
        action_frame = ttk.Frame(button_frame)
        action_frame.pack(side=tk.LEFT)

        self.tab.start_button = ttk.Button(
            action_frame,
            text="▶️ 开始混淆",
            command=self.tab.start_obfuscation,
            width=12
        )
        self.tab.start_button.pack(side=tk.LEFT, padx=3)

        self.tab.stop_button = ttk.Button(
            action_frame,
            text="⏹️ 停止",
            command=self.tab.stop_obfuscation,
            state=tk.DISABLED,
            width=10
        )
        self.tab.stop_button.pack(side=tk.LEFT, padx=3)

        # 中间：白名单管理和参数说明
        whitelist_frame = ttk.Frame(button_frame)
        whitelist_frame.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            whitelist_frame,
            text="🛡️ 管理白名单",
            command=self.tab.manage_whitelist,
            width=14
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            whitelist_frame,
            text="❓ 参数说明",
            command=self.tab.show_parameter_help,
            width=12
        ).pack(side=tk.LEFT, padx=3)

        # 右侧：映射管理按钮
        mapping_frame = ttk.Frame(button_frame)
        mapping_frame.pack(side=tk.RIGHT)

        ttk.Button(
            mapping_frame,
            text="📋 查看映射",
            command=self.tab.view_mapping,
            width=12
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            mapping_frame,
            text="💾 导出映射",
            command=self.tab.export_mapping,
            width=12
        ).pack(side=tk.LEFT, padx=3)
