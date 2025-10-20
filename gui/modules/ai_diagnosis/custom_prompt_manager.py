"""
自定义Prompt模板管理器

支持用户自定义AI提示词模板，实现灵活的场景化分析。
例如：语音问题专项分析、网络问题诊断、UI卡顿分析等。

特性：
- CRUD操作：创建、读取、更新、删除自定义模板
- 分类管理：按业务场景分类（语音、网络、性能等）
- 持久化存储：JSON格式存储
- 模板变量：支持动态变量替换
- 启用/禁用：灵活控制模板可见性
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CustomPrompt:
    """自定义Prompt模板数据模型"""

    id: str                    # 唯一标识符
    name: str                  # 模板名称
    category: str              # 分类（自定义分析/崩溃分析/性能诊断等）
    description: str           # 模板描述
    template: str              # Prompt模板内容
    enabled: bool = True       # 是否启用
    created_at: str = ""       # 创建时间
    modified_at: str = ""      # 修改时间
    variables: List[str] = None  # 模板变量列表

    def __post_init__(self):
        """初始化时自动设置时间戳"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = datetime.now().isoformat()
        if self.variables is None:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """
        从模板中提取变量名

        支持格式：{variable_name}

        Returns:
            变量名列表
        """
        import re
        return list(set(re.findall(r'\{(\w+)\}', self.template)))

    def format(self, **kwargs) -> str:
        """
        格式化模板，替换变量

        Args:
            **kwargs: 变量值

        Returns:
            格式化后的prompt

        Example:
            >>> prompt = CustomPrompt(...)
            >>> formatted = prompt.format(module_name="Voice", error_msg="超时")
        """
        return self.template.format(**kwargs)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomPrompt':
        """从字典创建实例"""
        return cls(**data)


