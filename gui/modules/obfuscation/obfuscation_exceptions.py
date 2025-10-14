"""
混淆异常类型 - 定义混淆过程中的各类异常

支持:
1. 基础异常类型（ObfuscationError）
2. 配置错误（ConfigurationError）
3. 解析错误（ParseError）
4. 转换错误（TransformError）
5. 资源处理错误（ResourceError）
6. 名称冲突错误（NameConflictError）
7. 白名单错误（WhitelistError）
8. 文件IO错误（FileIOError）
"""

from typing import Optional


class ObfuscationError(Exception):
    """
    混淆基础异常

    所有混淆相关异常的基类
    """

    def __init__(self, message: str, details: Optional[str] = None):
        """
        初始化基础异常

        Args:
            message: 错误消息
            details: 详细错误信息（可选）
        """
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.details:
            return f"{self.message}\n详情: {self.details}"
        return self.message


class ConfigurationError(ObfuscationError):
    """
    配置错误

    当配置文件无效或配置参数不正确时抛出
    """

    def __init__(self, message: str, config_key: Optional[str] = None,
                 expected_value: Optional[str] = None, actual_value: Optional[str] = None):
        """
        初始化配置错误

        Args:
            message: 错误消息
            config_key: 配置项名称
            expected_value: 期望值
            actual_value: 实际值
        """
        self.config_key = config_key
        self.expected_value = expected_value
        self.actual_value = actual_value

        details = []
        if config_key:
            details.append(f"配置项: {config_key}")
        if expected_value:
            details.append(f"期望值: {expected_value}")
        if actual_value:
            details.append(f"实际值: {actual_value}")

        super().__init__(message, ", ".join(details) if details else None)


class ParseError(ObfuscationError):
    """
    解析错误

    当代码解析失败时抛出
    """

    def __init__(self, file_path: str, line_number: int, message: str,
                 code_snippet: Optional[str] = None):
        """
        初始化解析错误

        Args:
            file_path: 文件路径
            line_number: 行号
            message: 错误消息
            code_snippet: 代码片段（可选）
        """
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet

        location = f"{file_path}:{line_number}"
        details = f"位置: {location}"
        if code_snippet:
            details += f"\n代码: {code_snippet}"

        super().__init__(f"解析错误: {message}", details)


class TransformError(ObfuscationError):
    """
    转换错误

    当代码转换过程中出现错误时抛出
    """

    def __init__(self, file_path: str, message: str,
                 symbol_name: Optional[str] = None,
                 operation: Optional[str] = None):
        """
        初始化转换错误

        Args:
            file_path: 文件路径
            message: 错误消息
            symbol_name: 符号名称（可选）
            operation: 操作类型（可选）
        """
        self.file_path = file_path
        self.symbol_name = symbol_name
        self.operation = operation

        details = [f"文件: {file_path}"]
        if symbol_name:
            details.append(f"符号: {symbol_name}")
        if operation:
            details.append(f"操作: {operation}")

        super().__init__(f"转换错误: {message}", ", ".join(details))


class ResourceError(ObfuscationError):
    """
    资源处理错误

    当处理XIB、Storyboard等资源文件时出错
    """

    def __init__(self, resource_path: str, resource_type: str, message: str):
        """
        初始化资源错误

        Args:
            resource_path: 资源文件路径
            resource_type: 资源类型（xib/storyboard/assets等）
            message: 错误消息
        """
        self.resource_path = resource_path
        self.resource_type = resource_type

        details = f"资源: {resource_path}, 类型: {resource_type}"
        super().__init__(f"资源处理错误: {message}", details)


class NameConflictError(ObfuscationError):
    """
    名称冲突错误

    当生成的混淆名称与已有名称冲突时抛出
    """

    def __init__(self, original_name: str, obfuscated_name: str,
                 existing_original: str):
        """
        初始化名称冲突错误

        Args:
            original_name: 当前符号的原始名称
            obfuscated_name: 冲突的混淆名称
            existing_original: 已存在的符号原始名称
        """
        self.original_name = original_name
        self.obfuscated_name = obfuscated_name
        self.existing_original = existing_original

        message = f"名称冲突: {original_name} 和 {existing_original} 都映射到 {obfuscated_name}"
        details = (f"当前符号: {original_name}, "
                  f"混淆名: {obfuscated_name}, "
                  f"已存在符号: {existing_original}")

        super().__init__(message, details)


class WhitelistError(ObfuscationError):
    """
    白名单错误

    当白名单加载或处理出错时抛出
    """

    def __init__(self, message: str, whitelist_type: Optional[str] = None):
        """
        初始化白名单错误

        Args:
            message: 错误消息
            whitelist_type: 白名单类型（system/third_party/custom等）
        """
        self.whitelist_type = whitelist_type

        details = f"白名单类型: {whitelist_type}" if whitelist_type else None
        super().__init__(f"白名单错误: {message}", details)


class FileIOError(ObfuscationError):
    """
    文件IO错误

    当文件读写操作失败时抛出
    """

    def __init__(self, file_path: str, operation: str, message: str):
        """
        初始化文件IO错误

        Args:
            file_path: 文件路径
            operation: 操作类型（read/write/delete等）
            message: 错误消息
        """
        self.file_path = file_path
        self.operation = operation

        details = f"文件: {file_path}, 操作: {operation}"
        super().__init__(f"文件IO错误: {message}", details)


class ProjectAnalysisError(ObfuscationError):
    """
    项目分析错误

    当项目结构分析失败时抛出
    """

    def __init__(self, project_path: str, message: str):
        """
        初始化项目分析错误

        Args:
            project_path: 项目路径
            message: 错误消息
        """
        self.project_path = project_path

        details = f"项目路径: {project_path}"
        super().__init__(f"项目分析错误: {message}", details)


