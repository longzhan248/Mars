# iOS混淆工具 - 自定义白名单功能

## 功能概述

自定义白名单功能允许用户定义自己不希望被混淆的类名、方法名、属性名等符号。除了内置的系统API白名单和自动检测的第三方库白名单外，用户可以添加自己的白名单项，确保特定符号在混淆过程中保持不变。

## 功能亮点

✅ **GUI界面管理** - 友好的可视化界面，无需手动编辑JSON文件
✅ **完整CRUD操作** - 添加、编辑、删除白名单项
✅ **导入导出支持** - 支持JSON和TXT两种格式
✅ **持久化存储** - 自动保存到`custom_whitelist.json`文件
✅ **无缝集成** - 自动集成到混淆执行流程
✅ **实时统计** - 显示白名单项数量和类型分布

## 使用场景

### 1. 保护特定的业务代码
某些关键业务类名、方法名可能被其他模块或配置文件引用，混淆后会导致功能异常。

**示例**：
```objc
// 支付模块的类名被配置文件引用
@interface PaymentManager : NSObject
@end

// 添加到白名单：
// 名称: PaymentManager
// 类型: class
// 原因: 配置文件中硬编码了类名
```

### 2. 保护动态调用的方法
使用Runtime动态调用的方法名不能被混淆，否则运行时会找不到方法。

**示例**：
```objc
// 动态调用的方法
SEL selector = NSSelectorFromString(@"handlePushNotification:");
[self performSelector:selector withObject:notification];

// 添加到白名单：
// 名称: handlePushNotification:
// 类型: method
// 原因: Runtime动态调用
```

### 3. 保护JSBridge接口
iOS与Web交互的JSBridge接口方法名通常在JS代码中硬编码，不能混淆。

**示例**：
```swift
// JSBridge方法
@objc func getUserInfo() -> String {
    // ...
}

// 添加到白名单：
// 名称: getUserInfo
// 类型: method
// 原因: JSBridge接口，JS代码中硬编码
```

### 4. 保护Notification名称
通知名称通常以常量形式定义，可能被多处引用，混淆后会导致通知失效。

**示例**：
```objc
extern NSString *const UserDidLoginNotification;

// 添加到白名单：
// 名称: UserDidLoginNotification
// 类型: constant
// 原因: 通知名称常量
```

## 使用指南

### 打开白名单管理窗口

1. 在主程序中切换到"iOS代码混淆"标签页
2. 在界面中间找到"🛡️ 管理白名单"按钮
3. 点击按钮，打开白名单管理窗口

### 添加白名单项

1. **点击"添加"按钮**
2. **填写信息**：
   - **符号名称**：输入完整的类名、方法名、属性名等（必填）
   - **符号类型**：从下拉列表选择（class/method/property/protocol/constant）
   - **添加原因**：简短说明为什么需要白名单（必填）
3. **点击"确定"**保存

**示例**：
```
符号名称: PaymentManager
符号类型: class
添加原因: 配置文件中硬编码了类名，不能混淆
```

### 编辑白名单项

1. **选中要编辑的项**（在列表中点击）
2. **点击"编辑"按钮**（或双击列表项）
3. **修改信息**
4. **点击"确定"**保存

### 删除白名单项

1. **选中要删除的项**（可多选，按住Ctrl或Cmd）
2. **点击"删除"按钮**
3. **确认删除**

⚠️ **注意**：删除操作不可恢复，请谨慎操作。

### 导入白名单

#### 从JSON文件导入

1. **点击"导入"按钮**
2. **选择JSON文件**
3. **导入完成**，新项目将添加到列表

**JSON格式**：
```json
{
  "version": "1.0",
  "updated": "2025-10-14T12:00:00",
  "items": [
    {
      "name": "PaymentManager",
      "type": "class",
      "reason": "配置文件引用"
    },
    {
      "name": "handlePushNotification:",
      "type": "method",
      "reason": "Runtime动态调用"
    }
  ]
}
```

#### 从TXT文件导入

1. **点击"导入"按钮**
2. **选择TXT文件**
3. **导入完成**，每行作为一个白名单项

**TXT格式**：
```txt
# iOS混淆自定义白名单
# 注释行（以#开头）会被忽略
PaymentManager
handlePushNotification:
getUserInfo
UserDidLoginNotification
```

⚠️ **注意**：TXT导入的项目类型默认为"auto"，原因为"Imported from TXT"。

### 导出白名单

#### 导出为JSON

1. **点击"导出"按钮**
2. **选择保存位置**，文件名以`.json`结尾
3. **导出完成**

JSON格式包含完整的元数据和所有白名单项信息。

#### 导出为TXT

