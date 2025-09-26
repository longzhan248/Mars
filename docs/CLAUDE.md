# CLAUDE.md - 文档目录技术指南

## 模块概述
项目文档中心，包含用户手册、API文档、开发指南等。支持多语言文档，提供完整的项目说明和使用指导。

## 文档结构

### README_CN.md
中文版项目说明文档，面向中文用户。

#### 文档大纲
```markdown
1. 项目简介
   - Mars日志框架介绍
   - xlog格式说明
   - 工具套件功能

2. 快速开始
   - 系统要求
   - 安装步骤
   - 首次使用

3. 功能说明
   - 解码器功能
   - GUI分析器
   - IPS崩溃分析

4. 使用教程
   - 基础操作
   - 高级功能
   - 性能优化

5. 常见问题
   - 故障排除
   - 最佳实践
   - 技术支持
```

#### 内容规范

##### 标题层级
```markdown
# 一级标题 - 主要章节
## 二级标题 - 子章节
### 三级标题 - 具体功能
#### 四级标题 - 详细说明
```

##### 代码示例
```markdown
\`\`\`bash
# Shell命令
./scripts/run_analyzer.sh
\`\`\`

\`\`\`python
# Python代码
parser = IPSParser()
parser.parse_file("crash.ips")
\`\`\`
```

##### 表格格式
```markdown
| 功能 | 描述 | 状态 |
|-----|------|------|
| 解码 | xlog文件解码 | ✅ |
| 分析 | 日志统计分析 | ✅ |
| 导出 | 多格式导出 | ✅ |
```

##### 图片引用
```markdown
![架构图](images/architecture.png)
![界面截图](images/screenshot.png)
```

#### 本地化考虑

##### 术语统一
```python
TERMS_CN = {
    'decoder': '解码器',
    'parser': '解析器',
    'analyzer': '分析器',
    'crash': '崩溃',
    'log': '日志',
    'symbolicate': '符号化'
}
```

##### 文化适应
- 使用本地化的例子
- 考虑阅读习惯
- 适应技术背景

### README_EN.md
英文版项目说明文档，面向国际用户。

#### Documentation Outline
```markdown
1. Introduction
   - About Mars logging framework
   - xlog format specification
   - Tool suite overview

2. Getting Started
   - System requirements
   - Installation guide
   - Quick start tutorial

3. Features
   - Decoders
   - GUI analyzer
   - IPS crash analysis

4. Usage Guide
   - Basic operations
   - Advanced features
   - Performance tuning

5. Troubleshooting
   - Common issues
   - Best practices
   - Support channels
```

#### Writing Guidelines

##### Language Style
- Clear and concise
- Active voice preferred
- Technical accuracy
- Consistent terminology

##### Code Examples
```python
# Well-commented code
def decode_xlog(file_path):
    """
    Decode Mars xlog file.

    Args:
        file_path: Path to xlog file

    Returns:
        Decoded log content
    """
    pass
```

##### Version Notes
```markdown
> **Note:** Requires Python 3.6 or later
> **Warning:** Large files may require additional memory
> **Tip:** Use fast_decoder for files over 10MB
```

## 文档开发指南

### Markdown最佳实践

#### 结构化内容
```markdown
<!-- 使用注释标记章节 -->
<!-- BEGIN: Installation -->
## Installation
...
<!-- END: Installation -->
```

#### 可维护性
```markdown
<!-- 使用变量减少重复 -->
[project-repo]: https://github.com/user/project
[issues]: https://github.com/user/project/issues

See [our repository][project-repo] for code.
Report bugs at [issues page][issues].
```

#### 可访问性
```markdown
<!-- 为图片提供替代文本 -->
![GUI界面展示了日志分析的主要功能](images/gui.png)

<!-- 使用语义化标记 -->
**重要:** 请先备份数据
*注意:* 此功能需要管理员权限
```

### 文档生成

#### 从代码生成文档
```python
# generate_docs.py
import ast
import inspect

def extract_docstrings(module_path):
    """提取模块中的文档字符串"""
    with open(module_path, 'r') as f:
        tree = ast.parse(f.read())

    docs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docs[node.name] = ast.get_docstring(node)

    return docs

def generate_api_docs():
    """生成API文档"""
    modules = [
        'decoders/decode_mars_nocrypt_log_file_py3.py',
        'tools/ips_parser.py'
    ]

    for module in modules:
        docs = extract_docstrings(module)
        # 生成Markdown文档
        generate_markdown(docs)
```

#### 使用Sphinx
```python
# conf.py - Sphinx配置
project = 'Mars Log Analyzer'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme'
]

html_theme = 'sphinx_rtd_theme'
```

```bash
# 生成HTML文档
sphinx-build -b html source build/html

# 生成PDF文档
sphinx-build -b latex source build/latex
make -C build/latex
```

### 文档模板

