# CLAUDE.md - iOS沙盒浏览模块技术文档

## 模块概述

iOS应用沙盒文件浏览器，提供完整的设备连接、应用管理、文件浏览、预览和操作功能。基于 `pymobiledevice3` 库实现，支持智能应用过滤、文件搜索、多格式预览等高级特性。

## 目录结构

```
sandbox/
├── __init__.py              # 模块导出
├── device_manager.py        # 设备管理
├── app_manager.py          # 应用管理
├── file_browser.py         # 文件浏览
├── file_operations.py      # 文件操作
├── file_preview.py         # 文件预览
├── search_manager.py       # 搜索功能
├── REFACTORING.md          # 重构总结
├── BUGFIX.md              # Bug修复记录
└── CLAUDE.md              # 技术文档（本文件）
```

## 核心模块详解

### 1. device_manager.py - 设备管理

**职责**：
- 检测和列出连接的iOS设备
- 显示设备信息（名称、型号、UDID）
- 处理设备选择事件

**关键方法**：
```python
def refresh_devices(self):
    """刷新设备列表"""
    devices = list_devices()
    for device in devices:
        # 获取设备信息并映射 UDID
        self.device_map[device_name] = udid
```

**技术实现**：
- 使用 `pymobiledevice3.usbmux.list_devices()` 列举设备
- 通过 `LockdownClient` 获取设备详细信息
- 构建设备名称到UDID的映射表

---

### 2. app_manager.py - 应用管理

**职责**：
- 加载iOS设备上的用户应用
- **智能过滤不可访问的应用** 🚀
- 显示加载和过滤统计
- 自动加载第一个可访问的应用

**核心特性**：

#### 智能应用过滤（2025-10-10 新增）
在加载应用列表时，预先检测每个应用的沙盒访问权限，只显示可访问的应用。

```python
def _load_apps_async(self):
    """异步加载应用列表，并预先过滤无法访问的应用"""

    # 获取所有应用
    apps = instproxy.get_apps(application_type='User')

    # 逐个检测访问权限
    for app_id in apps:
        try:
            # 尝试创建 HouseArrestService
            HouseArrestService(lockdown=lockdown, bundle_id=app_id)
            accessible_apps.append(app_id)  # 可访问
        except:
            filtered_count += 1  # 过滤掉
```

**用户体验改进**：
- ✅ 只显示可访问的应用
- ✅ 实时显示检测进度（已检测 n/total）
- ✅ 显示过滤统计信息
- ✅ 避免用户选择到无法访问的应用
- ✅ 杜绝 `InstallationLookupFailed` 错误

---

### 3. file_browser.py - 文件浏览

**职责**：
- 树形结构展示文件系统
- 懒加载目录内容（按需加载）
- 处理目录展开和双击事件
- 格式化文件大小和日期

**核心方法**：

```python
def load_sandbox_async(self):
    """异步加载沙盒文件"""
    # 创建 HouseArrestService 连接
    house_arrest = HouseArrestService(lockdown=lockdown, bundle_id=app_id)
    self.parent.afc_client = house_arrest

    # 加载根目录
    self._list_directory(".", "")

def _list_directory(self, path, parent_item):
    """列出目录内容，批量插入UI"""
    items = self.parent.afc_client.listdir(path)
    # 收集数据后批量插入，避免频繁UI更新
```

**技术特点**：
- **懒加载**：目录首次展开时才加载内容
- **占位符机制**：使用placeholder标识未加载的目录
- **异步处理**：文件操作在后台线程执行，避免UI阻塞
- **批量更新**：收集数据后一次性插入树形控件

---

### 4. file_operations.py - 文件操作

**职责**：
- 导出文件/目录到本地
- 打开文件（使用系统默认程序）
- 删除文件/目录
- **自动处理连接断开问题** ⚠️

**核心功能**：

#### 连接断开自动恢复
文件操作后（特别是"打开"操作），iOS设备可能断开AFC连接。模块会自动检测并恢复。

```python
def _read_file_with_retry(self, remote_path):
    """读取文件，连接断开时自动重新加载应用"""
    try:
        return self.parent.afc_client.get_file_contents(remote_path)
    except Exception as e:
        # 检测连接相关错误
        if self._is_connection_error(e):
            # 提示用户并重新加载应用
            messagebox.showinfo("提示", "连接已断开，正在自动重新加载...")
            self._reload_sandbox()
            raise
```

**支持的错误类型**：
- `ConnectionAbortedError` - 连接被中止
- `ConnectionTerminatedError` - 连接被终止
- `ConstError` - AFC协议错误
- `magic` / `parsing` 错误 - AFC状态异常

#### 图片文件特殊处理（2025-10-11 改进）
由于打开图片文件会导致系统预览程序保持文件句柄，引发连接断开和界面刷新，现已采用更友好的处理方式：

