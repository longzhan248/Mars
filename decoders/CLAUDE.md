# CLAUDE.md - 解码器模块

## 模块概述
Mars xlog文件解码核心实现，支持多种压缩和加密格式。

## 文件说明

### decode_mars_nocrypt_log_file_py3.py (主要)
- **用途**: Python 3标准解码器
- **功能**: 多种压缩格式、加密支持、完整性验证
- **关键函数**: `ParseFile()`, `GetLogStartPos()`, `DecodeBuffer()`

### fast_decoder.py (性能优化)
- **用途**: 高性能解码器
- **特性**: 内存映射、批量处理、比标准版快2-3倍
- **适用**: 大文件(>10MB)、批量处理

### optimized_decoder.py (内存优化)
- **用途**: 内存优化解码器
- **特性**: 流式处理、智能缓冲、支持断点续传
- **适用**: 内存受限环境、超大文件(>100MB)

### decode_mars_nocrypt_log_file.py (遗留)
- **用途**: Python 2兼容版本
- **状态**: 仅保留兼容性，不推荐新功能

## xlog格式要点

### 魔数定义
```python
MAGIC_NO_COMPRESS_START = 0x03       # 未压缩，无加密
MAGIC_COMPRESS_START = 0x05          # 压缩，无加密
MAGIC_COMPRESS_START1 = 0x06         # 压缩，4字节密钥
MAGIC_COMPRESS_START2 = 0x07         # 压缩，64字节密钥
MAGIC_END = 0x00                      # 结束标记
```

### 日志条目结构
`[魔数(1)][序列号(2)][时间(2)][长度(4)][密钥(可选)][数据][MAGIC_END]`

## 使用建议

### 选择解码器
- **标准使用**: `decode_mars_nocrypt_log_file_py3.py`
- **大文件**: `fast_decoder.py`
- **内存受限**: `optimized_decoder.py`

### 常见问题
- **解码失败**: 检查文件完整性、确认版本、查看错误日志
- **性能问题**: 使用fast_decoder、增加缓冲区、SSD存储
- **内存溢出**: 使用optimized_decoder、分批处理

## 开发注意

### 添加新格式
1. 更新魔数定义
2. 修改DecodeBuffer逻辑
3. 实现解压/解密
4. 添加测试

### 性能优化
- I/O: 缓冲读取、减少系统调用
- 内存: 复用缓冲区、及时释放
- CPU: 避免重复计算、使用内置函数

### 错误处理
- 损坏数据: 跳过块、记录位置、尝试恢复
- 格式不兼容: 检测版本、明确错误信息

---

*详细技术实现请参考源码注释和测试用例。*