"""
iOS混淆工具 - 配置模板

定义预设的混淆配置模板（最小化、标准、激进），
从obfuscation_tab.py中提取以减少主文件大小。
"""

# 配置模板定义
OBFUSCATION_TEMPLATES = {
    "minimal": {
        "name": "最小化",
        "description": "仅混淆类名和方法名，适合快速测试",
        "class_names": True,
        "method_names": True,
        "property_names": False,
        "protocol_names": False,
        "resources": False,
        "images": False,
        "audio": False,
        "fonts": False,
        "auto_detect": True,
        "fixed_seed": False
    },
    "standard": {
        "name": "标准",
        "description": "平衡的混淆策略，适合日常开发",
        "class_names": True,
        "method_names": True,
        "property_names": True,
        "protocol_names": True,
        "resources": False,
        "images": False,
        "audio": False,
        "fonts": False,
        "auto_detect": True,
        "fixed_seed": False
    },
    "aggressive": {
        "name": "激进",
        "description": "最强混淆力度，适合正式发布",
        "class_names": True,
        "method_names": True,
        "property_names": True,
        "protocol_names": True,
        "resources": True,
        "images": True,
        "audio": True,
        "fonts": True,
        "auto_detect": True,
        "fixed_seed": False
    }
}


def get_template(template_name):
    """
    获取配置模板

    Args:
        template_name: 模板名称 (minimal/standard/aggressive)

    Returns:
        dict: 配置字典，如果模板不存在返回None
    """
    return OBFUSCATION_TEMPLATES.get(template_name)


def list_templates():
    """
    列出所有可用的模板名称

    Returns:
        list: 模板名称列表
    """
    return list(OBFUSCATION_TEMPLATES.keys())


def get_template_info(template_name):
    """
    获取模板的详细信息

    Args:
        template_name: 模板名称

    Returns:
        dict: 包含name和description的字典
    """
    template = get_template(template_name)
    if template:
        return {
            "name": template["name"],
            "description": template["description"]
        }
    return None
