# CLAUDE.md - 文档目录

## 模块概述
项目文档中心，包含用户手册、API文档、开发指南等。支持多语言文档，提供完整的项目说明和使用指导。

## 核心文档

### README_CN.md - 中文用户手册
面向中文用户的完整项目说明文档。

#### 主要内容
- **项目简介**: Mars日志框架和xlog格式说明
- **快速开始**: 系统要求、安装步骤、首次使用
- **功能说明**: 解码器、GUI分析器、IPS崩溃分析
- **使用教程**: 基础操作、高级功能、性能优化
- **常见问题**: 故障排除、最佳实践、技术支持

### README_EN.md - 英文用户手册
面向国际用户的英文版项目文档。

#### 内容结构
- **Introduction**: Mars logging framework overview
- **Getting Started**: System requirements, installation guide
- **Features**: Decoders, GUI analyzer, IPS crash analysis
- **Usage Guide**: Basic operations, advanced features
- **Troubleshooting**: Common issues, best practices

## 文档开发

### Markdown最佳实践

#### 结构化内容
```markdown
<!-- 章节标记 -->
<!-- BEGIN: Installation -->
## Installation
...
<!-- END: Installation -->

<!-- 引用管理 -->
[project]: https://github.com/user/project
[issues]: https://github.com/user/project/issues
```

#### 可访问性
- 为图片提供替代文本
- 使用语义化标记
- 重要信息用**粗体**或*斜体*强调

### 文档生成

#### 自动化API文档
```python
# 从代码提取文档字符串
def extract_docstrings(module_path):
    """提取模块中的文档字符串"""
    # 实现代码解析逻辑
    pass

def generate_api_docs():
    """生成API文档"""
    # 实现文档生成逻辑
    pass
```

#### Sphinx支持
```python
# conf.py - Sphinx配置
project = 'Mars Log Analyzer'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme'
]
```

### 文档模板

#### API文档模板
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    函数功能简述。

    Args:
        param1: 参数描述
        param2: 参数描述，默认值为0

    Returns:
        返回值描述

    Raises:
        ValueError: 参数无效时

    Example:
        >>> result = function_name("test", 10)
        >>> print(result['status'])
        'success'
    """
    pass
```

### 版本管理
```markdown
<!-- 版本标记 -->
<!-- Version: 1.0.0 -->
<!-- Last Updated: 2024-01-01 -->

# 文档标题
> 本文档适用于版本 1.0.0
```

## 文档发布

### GitHub Pages自动化
```yaml
# .github/workflows/docs.yml
name: Deploy Docs
on:
  push:
    branches: [main]
    paths: ['docs/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build docs
      run: |
        pip install sphinx sphinx-rtd-theme
        sphinx-build -b html docs docs/_build
    - name: Deploy
      uses: peaceiris/actions-gh-pages@v3
```

### ReadTheDocs配置
```yaml
# .readthedocs.yml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.9"
sphinx:
  configuration: docs/conf.py
```

## 质量保证

### 检查清单
- [x] 拼写检查
- [x] 链接验证
- [x] 代码示例测试
- [x] 格式一致性
- [x] 版本准确性

### 自动化工具
```bash
# 拼写检查
spellchecker -f '**/*.md' -d dictionary.txt

# 链接检查
find . -name "*.md" | xargs -I {} markdown-link-check {}

# 格式检查
markdownlint '**/*.md'
```

## 多语言支持

### 文档结构
```
docs/
├── en/          # 英文文档
├── zh-CN/       # 中文文档
└── locales/     # 翻译文件
    ├── en.json
    └── zh-CN.json
```

### 翻译流程
```python
def translate_markdown(source_file, target_lang):
    """自动翻译Markdown文档"""
    # 实现翻译逻辑
    # 保护代码块
    # 翻译文本内容
    # 恢复代码块
    pass
```

## 维护指南

### 定期更新
1. **每次发布**: 更新版本号和变更日志
2. **每月**: 检查链接有效性
3. **每季度**: 审查文档完整性
4. **每年**: 全面重构和优化

### 贡献流程
```markdown
## 提交规范
- docs: 文档更新
- fix: 修复文档错误
- feat: 新增文档章节

## 写作风格
- 使用主动语态
- 保持简洁明了
- 提供实际例子
- 避免技术术语堆砌
```

### 工具推荐
- **Typora**: Markdown编辑器
- **draw.io**: 架构图绘制
- **Carbon**: 代码截图美化
- **Grammarly**: 英文语法检查

## 未来规划

### 短期目标
- 交互式文档和API playground
- 搜索功能优化
- 视频教程制作

### 长期目标
- 多语言自动翻译
- 用户评论系统
- AI问答助手
- 协作编辑平台

---

*最后更新: 2025-10-21*