1. **点击"导出"按钮**
2. **选择保存位置**，文件名以`.txt`结尾
3. **导出完成**

TXT格式仅包含符号名称列表，适合快速查看和分享。

## 文件位置

自定义白名单保存在以下位置：
```
gui/modules/obfuscation/custom_whitelist.json
```

文件会在首次添加白名单项时自动创建。

## 白名单优先级

混淆过程中的白名单检查优先级：

1. **系统API白名单**（最高优先级）
   - 内置500+系统类、1000+系统方法
   - 例如：UIViewController、NSString等

2. **第三方库白名单**
   - 自动检测的CocoaPods、SPM、Carthage依赖
   - 例如：AFNetworking、SDWebImage等

3. **自定义白名单**（本功能）
   - 用户手动添加的白名单项
   - 适用于业务代码中的特殊情况

**检查逻辑**：
```
if 符号名称 in 系统API白名单:
    不混淆
elif 符号名称 in 第三方库白名单:
    不混淆
elif 符号名称 in 自定义白名单:
    不混淆
else:
    执行混淆
```

## 混淆执行时的应用

当用户点击"▶️ 开始混淆"按钮时，自定义白名单会自动加载并应用：

### 1. 加载阶段

```
📋 正在加载自定义白名单...
📋 已加载 3 个自定义白名单项
   - PaymentManager
   - handlePushNotification:
   - getUserInfo
```

### 2. 混淆阶段

在符号混淆过程中，自动跳过白名单中的符号：

```
✅ 混淆类名: MyViewController -> WHC8kF3x
⏭️  跳过白名单: PaymentManager (自定义白名单)
✅ 混淆方法: loadData -> WHCm9K2p
⏭️  跳过白名单: handlePushNotification: (自定义白名单)
```

### 3. 统计报告

混淆完成后，在统计报告中会显示白名单项数量：

```
📊 混淆统计：
   处理文件: 50 个
   混淆符号: 120 个
   跳过系统API: 30 个
   跳过第三方库: 15 个
   跳过自定义白名单: 3 个 ⬅️ 本功能
   总耗时: 5.2 秒
```

## 最佳实践

### 1. 合理使用白名单

❌ **不推荐**：将所有类都加入白名单
- 失去混淆的意义
- 无法应对机器审核

✅ **推荐**：仅将必要的符号加入白名单
- 被配置文件/JS代码硬编码的符号
- Runtime动态调用的方法
- 与外部系统约定的接口

### 2. 添加详细的原因

❌ **不推荐**：原因写"重要"、"不要混淆"等模糊描述

✅ **推荐**：详细说明为什么需要白名单
```
原因: JS代码中硬编码了getUserInfo方法名，用于JSBridge通信
原因: 配置文件config.plist中引用了PaymentManager类名
原因: 使用NSSelectorFromString动态调用handlePushNotification:
```

### 3. 定期审查白名单

- 每次发版前检查白名单是否还需要
- 移除不再使用的白名单项
- 保持白名单尽可能小

### 4. 备份白名单文件

- 将`custom_whitelist.json`加入版本控制（Git）
- 团队成员共享同一份白名单
- 避免每个人维护不同的白名单

### 5. 结合测试验证

- 添加白名单后，运行完整测试
- 确认功能正常
- 如果出现问题，检查是否有遗漏的符号

## 故障排查

### Q1: 白名单文件在哪里？

**A**: 文件位置：`gui/modules/obfuscation/custom_whitelist.json`

如果文件不存在，添加第一个白名单项时会自动创建。

### Q2: 添加白名单后混淆仍然失败？

**可能原因**：
1. 符号名称拼写错误
2. 类型选择不正确（例如方法误选为类）
3. 方法名缺少冒号（Objective-C方法需要冒号）

**解决方案**：
- 仔细检查符号名称的大小写和拼写
- 确认符号类型选择正确
- Objective-C方法名注意冒号：`tableView:cellForRowAtIndexPath:`

### Q3: 导入TXT文件后，白名单项类型都是"auto"？

**A**: 这是正常现象。TXT文件仅包含符号名称，不包含类型信息。

**建议**：
- 导入后，使用"编辑"功能修改类型
- 或者使用JSON格式导入，保留完整信息

### Q4: 删除了白名单项，但混淆时还是跳过？

**可能原因**：符号在系统API白名单或第三方库白名单中。

**解决方案**：
- 检查是否为系统类名（如UIViewController）
- 检查是否为第三方库（如AFNetworking）
- 系统和第三方库白名单不能通过GUI删除

### Q5: 白名单文件损坏或格式错误？