#### 功能文档模板
```markdown
# 功能名称

## 概述
简要说明功能作用和应用场景。

## 前置条件
- 条件1
- 条件2

## 使用步骤
1. 第一步
2. 第二步
3. 第三步

## 参数说明
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| param1 | string | 是 | 参数描述 |

## 示例
\`\`\`python
# 代码示例
\`\`\`

## 注意事项
- 注意点1
- 注意点2

## 相关链接
- [相关功能1]()
- [相关功能2]()
```

#### API文档模板
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    简短描述函数功能。

    详细说明函数的作用、算法或实现细节。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述，默认值为0

    Returns:
        返回值的描述，包括数据结构

        Example:
            {
                'status': 'success',
                'data': [...]
            }

    Raises:
        ValueError: 当参数无效时
        IOError: 当文件操作失败时

    Example:
        >>> result = function_name("test", 10)
        >>> print(result['status'])
        'success'

    Note:
        特别注意事项或限制

    Since: v1.0.0
    """
    pass
```

### 文档版本管理

#### 版本标记
```markdown
<!-- Version: 1.0.0 -->
<!-- Last Updated: 2024-01-01 -->
<!-- Author: Team -->

# 文档标题

> 本文档适用于版本 1.0.0
```

#### 变更日志
```markdown
# CHANGELOG

## [1.0.0] - 2024-01-01
### Added
- 初始版本发布
- 基础功能文档

### Changed
- 更新安装说明

### Fixed
- 修复文档错误

### Deprecated
- 旧版API标记为废弃
```

### 多语言支持

#### i18n结构
```
docs/
├── en/
│   ├── README.md
│   ├── user-guide.md
│   └── api-reference.md
├── zh-CN/
│   ├── README.md
│   ├── user-guide.md
│   └── api-reference.md
└── locales/
    ├── en.json
    └── zh-CN.json
```

#### 翻译工作流
```python
# translate.py
from googletrans import Translator

def translate_markdown(source_file, target_lang):
    """自动翻译Markdown文档"""
    translator = Translator()

    with open(source_file, 'r') as f:
        content = f.read()

    # 保护代码块
    code_blocks = extract_code_blocks(content)

    # 翻译文本
    translated = translator.translate(
        content,
        dest=target_lang
    ).text

    # 恢复代码块
    final_content = restore_code_blocks(
        translated,
        code_blocks
    )

    return final_content
```

## 文档发布

### GitHub Pages
```yaml
# .github/workflows/docs.yml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Build docs
      run: |
        pip install sphinx sphinx-rtd-theme
        sphinx-build -b html docs docs/_build

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs/_build
```

### ReadTheDocs
```yaml
# .readthedocs.yml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.9"

sphinx:
  configuration: docs/conf.py

python:
  install:
    - requirements: docs/requirements.txt
```

## 文档质量保证

### 检查清单
- [ ] 拼写检查
- [ ] 链接验证
- [ ] 代码示例测试
- [ ] 格式一致性
- [ ] 版本准确性

### 自动化检查
```bash
# 拼写检查
npm install -g spellchecker-cli
spellchecker -f '**/*.md' -d dictionary.txt

# 链接检查
npm install -g markdown-link-check
find . -name "*.md" | xargs -I {} markdown-link-check {}

# 格式检查
npm install -g markdownlint-cli
markdownlint '**/*.md'
```

### 用户反馈
```python
# feedback.py
class DocumentationFeedback:
    def __init__(self):
        self.feedback_db = []

    def collect_feedback(self, page, rating, comment):
        """收集文档反馈"""
        self.feedback_db.append({
            'page': page,
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.now()
        })

    def analyze_feedback(self):
        """分析反馈改进文档"""
        # 识别问题页面
        # 提取改进建议
        # 生成改进报告
        pass
```

## 维护指南

### 定期更新
1. **每次发布**: 更新版本号和变更日志
2. **每月**: 检查链接有效性
3. **每季度**: 审查文档完整性
4. **每年**: 全面重构和优化

### 贡献指南
```markdown
# Contributing to Documentation

## 提交规范
- docs: 文档更新
- fix: 修复文档错误
- feat: 新增文档章节

## 写作风格
- 使用主动语态
- 保持简洁明了
- 提供实际例子
- 避免技术术语堆砌

## 审查流程
1. 自我审查
2. 同行评审
3. 技术审核
4. 最终批准
```

### 工具推荐
- **Typora**: Markdown编辑器
- **draw.io**: 架构图绘制
- **Carbon**: 代码截图美化
- **Grammarly**: 英文语法检查
- **Vale**: 技术写作风格检查

## 未来规划

### 短期目标
- [ ] 视频教程制作
- [ ] 交互式文档
- [ ] API playground
- [ ] 搜索功能优化

### 中期目标
- [ ] 多语言自动翻译
- [ ] 文档版本对比
- [ ] 用户评论系统
- [ ] AI问答助手

### 长期目标
- [ ] 知识图谱构建
- [ ] 个性化文档推荐
- [ ] 协作编辑平台
- [ ] 文档自动生成