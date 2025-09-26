# iOS推送测试工具

## 功能介绍

这是一个功能完整的iOS推送测试工具，集成了SmartPush的核心功能到mars_log_analyzer项目中。支持以下功能：

- 🔐 **证书管理** - 支持P12、PEM、CER格式的推送证书
- 📱 **推送发送** - 支持开发环境和生产环境的推送发送
- 📝 **Payload编辑** - 提供多种预设模板，支持自定义JSON
- 📊 **历史记录** - 自动保存推送历史，方便查看和重发
- 🎨 **图形界面** - 友好的GUI界面，操作简单直观

## 安装要求

- Python 3.6+
- macOS/Linux/Windows
- 推送证书文件（.p12/.pem/.cer）

## 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd /Volumes/long/心娱/log

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r push_tools/requirements.txt
```

### 2. 启动GUI界面

```bash
# 方式1：使用启动脚本
./scripts/run_push_tool.sh

# 方式2：直接运行Python
python3 push_tools/apns_gui.py
```

### 3. 命令行使用

```bash
# 基本用法
python3 push_tools/apns_push.py \
    --cert /path/to/certificate.p12 \
    --password "证书密码" \
    --token "设备Token" \
    --message "测试消息" \
    --sandbox

# 自定义payload
python3 push_tools/apns_push.py \
    --cert certificate.p12 \
    --token "device_token" \
    --payload '{"aps":{"alert":"自定义消息","badge":5}}' \
    --sandbox
```

## GUI使用指南

### 界面说明

#### 1. 证书配置区
- **证书文件**：点击"浏览"选择推送证书文件
- **密码**：输入证书密码（如果有）
- **加载证书**：点击加载并验证证书
- 证书信息会显示环境、Bundle ID、有效期等

#### 2. Device Token输入
- 输入要推送的设备Token
- 支持带空格的格式，会自动处理

#### 3. 环境选择
- **开发环境(Sandbox)**：用于开发测试
- **生产环境(Production)**：用于正式发布的应用

#### 4. Payload编辑区
- **快速模板**：
  - 简单消息：仅包含文本
  - 带角标：包含角标数字
  - 带声音：包含提示音
  - 静默推送：后台唤醒
  - 富文本：标题、副标题、正文

- **自定义编辑**：直接编辑JSON格式的payload

#### 5. 高级选项
- **优先级**：10(立即) 或 5(省电)
- **推送类型**：alert、background、voip等
- **Topic**：通常为Bundle ID，会自动填充

#### 6. 日志区域
- **实时日志**：显示操作日志和错误信息
- **推送历史**：查看历史推送记录

### 使用步骤

1. **准备证书**
   - 从Apple开发者中心下载推送证书
   - 导出为.p12格式（包含私钥）

2. **加载证书**
   - 点击"浏览"选择证书文件
   - 输入密码（如果有）
   - 点击"加载证书"

3. **获取Device Token**
   - 在iOS应用中获取设备Token
   - 复制Token到输入框

4. **编辑推送内容**
   - 选择快速模板或自定义编辑
   - 验证Payload格式

5. **发送推送**
   - 选择正确的环境
   - 点击"发送推送"
   - 查看日志确认结果

## 证书说明

### 证书类型

1. **开发证书** (Development)
   - 用于开发环境测试
   - 文件名通常包含"Development"或"Developer"
   - 使用Sandbox服务器

2. **生产证书** (Production)
   - 用于App Store应用
   - 文件名通常包含"Production"或"Distribution"
   - 使用Production服务器

### 证书格式

- **.p12**：包含证书和私钥，推荐使用
- **.pem**：文本格式，可能需要单独的私钥文件
- **.cer**：仅包含证书，需要从钥匙串导出私钥

### 证书导出步骤

1. 打开"钥匙串访问"应用
2. 找到推送证书
3. 右键选择"导出..."
4. 选择.p12格式
5. 设置密码（可选）

## Payload示例

### 基础推送
```json
{
    "aps": {
        "alert": "Hello, World!",
        "badge": 1,
        "sound": "default"
    }
}
```

### 富文本推送
```json
{
    "aps": {
        "alert": {
            "title": "新消息",
            "subtitle": "来自朋友",
            "body": "这是消息的详细内容"
        },
        "badge": 5,
        "sound": "default",
        "mutable-content": 1
    }
}
```

### 静默推送
```json
{
    "aps": {
        "content-available": 1
    },
    "custom_data": {
        "update_type": "message_sync"
    }
}
```

### 自定义数据
```json
{
    "aps": {
        "alert": "您有新订单",
        "badge": 1
    },
    "order_id": "12345",
    "action": "view_order"
}
```

## 故障排除

### 常见问题

#### 1. 证书加载失败
- 确认证书格式正确
- 检查密码是否正确
- 确认证书未过期

#### 2. 推送发送失败
- **InvalidToken**：Token格式错误或不匹配环境
- **BadCertificate**：证书无效或过期
- **BadDeviceToken**：设备Token无效
- **TopicDisallowed**：Topic与证书不匹配

#### 3. 收不到推送
- 确认设备已注册推送通知
- 检查应用是否在前台（某些推送不会显示）
- 验证环境是否正确（开发/生产）
- 查看设备的通知设置

#### 4. 依赖安装问题
```bash
# 升级pip
pip install --upgrade pip

