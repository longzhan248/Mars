# CLAUDE.md - iOS沙盒浏览模块

## 模块概述
iOS应用沙盒文件浏览器，基于`pymobiledevice3`实现设备连接、应用管理、文件浏览、预览和操作功能。支持智能应用过滤、文件搜索、多格式预览。

## 核心功能

### 设备和应用管理
- **设备检测**: 自动列出连接的iOS设备
- **智能应用过滤**: 预先检测访问权限，只显示可访问应用
- **多线程并发**: 5线程并发检测，速度提升5倍
- **自动加载**: 首次进入自动加载第一个可访问应用

### 文件浏览和操作
- **树形浏览**: 懒加载目录结构
- **文件预览**: 支持文本、图片、十六进制格式
- **文件操作**: 预览、导出、删除
- **搜索功能**: 文件名和内容递归搜索

### 连接管理
- **自动恢复**: 连接断开时自动重新加载
- **错误处理**: 智能识别连接相关错误
- **图片文件特殊处理**: 避免系统预览导致连接断开

## 目录结构
```
sandbox/
├── device_manager.py     # 设备管理
├── app_manager.py       # 应用管理（智能过滤）
├── file_browser.py      # 文件浏览（懒加载）
├── file_operations.py   # 文件操作（连接恢复）
├── file_preview.py      # 文件预览（多格式）
└── search_manager.py    # 搜索功能
```

## 核心特性

### 智能应用过滤 🚀
```python
# 多线程并发检测应用权限
with ThreadPoolExecutor(max_workers=5) as executor:
    # 5个线程同时检测，实时更新进度
    # 30个应用：60-90秒 → 12-18秒
```

### 文件预览支持
- **文本**: `.txt, .log, .json, .xml, .plist, .html, .css, .js, .py, .md, .sh, .h, .m, .swift, .c, .cpp`
- **图片**: `.png, .jpg, .jpeg, .gif, .bmp, .ico` (需Pillow库)
- **其他**: 十六进制dump显示

### 搜索功能
- **文件名搜索**: 快速查找文件/目录
- **内容搜索**: 递归搜索文本文件内容
- **异步执行**: 后台搜索，不阻塞UI
- **结果高亮**: 蓝色显示匹配结果

## 技术实现

### 依赖库
```python
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.house_arrest import HouseArrestService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from PIL import Image, ImageTk  # 图片预览
```

### 关键技术点
- **HouseArrestService限制**: 每个应用只能有一个实例
- **懒加载机制**: 目录展开时才加载内容
- **批量UI更新**: 收集数据后一次性插入
- **连接恢复**: 自动检测并重新建立连接

### 图片文件处理
由于系统预览程序会保持文件句柄导致连接断开：
- ❌ 右键菜单不显示"打开"选项（图片文件）
- ✅ 提供"预览"（程序内查看）
- ✅ 提供"导出"（保存到本地）
- ✅ 友好提示引导正确操作

## 使用方法

### 基础使用
```python
from gui.modules.sandbox import SandboxBrowserTab

# 创建标签页
sandbox_tab = SandboxBrowserTab(parent_notebook, main_app)
```

### 文件操作
```python
# 预览文件
sandbox_tab.preview_selected()

# 导出文件
sandbox_tab.export_selected()

# 搜索文件
sandbox_tab.search_files("keyword", "文件名")
```

## 常见问题

**Q: 为什么有些应用看不到？**
A: 智能过滤功能预先检测访问权限，只显示可访问应用，避免InstallationLookupFailed错误。

**Q: 图片文件为什么不能"打开"？**
A: 系统预览会保持文件句柄导致连接断开。请使用"预览"查看或"导出"到本地。

**Q: 搜索速度慢怎么办？**
A: 文件名搜索很快，文件内容搜索需要读取文本文件。搜索在后台执行，不会阻塞UI。

## 性能优化

### 已实现优化
- **多线程检测**: 5倍速度提升
- **懒加载**: 减少初始加载时间
- **批量更新**: 提高UI响应速度
- **异步操作**: 避免主线程阻塞

### 性能指标
- **应用检测**: 30个应用12-18秒
- **文件加载**: 按需加载，秒级响应
- **搜索速度**: 文件名搜索<1秒，内容搜索取决于文件大小

## 版本历史
- **v2.2.0**: 多线程并发检测，性能提升5倍
- **v2.1.0**: 图片文件UI限制，避免连接断开
- **v2.0.0**: 完善连接自动恢复机制
- **v1.1.0**: 智能应用过滤功能
- **v1.0.0**: 基础文件浏览功能

---

*最后更新: 2025-10-11*
