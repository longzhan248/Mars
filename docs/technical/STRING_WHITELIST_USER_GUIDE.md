# 字符串加密白名单使用指南

## 功能简介

字符串加密白名单允许您指定哪些字符串常量不应该被加密。这对于保护系统API名称、配置键名、通知名称等至关重要，因为加密这些字符串可能导致Runtime调用失败。

## 快速开始

### 1. 打开白名单管理器

1. 启动主程序
2. 切换到"iOS代码混淆"标签页
3. 勾选"字符串加密 🆕"复选框
4. 点击"🛡️ 加密白名单"按钮

![白名单按钮位置](位于右侧选项区域，字符串加密配置下方)

### 2. 添加白名单项

点击"➕ 添加"按钮，填写：
- **字符串内容**: 需要保护的字符串（例如："viewDidLoad"）
- **备注说明**: 添加原因，便于后期维护（例如："系统方法名"）

**示例**:
```
字符串内容: viewDidLoad
备注说明: UIViewController生命周期方法，不能加密
```

### 3. 批量导入

如果您有很多字符串需要添加，可以使用导入功能：

**JSON格式**:
```json
{
  "version": "1.0",
  "strings": [
    {"content": "viewDidLoad", "reason": "系统方法"},
    {"content": "tableView", "reason": "UITableView代理"},
    {"content": "NSUserDefaults", "reason": "系统类"}
  ]
}
```

**TXT格式**（每行一个字符串）:
```
viewDidLoad
tableView
NSUserDefaults
applicationDidFinishLaunching
```

## 常见使用场景

### 场景1: 保护系统方法名

当您的代码使用Runtime或performSelector时，方法名字符串不能加密：

```objective-c
// ❌ 如果"viewDidLoad"被加密，这段代码会失败
SEL selector = NSSelectorFromString(@"viewDidLoad");
[self performSelector:selector];
```

**解决方案**: 将"viewDidLoad"添加到白名单

---

### 场景2: 保护配置键名

UserDefaults和配置文件中的键名不应加密：

```objective-c
// ❌ 如果"userToken"被加密，数据无法正确读取
NSString *token = [[NSUserDefaults standardUserDefaults]
                   objectForKey:@"userToken"];
```

**解决方案**: 将"userToken"添加到白名单

---

### 场景3: 保护通知名称

NSNotification的名称字符串不能加密：

```objective-c
// ❌ 如果通知名称被加密，观察者无法接收通知
[[NSNotificationCenter defaultCenter]
 postNotificationName:@"UserLoginSuccess" object:nil];
```

**解决方案**: 将"UserLoginSuccess"添加到白名单

---

### 场景4: 保护KVO/KVC键路径

Key-Value Observing和Key-Value Coding的键名不能加密：

```objective-c
// ❌ 如果"username"被加密，KVO会失败
[user addObserver:self
       forKeyPath:@"username"
          options:NSKeyValueObservingOptionNew
          context:nil];
```

**解决方案**: 将"username"添加到白名单

---

### 场景5: 保护第三方SDK调用

第三方SDK要求的字符串参数不应加密：

```objective-c
// ❌ 如果"action"被加密，SDK无法识别
[ThirdPartySDK trackEvent:@"action" properties:@{}];
```

**解决方案**: 将"action"添加到白名单

---

## 推荐的白名单项

### UIKit常用方法名
```
viewDidLoad
viewWillAppear
viewDidAppear
viewWillDisappear
viewDidDisappear
viewDidLayoutSubviews
tableView
numberOfRowsInSection
cellForRowAtIndexPath
didSelectRowAtIndexPath
```

### 配置和存储
```
NSUserDefaults
userToken
apiKey
isFirstLaunch
lastSyncTime
userSettings
```

### 通知名称
```
UIApplicationDidFinishLaunchingNotification
UIApplicationWillResignActiveNotification
UIApplicationDidEnterBackgroundNotification
UIApplicationWillEnterForegroundNotification
UIApplicationDidBecomeActiveNotification
```

### KVO/KVC常用键
```
frame
bounds
center
alpha
hidden
backgroundColor
```

## 白名单管理技巧

### 1. 使用描述性备注

良好的备注可以帮助您理解为什么添加这个白名单项：

```
✅ 好的备注:
- "UITableView代理方法，Runtime调用需要"
- "UserDefaults存储键，数据持久化使用"
- "第三方SDK要求的事件名称"

❌ 不好的备注:
- "不知道"
- "测试"
- ""（空白）
```

### 2. 定期审查

建议每个版本发布前审查白名单：
- 移除不再使用的字符串
- 添加新增的Runtime调用字符串
- 更新备注说明

### 3. 导出备份