# 异常处理辅助函数

def handle_obfuscation_error(error: Exception) -> str:
    """
    统一处理混淆异常，返回格式化的错误消息

    Args:
        error: 异常对象

    Returns:
        str: 格式化的错误消息
    """
    if isinstance(error, ConfigurationError):
        return f"❌ 配置错误: {error.message}"

    elif isinstance(error, ParseError):
        return f"❌ 解析错误: {error.file_path}:{error.line_number} - {error.message}"

    elif isinstance(error, TransformError):
        return f"❌ 转换错误: {error.file_path} - {error.message}"

    elif isinstance(error, ResourceError):
        return f"❌ 资源错误: {error.resource_type} {error.resource_path} - {error.message}"

    elif isinstance(error, NameConflictError):
        return (f"❌ 名称冲突: {error.original_name} 和 {error.existing_original} "
                f"都映射到 {error.obfuscated_name}")

    elif isinstance(error, WhitelistError):
        return f"❌ 白名单错误: {error.message}"

    elif isinstance(error, FileIOError):
        return f"❌ 文件错误: {error.operation} {error.file_path} - {error.message}"

    elif isinstance(error, ProjectAnalysisError):
        return f"❌ 项目分析错误: {error.project_path} - {error.message}"

    elif isinstance(error, ObfuscationError):
        return f"❌ 混淆错误: {error.message}"

    else:
        return f"❌ 未知错误: {str(error)}"


def get_error_suggestions(error: Exception) -> str:
    """
    根据异常类型提供修复建议

    Args:
        error: 异常对象

    Returns:
        str: 修复建议
    """
    if isinstance(error, ConfigurationError):
        return """
修复建议:
1. 检查配置文件格式是否正确
2. 验证配置项的值是否在有效范围内
3. 参考配置模板示例
4. 使用配置验证工具检查
"""

    elif isinstance(error, ParseError):
        return """
修复建议:
1. 检查代码语法是否正确
2. 确认文件编码是否为UTF-8
3. 查看是否有不支持的语言特性
4. 尝试简化复杂的代码结构
"""

    elif isinstance(error, TransformError):
        return """
修复建议:
1. 检查符号名称是否合法
2. 确认没有使用保留关键字
3. 验证代码格式是否标准
4. 尝试增量混淆模式
"""

    elif isinstance(error, ResourceError):
        return """
修复建议:
1. 确认资源文件格式是否正确
2. 检查XML结构是否完整
3. 验证文件权限是否足够
4. 尝试使用Xcode重新保存资源文件
"""

    elif isinstance(error, NameConflictError):
        return """
修复建议:
1. 使用更长的混淆名称长度
2. 增加名称前缀的多样性
3. 检查是否使用了固定种子
4. 考虑调整命名策略
"""

    elif isinstance(error, FileIOError):
        return """
修复建议:
1. 检查文件路径是否正确
2. 确认文件权限是否足够
3. 验证磁盘空间是否充足
4. 关闭可能占用文件的程序
"""

    else:
        return """
修复建议:
1. 查看完整的错误信息和堆栈跟踪
2. 检查日志文件获取更多细节
3. 尝试使用更详细的输出模式
4. 联系技术支持获取帮助
"""


# 异常装饰器

def handle_parse_errors(func):
    """解析错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, ParseError):
                # 将普通异常转换为ParseError
                file_path = kwargs.get('file_path', args[1] if len(args) > 1 else 'unknown')
                raise ParseError(file_path, 0, str(e)) from e
            raise
    return wrapper


def handle_transform_errors(func):
    """转换错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, TransformError):
                # 将普通异常转换为TransformError
                file_path = kwargs.get('file_path', args[1] if len(args) > 1 else 'unknown')
                raise TransformError(file_path, str(e)) from e
            raise
    return wrapper


if __name__ == "__main__":
    # 测试异常类型
    print("=== 混淆异常类型测试 ===\n")

    # 测试1: ConfigurationError
    print("1. ConfigurationError:")
    try:
        raise ConfigurationError(
            "配置项无效",
            config_key="name_prefix",
            expected_value="字符串",
            actual_value="123"
        )
    except ObfuscationError as e:
        print(f"   {handle_obfuscation_error(e)}")
        print(f"   建议: {get_error_suggestions(e)[:50]}...")

    # 测试2: ParseError
    print("\n2. ParseError:")
    try:
        raise ParseError(
            "/path/to/file.m",
            42,
            "无法解析方法声明",
            code_snippet="- (void)methodName {"
        )
    except ObfuscationError as e:
        print(f"   {handle_obfuscation_error(e)}")

    # 测试3: TransformError
    print("\n3. TransformError:")
    try:
        raise TransformError(
            "/path/to/file.m",
            "符号替换失败",
            symbol_name="MyClass",
            operation="class_name_replacement"
        )
    except ObfuscationError as e:
        print(f"   {handle_obfuscation_error(e)}")

    # 测试4: NameConflictError
    print("\n4. NameConflictError:")
    try:
        raise NameConflictError(
            "MyViewController",
            "Abc123",
            "UserManager"
        )
    except ObfuscationError as e:
        print(f"   {handle_obfuscation_error(e)}")

    # 测试5: ResourceError
    print("\n5. ResourceError:")
    try:
        raise ResourceError(
            "/path/to/Main.storyboard",
            "storyboard",
            "XML解析失败"
        )
    except ObfuscationError as e:
        print(f"   {handle_obfuscation_error(e)}")

    print("\n=== 测试完成 ===")
