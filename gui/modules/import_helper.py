"""
导入辅助模块

提供统一的导入辅助函数，避免重复的三级fallback导入代码。

使用示例:
    >>> from import_helper import import_ai_diagnosis, import_custom_prompt_manager
    >>> AIClientFactory, AIConfig = import_ai_diagnosis()
    >>> manager = import_custom_prompt_manager()
"""

import sys
import os


def _add_gui_path():
    """添加gui目录到Python路径（如果需要）"""
    # 获取gui目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gui_dir = os.path.dirname(current_dir)

    if gui_dir not in sys.path:
        sys.path.insert(0, gui_dir)


def import_ai_diagnosis():
    """
    导入AI诊断核心模块

    Returns:
        tuple: (AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer)

    Raises:
        ImportError: 如果无法导入模块
    """
    try:
        from ai_diagnosis import AIClientFactory, AIConfig
        from ai_diagnosis.log_preprocessor import LogPreprocessor
        from ai_diagnosis.prompt_templates import PromptTemplates
        from ai_diagnosis.token_optimizer import TokenOptimizer
        return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer
    except ImportError:
        try:
            from modules.ai_diagnosis import AIClientFactory, AIConfig
            from modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from modules.ai_diagnosis.prompt_templates import PromptTemplates
            from modules.ai_diagnosis.token_optimizer import TokenOptimizer
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer
        except ImportError:
            from gui.modules.ai_diagnosis import AIClientFactory, AIConfig
            from gui.modules.ai_diagnosis.log_preprocessor import LogPreprocessor
            from gui.modules.ai_diagnosis.prompt_templates import PromptTemplates
            from gui.modules.ai_diagnosis.token_optimizer import TokenOptimizer
            return AIClientFactory, AIConfig, LogPreprocessor, PromptTemplates, TokenOptimizer


def import_custom_prompt_manager():
    """
    导入自定义Prompt管理器

    Returns:
        function: get_custom_prompt_manager函数

    Raises:
        ImportError: 如果无法导入模块
    """
    try:
        from .ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
        return get_custom_prompt_manager
    except ImportError:
        try:
            from ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            return get_custom_prompt_manager
        except ImportError:
            _add_gui_path()
            from modules.ai_diagnosis.custom_prompt_manager import get_custom_prompt_manager
            return get_custom_prompt_manager


def import_custom_prompt_class():
    """
    导入CustomPrompt类

    Returns:
        class: CustomPrompt类

    Raises:
        ImportError: 如果无法导入
    """
    try:
        from .ai_diagnosis.custom_prompt_manager import CustomPrompt
        return CustomPrompt
    except ImportError:
        try:
            from ai_diagnosis.custom_prompt_manager import CustomPrompt
            return CustomPrompt
        except ImportError:
            _add_gui_path()
            from modules.ai_diagnosis.custom_prompt_manager import CustomPrompt
            return CustomPrompt


def import_ai_settings_dialog():
    """
    导入AI设置对话框

    Returns:
        class: AISettingsDialog类

    Raises:
        ImportError: 如果无法导入
    """
    try:
        from ai_diagnosis_settings import AISettingsDialog
        return AISettingsDialog
    except ImportError:
        try:
            from modules.ai_diagnosis_settings import AISettingsDialog
            return AISettingsDialog
        except ImportError:
            from gui.modules.ai_diagnosis_settings import AISettingsDialog
            return AISettingsDialog


def import_custom_prompt_dialog():
    """
    导入自定义Prompt对话框

    Returns:
        function: show_custom_prompt_dialog函数

    Raises:
        ImportError: 如果无法导入
    """
    try:
        from .custom_prompt_dialog import show_custom_prompt_dialog
        return show_custom_prompt_dialog
    except ImportError:
        try:
            from custom_prompt_dialog import show_custom_prompt_dialog
            return show_custom_prompt_dialog
        except ImportError:
            try:
                from modules.custom_prompt_dialog import show_custom_prompt_dialog
                return show_custom_prompt_dialog
            except ImportError:
                _add_gui_path()
                from modules.custom_prompt_dialog import show_custom_prompt_dialog
                return show_custom_prompt_dialog


def import_custom_prompt_selector():
    """
    导入自定义Prompt选择器

    Returns:
        function: create_prompt_selector函数

    Raises:
        ImportError: 如果无法导入
    """
    try:
        from .custom_prompt_selector import create_prompt_selector
        return create_prompt_selector
    except ImportError:
        try:
            from custom_prompt_selector import create_prompt_selector
            return create_prompt_selector
        except ImportError:
            try:
                from modules.custom_prompt_selector import create_prompt_selector
                return create_prompt_selector
            except ImportError:
                _add_gui_path()
                from modules.custom_prompt_selector import create_prompt_selector
                return create_prompt_selector
