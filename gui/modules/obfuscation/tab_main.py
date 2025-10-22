"""
iOS代码混淆标签页主控制器（重构版）

整合UI组件和业务逻辑，提供完整的混淆功能。
"""

import os
import tkinter as tk
from tkinter import ttk

from .ui.config_panel import ConfigPanel
from .ui.progress_panel import ProgressPanel
from .ui.mapping_panel import MappingViewer, MappingExporter


class ObfuscationTab(ttk.Frame):
    """iOS代码混淆标签页（重构版）"""

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

        # 创建UI
        self.create_widgets()

    def create_widgets(self):
        """创建主UI结构"""
        # 顶部信息栏
        self.create_header()

        # 创建主容器（使用PanedWindow实现上下分割）
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 上半部分：配置区域 ===
        config_frame = ttk.Frame(paned)
        paned.add(config_frame, weight=1)

        # 使用ConfigPanel组件
        self.config_panel = ConfigPanel(config_frame, self)
        self.config_panel.pack(fill=tk.BOTH, expand=True)

        # === 下半部分：日志和进度 ===
        log_frame = ttk.Frame(paned)
        paned.add(log_frame, weight=2)

        # 使用ProgressPanel组件
        self.progress_panel = ProgressPanel(log_frame, self)
        self.progress_panel.pack(fill=tk.BOTH, expand=True)

    def create_header(self):
        """创建标题区域"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # 标题
        title_label = ttk.Label(
            header_frame,
            text="🔐 iOS代码混淆工具",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor=tk.W)

        # 说明文本
        desc_text = "应对App Store审核(4.3/2.1)，支持ObjC/Swift符号混淆，智能保护系统API和第三方库"
        desc_label = ttk.Label(
            header_frame,
            text=desc_text,
            font=("Arial", 9),
            foreground="gray"
        )
        desc_label.pack(anchor=tk.W, pady=(2, 0))

    # ==================== 事件处理方法 ====================
    # 这些方法将被ConfigPanel和其他组件调用

    def load_template(self, template_name):
        """
        加载配置模板

        Args:
            template_name: 模板名称 (minimal/standard/aggressive)
        """
        try:
            from ..obfuscation_templates import get_template
        except ImportError:
            from modules.obfuscation_templates import get_template

        template = get_template(template_name)
        if not template:
            self.progress_panel.log(f"❌ 模板 '{template_name}' 不存在", "error")
            return

        # 应用模板配置到UI
        self.obfuscate_classes.set(template.get('obfuscate_classes', True))
        self.obfuscate_methods.set(template.get('obfuscate_methods', True))
        self.obfuscate_properties.set(template.get('obfuscate_properties', True))
        self.obfuscate_protocols.set(template.get('obfuscate_protocols', True))

        self.modify_resources.set(template.get('modify_resources', False))
        self.modify_images.set(template.get('modify_images', False))
        self.modify_audio.set(template.get('modify_audio', False))
        self.modify_fonts.set(template.get('modify_fonts', False))

        self.insert_garbage_code.set(template.get('insert_garbage_code', False))
        self.string_encryption.set(template.get('string_encryption', False))

        # 高级配置
        if 'garbage_count' in template:
            self.garbage_count.set(template['garbage_count'])
        if 'garbage_complexity' in template:
            self.garbage_complexity.set(template['garbage_complexity'])
        if 'encryption_algorithm' in template:
            self.encryption_algorithm.set(template['encryption_algorithm'])

        self.progress_panel.log(f"✅ 已加载 '{template_name}' 模板配置", "success")

    def select_project(self):
        """选择项目目录"""
        from tkinter import filedialog

        directory = filedialog.askdirectory(
            title="选择iOS项目目录",
            initialdir=self.project_path or "."
        )

        if directory:
            self.project_path = directory
            self.project_path_var.set(directory)
            self.progress_panel.log(f"📁 已选择项目: {directory}", "info")

    def select_output(self):
        """选择输出目录"""
        from tkinter import filedialog

        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_path or "."
        )

        if directory:
            self.output_path = directory
            self.output_path_var.set(directory)
            self.progress_panel.log(f"📁 已选择输出目录: {directory}", "info")

    def start_obfuscation(self):
        """开始混淆（主入口）"""
        from tkinter import messagebox
        import threading

        # 验证输入
        if not self.project_path_var.get():
            messagebox.showwarning("警告", "请选择源项目目录")
            return

        if not self.output_path_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return

        # 清空日志
        self.progress_panel.clear()
        self.progress_panel.log("=" * 60, "header")
        self.progress_panel.log("🚀 开始iOS代码混淆", "header")
        self.progress_panel.log("=" * 60, "header")

        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True

        # 在后台线程中执行混淆
        thread = threading.Thread(target=self._run_obfuscation, daemon=True)
        thread.start()

    def _run_obfuscation(self):
        """执行混淆（异步执行）"""
        try:
            # 导入混淆引擎（兼容不同导入路径）
            try:
                from .obfuscation_engine import ObfuscationEngine
                from .config_manager import ConfigManager
                from ..exceptions import ObfuscationError
            except ImportError:
                from modules.obfuscation.obfuscation_engine import ObfuscationEngine
                from modules.obfuscation.config_manager import ConfigManager
                from modules.exceptions import ObfuscationError

            # 收集配置
            config = {
                'project_path': self.project_path_var.get(),
                'output_path': self.output_path_var.get(),
                'obfuscate_classes': self.obfuscate_classes.get(),
                'obfuscate_methods': self.obfuscate_methods.get(),
                'obfuscate_properties': self.obfuscate_properties.get(),
                'obfuscate_protocols': self.obfuscate_protocols.get(),
                'modify_resources': self.modify_resources.get(),
                'modify_images': self.modify_images.get(),
                'modify_audio': self.modify_audio.get(),
                'modify_fonts': self.modify_fonts.get(),
                'auto_add_to_xcode': self.auto_add_to_xcode.get(),
                'auto_detect_third_party': self.auto_detect_third_party.get(),
                'use_fixed_seed': self.use_fixed_seed.get(),
                'insert_garbage_code': self.insert_garbage_code.get(),
                'string_encryption': self.string_encryption.get(),
                'enable_call_relationships': self.enable_call_relationships.get(),
                'enable_parse_cache': self.enable_parse_cache.get(),
                'garbage_count': self.garbage_count.get(),
                'garbage_complexity': self.garbage_complexity.get(),
                'call_density': self.call_density.get(),
                'encryption_algorithm': self.encryption_algorithm.get(),
                'string_min_length': self.string_min_length.get(),
                'naming_strategy': self.naming_strategy.get(),
                'name_prefix': self.name_prefix.get(),
                'image_intensity': self.image_intensity.get(),
            }

            self.progress_panel.log("\n📋 配置信息:", "info")
            self.progress_panel.log(f"  源项目: {config['project_path']}", "info")
            self.progress_panel.log(f"  输出目录: {config['output_path']}", "info")
            self.progress_panel.log(f"  命名策略: {config['naming_strategy']}", "info")
            self.progress_panel.log(f"  名称前缀: {config['name_prefix']}\n", "info")

            # 初始化配置管理器
            self.config_manager = ConfigManager()
            self.config_manager.load_from_dict(config)

            # 初始化混淆引擎
            self.progress_panel.log("🔧 初始化混淆引擎...", "info")
            self.obfuscation_engine = ObfuscationEngine(self.config_manager)

            # 执行混淆
            self.progress_panel.log("⚙️  开始执行混淆...\n", "info")

            def progress_callback(progress, message):
                """进度回调"""
                self.update_progress(progress, message)

            results = self.obfuscation_engine.run(progress_callback=progress_callback)

            # 显示结果
            if results.get('success'):
                self.progress_panel.log("\n" + "=" * 60, "header")
                self.progress_panel.log("✅ 混淆完成！", "success")
                self.progress_panel.log("=" * 60, "header")
                self.progress_panel.log(f"\n📊 统计信息:", "info")
                self.progress_panel.log(f"  混淆类: {results.get('obfuscated_classes', 0)}", "info")
                self.progress_panel.log(f"  混淆方法: {results.get('obfuscated_methods', 0)}", "info")
                self.progress_panel.log(f"  混淆属性: {results.get('obfuscated_properties', 0)}", "info")
                self.progress_panel.log(f"  处理文件: {results.get('processed_files', 0)}", "info")

                if results.get('mapping_file'):
                    self.progress_panel.log(f"\n💾 映射文件: {results['mapping_file']}", "success")
            else:
                self.progress_panel.log("\n❌ 混淆失败", "error")
                if results.get('error'):
                    self.progress_panel.log(f"  错误: {results['error']}", "error")

        except ObfuscationError as e:
            self.progress_panel.log(f"\n❌ 混淆错误: {str(e)}", "error")

        except Exception as e:
            self.progress_panel.log(f"\n❌ 未知错误: {str(e)}", "error")
            import traceback
            self.progress_panel.log(f"\n{traceback.format_exc()}", "error")

        finally:
            # 恢复按钮状态
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def stop_obfuscation(self):
        """停止混淆"""
        if self.is_running and self.obfuscation_engine:
            self.progress_panel.log("\n⏹️  正在停止混淆...", "warning")
            self.obfuscation_engine.stop()
            self.is_running = False

    def view_mapping(self):
        """查看映射表"""
        try:
            from ..exceptions import FileOperationError, UIError, handle_exceptions
        except ImportError:
            from modules.exceptions import FileOperationError, UIError, handle_exceptions

        if not self.output_path:
            raise UIError(
                message="未设置输出路径",
                widget="查看映射按钮",
                action="查看混淆映射",
                user_message="请先执行混淆生成映射文件"
            )

        mapping_file = os.path.join(self.output_path, "obfuscation_mapping.json")

        try:
            viewer = MappingViewer(self, mapping_file)
            viewer.show()
        except (FileOperationError, UIError) as e:
            self.progress_panel.log(f"❌ {e.user_message}", "error")
        except Exception as e:
            self.progress_panel.log(f"❌ 查看映射失败: {str(e)}", "error")

    def export_mapping(self):
        """导出映射"""
        try:
            from ..exceptions import FileOperationError, UIError
        except ImportError:
            from modules.exceptions import FileOperationError, UIError

        if not self.output_path:
            raise UIError(
                message="未设置输出路径",
                widget="导出映射按钮",
                action="导出混淆映射",
                user_message="请先执行混淆生成映射文件"
            )

        mapping_file = os.path.join(self.output_path, "obfuscation_mapping.json")

        try:
            exporter = MappingExporter(self, mapping_file)
            exporter.export()
        except (FileOperationError, UIError) as e:
            self.progress_panel.log(f"❌ {e.user_message}", "error")
        except Exception as e:
            self.progress_panel.log(f"❌ 导出映射失败: {str(e)}", "error")

    def manage_whitelist(self):
        """管理符号白名单"""
        from .ui.whitelist_panel import WhitelistManager
        manager = WhitelistManager(self, self)
        manager.manage_symbol_whitelist()

    def manage_string_whitelist(self):
        """管理字符串白名单"""
        from .ui.whitelist_panel import WhitelistManager
        manager = WhitelistManager(self, self)
        manager.manage_string_whitelist()

    def show_parameter_help(self):
        """显示参数帮助"""
        from .ui.help_dialog import ParameterHelpDialog
        dialog = ParameterHelpDialog(self)
        dialog.show()

    def update_progress(self, progress, message):
        """
        更新进度（线程安全）

        Args:
            progress: 进度值(0-100)
            message: 状态消息
        """
        # 使用after确保在主线程中更新UI
        self.after(0, lambda: self.progress_panel.update_progress(progress, message))
        if message:
            self.after(0, lambda: self.progress_panel.log(f"  {message}", "info"))

    def log(self, message):
        """
        添加日志（线程安全）

        Args:
            message: 日志消息
        """
        self.after(0, lambda: self.progress_panel.log(message))