定期导出白名单作为备份：
1. 点击"💾 导出"按钮
2. 选择保存位置
3. 建议保存到项目版本控制中

### 4. 团队共享

如果您在团队中工作：
- 将白名单文件提交到Git
- 在代码审查时检查白名单更新
- 文档化白名单规则

## 注意事项

### ⚠️ 不要过度使用

过多的白名单项会降低混淆效果。只添加真正需要保护的字符串。

### ⚠️ 区分大小写

白名单检查是区分大小写的：
- "viewDidLoad" ≠ "ViewDidLoad"
- "API_KEY" ≠ "api_key"

### ⚠️ 完全匹配

白名单使用完全匹配，不支持通配符：
- 如果您添加"view"，只有完全是"view"的字符串才会被保护
- "viewDidLoad"不会被保护（因为不是完全匹配"view"）

### ⚠️ 测试验证

添加白名单后，务必测试应用功能：
1. 运行混淆
2. 在测试设备上完整测试所有功能
3. 特别关注Runtime调用和数据持久化功能

## 常见问题

### Q: 如何知道哪些字符串应该加入白名单？

**A**: 通常需要加入白名单的字符串包括：
1. 使用`NSSelectorFromString()`、`performSelector:`的方法名
2. 使用`NSClassFromString()`的类名
3. `NSUserDefaults`、`NSNotificationCenter`的键名
4. KVO/KVC使用的属性名
5. 第三方SDK要求的特定字符串
6. Plist配置文件中的键名

### Q: 白名单会影响混淆效果吗？

**A**: 会，但影响有限。白名单只保护特定的字符串，其他字符串仍然会被加密。合理使用白名单（10-50项）对整体混淆效果影响很小。

### Q: 可以使用正则表达式吗？

**A**: 当前版本不支持正则表达式或通配符，只支持完全匹配。这是为了确保精确控制。

### Q: 白名单文件丢失了怎么办？

**A**: 建议：
1. 定期导出白名单备份
2. 将白名单文件添加到版本控制
3. 在项目文档中记录常用白名单项

### Q: 能否自动检测需要白名单的字符串？

**A**: 这是一个很好的建议，已加入未来改进计划。目前需要手动添加。

## 实际案例

### 案例1: 修复Runtime调用失败

**问题**:
```objective-c
// 加密后这段代码失败
SEL selector = NSSelectorFromString(@"customMethod");
[self performSelector:selector];
```

**解决**:
1. 打开白名单管理器
2. 添加"customMethod"到白名单
3. 重新运行混淆
4. 测试验证功能正常

---

### 案例2: 修复数据丢失

**问题**:
```objective-c
// 加密后数据无法读取
NSString *token = [[NSUserDefaults standardUserDefaults]
                   objectForKey:@"authToken"];
// token 为 nil
```

**解决**:
1. 添加"authToken"到白名单
2. 重新运行混淆
3. 数据正常读取

---

### 案例3: 修复通知不触发

**问题**:
```objective-c
// 加密后通知观察者无法接收通知
[[NSNotificationCenter defaultCenter]
 addObserver:self
    selector:@selector(handleNotification:)
        name:@"DataUpdated"
      object:nil];
```

**解决**:
1. 添加"DataUpdated"到白名单
2. 重新运行混淆
3. 通知正常触发

---

## 最佳实践

### ✅ 推荐做法

1. **创建项目白名单模板**
   - 为您的项目创建标准白名单
   - 包含常用的系统API和配置键
   - 新成员可以直接导入使用

2. **代码审查时检查**
   - 添加Runtime调用时，同时更新白名单
   - 在Pull Request中包含白名单更新

3. **自动化测试**
   - 混淆后运行完整的自动化测试
   - 验证所有Runtime调用和数据持久化功能

4. **文档化规则**
   - 在项目文档中记录白名单规则
   - 说明何时需要添加白名单项

### ❌ 不推荐做法

1. **盲目添加所有字符串**
   - 降低混淆效果
   - 失去字符串加密的意义

2. **不添加备注**
   - 后期维护困难
   - 团队成员不理解为何添加

3. **不测试验证**
   - 可能遗漏需要保护的字符串
   - 导致线上功能异常

4. **不备份白名单**
   - 文件丢失后需要重新创建
   - 浪费时间

---

## 技术支持

如果您在使用过程中遇到问题：

1. **检查日志**: 混淆日志会显示白名单加载情况
2. **查看文档**: `docs/technical/STRING_WHITELIST_TEST_REPORT.md`
3. **运行测试**: `python tests/test_string_whitelist_integration.py`
4. **提交Issue**: 在GitHub上报告问题

---

**文档版本**: v1.0.0
**最后更新**: 2025-10-14
**适用版本**: iOS代码混淆工具 v2.2.4+