**UI层面限制**：
```python
# sandbox_tab.py - 右键菜单动态调整
def _update_context_menu(self, is_image):
    """根据文件类型更新右键菜单"""
    self.context_menu.add_command(label="预览", ...)
    self.context_menu.add_command(label="导出", ...)

    # 图片文件不显示"打开"选项
    if not is_image:
        self.context_menu.add_command(label="打开", ...)

# 底部按钮点击检查
def _open_file_with_check(self):
    """打开文件前检查是否为图片文件"""
    if self._is_image_file(item_id):
        messagebox.showinfo("提示",
            "图片文件无法使用\"打开\"功能\n\n"
            "建议使用以下方式查看图片:\n"
            "• 预览: 在程序内查看\n"
            "• 导出: 保存到本地后查看")
        return
```

**文件类型处理策略**：
- 📷 **图片**：不提供"打开"选项，引导用户使用"预览"或"导出"
- 🎬 **视频**：可正常打开（通常不会断开连接）
- 📄 **文本**：可正常打开
- 💾 **数据库**：可正常打开（会提示使用专业工具）

**用户体验改进**：
- ✅ 右键菜单不显示"打开"选项（图片文件）
- ✅ 底部按钮给出友好提示并引导正确操作
- ✅ 彻底避免连接断开和界面刷新问题
- ✅ 保留"预览"和"导出"两种查看方式

---

### 5. file_preview.py - 文件预览

**职责**：
- 文本文件预览（带语法高亮）
- 图片预览（支持缩放）
- 十六进制预览
- 数据库文件识别

**支持的文件格式**：

#### 文本文件
`.txt`, `.log`, `.json`, `.xml`, `.plist`, `.html`, `.css`, `.js`, `.py`, `.md`, `.sh`, `.h`, `.m`, `.swift`, `.c`, `.cpp`

```python
# 尝试UTF-8，失败则尝试GBK
try:
    text_content = data.decode('utf-8')
except:
    text_content = data.decode('gbk')
```

#### 图片文件（需要Pillow库）
`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.ico`

```python
from PIL import Image, ImageTk
img = Image.open(io.BytesIO(image_data))
# 自动缩放至合适大小
img.thumbnail((800, 600), Image.Resampling.LANCZOS)
```

#### 其他文件
显示十六进制dump（前512字节）

**预览窗口特性**：
- ✅ 工具栏显示文件信息
- ✅ "另存为"按钮
- ✅ 滚动条支持
- ✅ 自适应窗口大小

---

### 6. search_manager.py - 搜索功能

**职责**：
- 文件名搜索
- 文件内容搜索（递归）
- 搜索结果高亮显示
- 清除搜索恢复浏览

**搜索类型**：

#### 文件名搜索
快速查找包含关键词的文件或目录

```python
if search_type in ["文件名", "所有"]:
    if keyword.lower() in item.lower():
        results.append({
            'name': item,
            'path': item_path,
            'match_type': '文件名'
        })
```

#### 文件内容搜索
在文本文件内容中搜索关键词

```python
if search_type in ["文件内容", "所有"]:
    if file_ext in TEXT_EXTENSIONS:
        content = self.parent.afc_client.get_file_contents(item_path)
        if keyword.lower() in content.decode('utf-8', errors='ignore').lower():
            results.append({
                'name': item,
                'path': item_path,
                'match_type': '文件内容'
            })
```

**搜索特性**：
- 🔍 递归搜索所有子目录
- 🚀 异步执行，不阻塞UI
- 📊 实时显示搜索进度
- 🎯 结果用蓝色高亮显示
- 🏷️ 显示匹配类型标签 `[文件名]` 或 `[文件内容]`

---

## 技术架构

### 依赖库
```python
# iOS设备通信
from pymobiledevice3.lockdown import create_using_usbmux, LockdownClient
from pymobiledevice3.services.house_arrest import HouseArrestService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.usbmux import list_devices

# 图片预览（可选）
from PIL import Image, ImageTk
```

### 数据流

```
设备选择
    ↓
应用加载（智能过滤）
    ↓
创建 HouseArrestService
    ↓
文件浏览（懒加载）
    ↓
文件操作（自动恢复连接）
```

### 连接管理

#### HouseArrestService 限制
**重要**：不能为同一个应用创建多个 `HouseArrestService` 实例，否则会导致程序崩溃（Trace/BPT trap: 5）。

**正确做法**：
- ✅ 每个应用只维护一个 `HouseArrestService` 实例
- ✅ 连接断开时，重新加载整个应用（`load_sandbox_async()`）
- ❌ 不要尝试只重连而不刷新UI

#### 连接断开场景
1. **"打开"操作** - 系统应用保持文件句柄
2. **长时间无操作** - 设备超时断开
3. **设备锁屏** - 自动断开连接
4. **文件读取后** - 某些情况下设备主动断开

#### 恢复策略
```python
# 检测连接错误
if is_connection_error(error):
    # 提示用户
    messagebox.showinfo("提示", "连接已断开，正在自动重新加载...")

    # 重新加载应用（会创建新的 HouseArrestService）
    load_sandbox_async()
```

---

## 最佳实践