# 单独安装问题依赖
pip install cryptography
pip install httpx
pip install pyjwt
```

## 技术架构

### 核心模块

- **apns_push.py** - 推送核心逻辑
  - APNSCertificate：证书管理
  - APNSPusher：推送发送
  - PushHistory：历史记录
  - APNSManager：统一管理接口

- **apns_gui.py** - GUI界面
  - 基于tkinter
  - 支持拖放操作
  - 实时日志显示

### 使用的协议

- **HTTP/2**：新版APNS协议
- **TLS**：安全传输
- **JWT**：Token认证（可选）

### 数据存储

- 配置文件：`~/.apns_gui_config.json`
- 历史记录：`~/.apns_push_history.pkl`

## API参考

### Python API

```python
from push_tools import APNSManager

# 创建管理器
manager = APNSManager()

# 加载证书
manager.load_certificate('certificate.p12', password='123456')

# 发送推送
success, error = manager.send_push(
    device_token='your_device_token',
    alert_message='测试消息',
    badge=1,
    sound='default',
    sandbox=True
)

# 获取历史
history = manager.get_history(10)
```

### 命令行参数

```
用法: apns_push.py [-h] -c CERT [-p PASSWORD] -t TOKEN [-m MESSAGE]
                   [-b BADGE] [-s SOUND] [--sandbox] [--payload PAYLOAD]

参数:
  -c, --cert       证书文件路径
  -p, --password   证书密码
  -t, --token      设备Token
  -m, --message    推送消息
  -b, --badge      角标数字
  -s, --sound      提示音
  --sandbox        使用沙盒环境
  --payload        自定义JSON payload
```

## 开发说明

### 项目结构
```
push_tools/
├── __init__.py          # 模块初始化
├── apns_push.py         # 核心推送逻辑
├── apns_gui.py          # GUI界面
├── requirements.txt     # 依赖列表
├── test_push.py         # 测试脚本
└── README.md           # 本文档
```

### 扩展开发

1. **添加新的证书格式支持**
   - 在APNSCertificate类中添加加载方法
   - 更新_load_certificate方法

2. **自定义推送模板**
   - 在apns_gui.py的set_payload_template方法中添加

3. **批量推送功能**
   - 扩展APNSPusher类支持多设备
   - 添加并发控制

## 许可证

本工具基于MIT许可证开源。

## 致谢

- 基于SmartPush项目的设计理念
- 集成到mars_log_analyzer项目框架

## 更新日志

### v1.0.0 (2024-09-26)
- 初始版本发布
- 支持基本的推送发送功能
- GUI界面实现
- 历史记录功能