**解决方案**：
1. 备份当前文件（如果存在）
2. 删除`custom_whitelist.json`
3. 重新添加白名单项
4. 或者手动编辑JSON文件，确保格式正确

**正确的JSON格式**：
```json
{
  "version": "1.0",
  "updated": "2025-10-14T12:00:00",
  "items": [
    {
      "name": "ClassName",
      "type": "class",
      "reason": "原因说明"
    }
  ]
}
```

## 技术实现

### 数据结构

```python
# 白名单数据结构
{
    "version": "1.0",              # 文件版本
    "updated": "ISO8601时间戳",     # 最后更新时间
    "items": [                     # 白名单项列表
        {
            "name": "符号名称",     # 类名、方法名、属性名等
            "type": "符号类型",     # class/method/property/protocol/constant
            "reason": "添加原因"    # 说明为什么需要白名单
        }
    ]
}
```

### 核心方法

```python
# 加载自定义白名单
def load_custom_whitelist(self, tree):
    """从custom_whitelist.json加载白名单项到Treeview"""

# 保存自定义白名单
def save_custom_whitelist(self, tree):
    """将Treeview中的白名单项保存到custom_whitelist.json"""

# 添加白名单项
def add_whitelist_item(self, tree):
    """打开对话框添加新的白名单项"""

# 编辑白名单项
def edit_whitelist_item(self, tree):
    """编辑选中的白名单项"""

# 删除白名单项
def delete_whitelist_item(self, tree):
    """删除选中的白名单项（支持多选）"""

# 导入白名单
def import_whitelist(self, tree):
    """从JSON或TXT文件导入白名单"""

# 导出白名单
def export_whitelist_file(self, tree):
    """导出白名单到JSON或TXT文件"""
```

### 集成到混淆引擎

```python
# 在_run_obfuscation()方法中加载自定义白名单
custom_whitelist = []
whitelist_file = os.path.join(
    os.path.dirname(__file__),
    "obfuscation",
    "custom_whitelist.json"
)

if os.path.exists(whitelist_file):
    with open(whitelist_file, 'r', encoding='utf-8') as f:
        whitelist_data = json.load(f)
        custom_whitelist = [item['name'] for item in whitelist_data.get('items', [])]

    if custom_whitelist:
        self.log(f"📋 已加载 {len(custom_whitelist)} 个自定义白名单项")

# 传递给混淆配置
config = self.obfuscation_config_class(
    # ... 其他配置 ...
    custom_whitelist=custom_whitelist  # 自定义白名单
)
```

## 测试验证

完整的测试套件已验证所有功能：

### 测试用例

1. ✅ **test_whitelist_file_operations** - 文件操作
   - 保存白名单到JSON文件
   - 加载白名单从JSON文件
   - 数据完整性验证

2. ✅ **test_whitelist_export_txt** - TXT导出
   - 导出为TXT格式
   - 验证导出内容正确

3. ✅ **test_whitelist_import_txt** - TXT导入
   - 从TXT文件导入
   - 解析行内容
   - 忽略注释和空行

4. ✅ **test_whitelist_integration** - 引擎集成
   - 模拟混淆引擎加载白名单
   - 验证白名单项格式
   - 测试白名单应用

5. ✅ **test_whitelist_validation** - 数据验证
   - 验证有效数据
   - 拒绝无效数据
   - 测试边界条件

### 运行测试

```bash
# 运行所有测试
python tests/test_custom_whitelist.py

# 测试结果：
# 总计: 5/5 通过
# 🎉 所有测试通过！自定义白名单功能正常工作。
```

## 版本历史

### v1.0.0 (2025-10-14)

#### 初始发布

**新增功能**：
- ✅ GUI白名单管理窗口
- ✅ 添加、编辑、删除白名单项
- ✅ 导入导出（JSON和TXT格式）
- ✅ 持久化存储（custom_whitelist.json）
- ✅ 集成到混淆执行流程
- ✅ 实时统计显示

**测试验证**：
- ✅ 5个测试用例全部通过
- ✅ 文件操作验证
- ✅ 导入导出验证
- ✅ 引擎集成验证
- ✅ 数据验证

**文档**：
- ✅ 完整的使用指南
- ✅ 最佳实践建议
- ✅ 故障排查指南
- ✅ 技术实现说明

## 反馈和改进

如果您在使用过程中遇到问题或有改进建议，请：

1. **提交Issue** - 在项目GitHub页面提交Issue
2. **联系开发者** - 通过项目README中的联系方式
3. **查看日志** - 检查混淆日志中的错误信息

我们欢迎任何反馈，帮助我们改进这个功能！

---

**文档版本**: v1.0.0
**更新时间**: 2025-10-14
**作者**: Claude Code