class CustomPromptManager:
    """自定义Prompt模板管理器"""

    # 配置文件路径
    CONFIG_FILE = "gui/custom_prompts.json"

    # 内置模板类别
    CATEGORIES = [
        "崩溃分析",
        "性能诊断",
        "问题总结",
        "交互问答",
        "自定义分析"
    ]

    # 内置示例模板
    EXAMPLE_TEMPLATES = [
        {
            "id": "voice_issue_analysis",
            "name": "语音问题专项分析",
            "category": "自定义分析",
            "description": "专门针对语音模块的问题分析，包括录音、播放、编解码等",
            "template": """你是拥有10年以上经验的音频和语音处理专家，精通音频录制、播放、编解码、降噪等技术。

## 任务
分析以下语音模块相关日志，提供详细的诊断报告。

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
识别具体的语音问题类型：
- 录音问题？（权限、硬件、采样率等）
- 播放问题？（解码、缓冲、音频焦点等）
- 编解码问题？（格式不支持、参数错误等）
- 音质问题？（噪音、回声、音量等）
- 延迟问题？（编码延迟、传输延迟、播放延迟等）

### 2. 技术分析
- **音频参数**: 采样率、位深度、声道数
- **编解码器**: 使用的codec及其配置
- **硬件状态**: 麦克风、扬声器状态
- **权限检查**: 录音权限、通知权限
- **资源状态**: 音频焦点、会话管理

### 3. 根因分析
从日志推断问题根源：
- 硬件兼容性问题？
- 权限配置问题？
- 参数配置错误？
- 资源竞争冲突？
- 系统限制问题？

### 4. 解决方案
提供针对性的解决方案：
- **临时方案**：快速缓解问题
- **根治方案**：彻底解决问题
- **代码示例**：具体实现代码
- **参数调优**：最佳参数配置

### 5. 预防措施
- 音频参数校验
- 权限状态检查
- 硬件兼容性测试
- 降级方案设计

## 重要提示
在分析中引用日志时，使用可点击格式：
- 时间戳：[2025-09-21 13:09:49]
- 行号：#123
- 模块：@VoiceModule

用中文回答，Markdown格式，注重实用性。
""",
            "enabled": True
        },
        {
            "id": "network_issue_analysis",
            "name": "网络问题专项分析",
            "category": "自定义分析",
            "description": "专门针对网络请求、连接、超时等问题的分析",
            "template": """你是网络通信专家，精通HTTP/HTTPS、TCP/IP、WebSocket等协议。

## 任务
分析以下网络相关日志，诊断网络问题。

## 网络问题信息
**时间**: {timestamp}
**模块**: {module_name}
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
- 性能问题？（慢请求、重试过多）

### 2. 网络层分析
- **DNS解析**: 域名解析是否成功
- **TCP连接**: 三次握手状态
- **TLS握手**: HTTPS证书验证
- **HTTP请求**: 请求头、Body
- **HTTP响应**: 状态码、响应头

### 3. 根因分析
- 网络环境问题？（弱网、切换）
- 服务端问题？（超时、限流）
- 客户端配置？（超时设置、重试策略）
- 代理/拦截器？（抓包、防火墙）

### 4. 优化建议
- 超时配置优化
- 重试策略调整
- 缓存策略改进
- 降级方案设计

用中文回答，注重网络诊断经验。
""",
            "enabled": True
        }
    ]

    def __init__(self):
        """初始化管理器"""
        self._prompts: Dict[str, CustomPrompt] = {}
        self._load()

    def _get_config_path(self) -> str:
        """获取配置文件绝对路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.dirname(current_dir)
        gui_dir = os.path.dirname(modules_dir)
        project_root = os.path.dirname(gui_dir)
        return os.path.join(project_root, self.CONFIG_FILE)

    def _load(self):
        """从文件加载配置"""
        config_path = self._get_config_path()

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for prompt_data in data.get('custom_prompts', []):
                        prompt = CustomPrompt.from_dict(prompt_data)
                        self._prompts[prompt.id] = prompt
                print(f"✓ 加载了{len(self._prompts)}个自定义Prompt模板")
            except Exception as e:
                print(f"警告: 加载自定义Prompt配置失败: {e}")
                self._prompts = {}
        else:
            # 首次运行，创建示例模板
            print("首次运行，创建示例模板...")
            self._create_example_templates()

    def _save(self):
        """保存配置到文件"""
        config_path = self._get_config_path()

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # 转换为字典列表
            data = {
                'custom_prompts': [p.to_dict() for p in self._prompts.values()]
            }

            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✓ 保存了{len(self._prompts)}个自定义Prompt模板")
            return True
        except Exception as e:
            print(f"错误: 保存自定义Prompt配置失败: {e}")
            return False

    def _create_example_templates(self):
        """创建示例模板"""
        for template_data in self.EXAMPLE_TEMPLATES:
            prompt = CustomPrompt.from_dict(template_data)
            self._prompts[prompt.id] = prompt
        self._save()

    def add(self, prompt: CustomPrompt) -> bool:
        """
        添加自定义Prompt

        Args:
            prompt: CustomPrompt实例

        Returns:
            是否成功
        """
        if prompt.id in self._prompts:
            print(f"错误: Prompt ID '{prompt.id}' 已存在")
            return False

        self._prompts[prompt.id] = prompt
        return self._save()

    def update(self, prompt_id: str, **kwargs) -> bool:
        """
        更新自定义Prompt

        Args:
            prompt_id: Prompt ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        if prompt_id not in self._prompts:
            print(f"错误: Prompt ID '{prompt_id}' 不存在")
            return False

        prompt = self._prompts[prompt_id]

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        # 更新修改时间
        prompt.modified_at = datetime.now().isoformat()

        # 重新提取变量
        if 'template' in kwargs:
            prompt.variables = prompt._extract_variables()

        return self._save()

    def delete(self, prompt_id: str) -> bool:
        """
        删除自定义Prompt

        Args:
            prompt_id: Prompt ID

        Returns:
            是否成功
        """
        if prompt_id not in self._prompts:
            print(f"错误: Prompt ID '{prompt_id}' 不存在")
            return False

        del self._prompts[prompt_id]
        return self._save()

    def get(self, prompt_id: str) -> Optional[CustomPrompt]:
        """
        获取指定的Prompt

        Args:
            prompt_id: Prompt ID

        Returns:
            CustomPrompt实例或None
        """
        return self._prompts.get(prompt_id)

    def list_all(self, category: str = None, enabled_only: bool = False) -> List[CustomPrompt]:
        """
        列出所有Prompt

        Args:
            category: 按分类过滤（可选）
            enabled_only: 仅返回启用的模板

        Returns:
            CustomPrompt列表
        """
        prompts = list(self._prompts.values())

        # 分类过滤
        if category:
            prompts = [p for p in prompts if p.category == category]

        # 启用状态过滤
        if enabled_only:
            prompts = [p for p in prompts if p.enabled]

        # 按创建时间排序（新的在前）
        prompts.sort(key=lambda p: p.created_at, reverse=True)

        return prompts

    def get_by_category(self) -> Dict[str, List[CustomPrompt]]:
        """
        按分类分组返回Prompt

        Returns:
            字典，key为分类，value为该分类下的Prompt列表
        """
        result = {}
        for prompt in self._prompts.values():
            if prompt.category not in result:
                result[prompt.category] = []
            result[prompt.category].append(prompt)

        # 每个分类内部按创建时间排序
        for prompts in result.values():
            prompts.sort(key=lambda p: p.created_at, reverse=True)

        return result

    def enable(self, prompt_id: str) -> bool:
        """启用Prompt"""
        return self.update(prompt_id, enabled=True)

    def disable(self, prompt_id: str) -> bool:
        """禁用Prompt"""
        return self.update(prompt_id, enabled=False)

    def export_to_file(self, filepath: str, prompt_ids: List[str] = None):
        """
        导出Prompt到文件

        Args:
            filepath: 导出文件路径
            prompt_ids: 要导出的Prompt ID列表（None表示全部）
        """
        if prompt_ids is None:
            prompts_to_export = list(self._prompts.values())
        else:
            prompts_to_export = [self._prompts[pid] for pid in prompt_ids if pid in self._prompts]

        data = {
            'custom_prompts': [p.to_dict() for p in prompts_to_export]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ 导出了{len(prompts_to_export)}个Prompt到 {filepath}")

    def import_from_file(self, filepath: str) -> int:
        """
        从文件导入Prompt

        Args:
            filepath: 导入文件路径

        Returns:
            导入的Prompt数量
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for prompt_data in data.get('custom_prompts', []):
            prompt = CustomPrompt.from_dict(prompt_data)

            # 如果ID已存在，生成新ID
            if prompt.id in self._prompts:
                original_id = prompt.id
                counter = 1
                while f"{original_id}_{counter}" in self._prompts:
                    counter += 1
                prompt.id = f"{original_id}_{counter}"
                print(f"  ID冲突，重命名为: {prompt.id}")

            self._prompts[prompt.id] = prompt
            count += 1

        self._save()
        print(f"✓ 导入了{count}个Prompt")
        return count


# 便捷函数
def get_custom_prompt_manager() -> CustomPromptManager:
    """获取全局CustomPromptManager实例（单例）"""
    if not hasattr(get_custom_prompt_manager, '_instance'):
        get_custom_prompt_manager._instance = CustomPromptManager()
    return get_custom_prompt_manager._instance


# 示例用法
if __name__ == "__main__":
    print("=== 自定义Prompt管理器测试 ===\n")

    # 1. 获取管理器
    manager = CustomPromptManager()

    # 2. 列出所有Prompt
    print("1. 所有Prompt:")
    for prompt in manager.list_all():
        print(f"   - {prompt.name} ({prompt.category})")
        print(f"     变量: {prompt.variables}")
        print()

    # 3. 按分类列出
    print("2. 按分类分组:")
    by_category = manager.get_by_category()
    for category, prompts in by_category.items():
        print(f"   {category}: {len(prompts)}个模板")

    # 4. 测试格式化
    print("\n3. 测试模板格式化:")
    voice_prompt = manager.get("voice_issue_analysis")
    if voice_prompt:
        formatted = voice_prompt.format(
            timestamp="2025-10-20 10:00:00",
            module_name="VoiceRecorder",
            issue_type="录音失败",
            logs="[ERROR] 麦克风权限被拒绝"
        )
        print(f"   格式化长度: {len(formatted)}字符")
        print(f"   预览: {formatted[:200]}...")

    # 5. 测试CRUD操作
    print("\n4. 测试CRUD操作:")

    # 创建
    new_prompt = CustomPrompt(
        id="test_prompt",
        name="测试模板",
        category="自定义分析",
        description="这是一个测试模板",
        template="分析这个问题: {problem}"
    )
    manager.add(new_prompt)
    print("   ✓ 创建成功")

    # 读取
    prompt = manager.get("test_prompt")
    print(f"   ✓ 读取成功: {prompt.name}")

    # 更新
    manager.update("test_prompt", description="更新后的描述")
    print("   ✓ 更新成功")

    # 禁用/启用
    manager.disable("test_prompt")
    print("   ✓ 禁用成功")
    manager.enable("test_prompt")
    print("   ✓ 启用成功")

    # 删除
    manager.delete("test_prompt")
    print("   ✓ 删除成功")

    print("\n=== 测试完成 ===")