### 1. 文件操作
```python
# ✅ 推荐：使用重试包装
def export_file(self, remote_path, local_path):
    data = self._read_file_with_retry(remote_path)
    with open(local_path, 'wb') as f:
        f.write(data)

# ❌ 避免：直接读取，不处理错误
data = self.parent.afc_client.get_file_contents(remote_path)
```

### 2. UI更新
```python
# ✅ 推荐：批量收集数据，一次性插入
items_data = []
for item in items:
    items_data.append({'name': item, ...})
self.parent.parent.after(0, self._insert_tree_items, items_data)

# ❌ 避免：逐个插入，频繁更新UI
for item in items:
    self.parent.parent.after(0, lambda: self.tree.insert(...))
```

### 3. 异步操作
```python
# ✅ 推荐：耗时操作在后台线程
threading.Thread(target=self._export_file_async, daemon=True).start()

# ❌ 避免：在主线程执行，会阻塞UI
self._export_file_async()
```

### 4. 错误处理
```python
# ✅ 推荐：检测特定错误类型
if "connectionaborted" in type(e).__name__.lower():
    self._handle_connection_error()

# ❌ 避免：捕获所有异常
except Exception:
    pass
```

---

## 常见问题

### Q: 图片文件为什么不能使用"打开"功能？
**A**: 打开图片文件会导致系统预览程序保持文件句柄，引发iOS设备连接断开和界面刷新（目录折叠）。

**当前解决方案（v2.1.0）**：
- ✅ 图片文件右键菜单不显示"打开"选项
- ✅ 点击底部"打开文件"按钮时给出友好提示
- ✅ 引导用户使用"预览"（程序内查看）或"导出"（保存到本地）
- ✅ 彻底避免连接断开问题

**推荐操作**：
- 快速查看：使用"预览"功能在程序内查看图片
- 保存使用：使用"导出"功能保存到本地后查看

### Q: 为什么有些应用看不到？
**A**: 智能过滤功能会预先检测应用的沙盒访问权限，只显示可访问的应用。这避免了选择无法访问的应用导致的错误。

### Q: 搜索速度慢怎么办？
**A**:
- 文件名搜索很快
- 文件内容搜索需要读取所有文本文件，速度取决于文件数量和大小
- 搜索在后台线程执行，不会阻塞UI

### Q: 如何添加新的文件预览格式？
**A**: 在 `file_preview.py` 的 `_preview_file_async` 方法中添加：
```python
elif file_ext in ['.your_format']:
    # 实现预览逻辑
    self._show_your_format_preview(name, data)
```

---

## 性能优化

### 1. 懒加载
- 目录首次展开时才加载内容
- 减少初始加载时间
- 降低内存占用

### 2. 批量操作
- 收集数据后批量插入树形控件
- 减少UI更新次数
- 提高响应速度

### 3. 异步处理
- 所有耗时操作在后台线程
- UI线程只负责更新界面
- 使用 `parent.after()` 安全更新UI

### 4. 缓存策略
- 设备信息缓存
- 应用列表缓存
- 减少重复的设备通信

---

## 版本历史

### v2.1.0 (2025-10-11)
- ✅ **图片文件UI层面限制**：不显示"打开"选项，避免连接断开
- ✅ 动态右键菜单：根据文件类型自动调整菜单项
- ✅ 友好提示：引导用户使用"预览"或"导出"查看图片
- ✅ 改进用户体验：彻底解决图片打开导致的界面刷新问题

### v2.0.0 (2025-10-11)
- ✅ 完善连接断开自动恢复机制
- ✅ 图片文件特殊处理（打开后自动重新加载）
- ✅ 移除不稳定的重连机制
- ✅ 清理调试代码

### v1.1.0 (2025-10-10)
- ✅ 智能应用过滤功能
- ✅ 自动加载首个可访问应用
- ✅ 实时显示加载和过滤进度

### v1.0.0 (2025-09-28)
- ✅ 完成模块化重构
- ✅ 基础文件浏览功能
- ✅ 文件预览和操作
- ✅ 搜索功能

---

## 开发指南

### 添加新功能模块
1. 在 `sandbox/` 目录创建新的 `.py` 文件
2. 实现功能类，构造函数接收 `parent_tab`
3. 在 `__init__.py` 中导出
4. 在主标签页中初始化和调用

### 调试技巧
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印连接状态
print(f"AFC Client: {self.parent.afc_client}")
print(f"Device ID: {self.parent.device_id}")
print(f"App ID: {self.parent.current_app_id}")
```

### 测试要点
- ✅ 设备连接/断开
- ✅ 应用切换
- ✅ 文件操作（预览、打开、导出、删除）
- ✅ 搜索功能
- ✅ 连接断开恢复
- ✅ 边界条件（空目录、大文件、特殊字符）

---

## 参考资料

- [pymobiledevice3 文档](https://github.com/doronz88/pymobiledevice3)
- [Apple File Conduit (AFC) 协议](https://www.theiphonewiki.com/wiki/AFC)
- [iOS沙盒机制](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html)

---

**文档维护者**: Claude Code
**最后更新**: 2025-10-11
**模块版本**: v2.1.0
