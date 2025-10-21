#!/usr/bin/env python3
"""
iOS APNS推送工具
基于SmartPush项目功能的Python实现
支持证书管理、推送发送、历史记录等功能
"""

import json
import os
import pickle
import ssl
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID, NameOID


class APNSCertificate:
    """APNS证书管理类"""

    def __init__(self, cert_path: str, password: Optional[str] = None):
        self.cert_path = cert_path
        self.password = password
        self.certificate = None
        self.private_key = None
        self.cert_info = {}
        self._load_certificate()

    def _load_certificate(self):
        """加载证书文件"""
        try:
            # 支持.p12, .pem, .cer等格式
            if self.cert_path.endswith('.p12'):
                self._load_p12()
            elif self.cert_path.endswith('.pem'):
                self._load_pem()
            elif self.cert_path.endswith('.cer'):
                self._load_cer()
            else:
                raise ValueError(f"不支持的证书格式: {self.cert_path}")

            # 提取证书信息
            self._extract_cert_info()

        except Exception as e:
            raise Exception(f"加载证书失败: {str(e)}")

    def _load_p12(self):
        """加载P12格式证书"""
        from cryptography.hazmat.primitives.serialization import pkcs12

        with open(self.cert_path, 'rb') as f:
            p12_data = f.read()

        password = self.password.encode() if self.password else None
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            p12_data, password, default_backend()
        )

        self.private_key = private_key
        self.certificate = certificate

    def _load_pem(self):
        """加载PEM格式证书"""
        from cryptography.hazmat.primitives import serialization

        with open(self.cert_path, 'rb') as f:
            pem_data = f.read()

        # 尝试加载证书
        self.certificate = x509.load_pem_x509_certificate(pem_data, default_backend())

        # 尝试加载私钥
        password = self.password.encode() if self.password else None
        try:
            self.private_key = serialization.load_pem_private_key(
                pem_data, password, default_backend()
            )
        except:
            # 私钥可能在单独的文件中
            pass

    def _load_cer(self):
        """加载CER格式证书"""
        with open(self.cert_path, 'rb') as f:
            cer_data = f.read()

        try:
            # 尝试DER格式
            self.certificate = x509.load_der_x509_certificate(cer_data, default_backend())
        except:
            # 尝试PEM格式
            self.certificate = x509.load_pem_x509_certificate(cer_data, default_backend())

    def _extract_cert_info(self):
        """提取证书信息"""
        if not self.certificate:
            return

        cert = self.certificate

        # 提取基本信息
        self.cert_info = {
            'subject': cert.subject.rfc4514_string(),
            'issuer': cert.issuer.rfc4514_string(),
            'serial_number': str(cert.serial_number),
            'not_valid_before': cert.not_valid_before_utc,
            'not_valid_after': cert.not_valid_after_utc,
            'version': cert.version.name,
        }

        # 提取CN (Common Name)
        try:
            cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            self.cert_info['common_name'] = cn

            # 判断环境 (开发/生产)
            if 'Development' in cn or 'Developer' in cn:
                self.cert_info['environment'] = 'development'
            elif 'Production' in cn or 'Distribution' in cn:
                self.cert_info['environment'] = 'production'
            else:
                self.cert_info['environment'] = 'unknown'

        except:
            self.cert_info['common_name'] = 'Unknown'
            self.cert_info['environment'] = 'unknown'

        # 提取Bundle ID (如果存在)
        try:
            for ext in cert.extensions:
                if ext.oid == ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                    for name in ext.value:
                        if hasattr(name, 'value'):
                            value = name.value
                            if 'com.' in value or 'io.' in value:
                                self.cert_info['bundle_id'] = value
                                break
        except:
            pass

        # 提取UID (User ID)
        try:
            uid_attrs = cert.subject.get_attributes_for_oid(NameOID.USER_ID)
            if uid_attrs:
                self.cert_info['uid'] = uid_attrs[0].value
        except:
            pass

    def is_valid(self) -> bool:
        """检查证书是否有效"""
        if not self.certificate:
            return False

        now = datetime.now()
        return (self.cert_info['not_valid_before'] <= now <=
                self.cert_info['not_valid_after'])

    def days_until_expiry(self) -> int:
        """获取证书过期天数"""
        if not self.certificate:
            return -1

        delta = self.cert_info['not_valid_after'] - datetime.now()
        return delta.days


class APNSConnection:
    """APNS连接管理类"""

    # APNS服务器地址
    APNS_HOST_SANDBOX = 'api.sandbox.push.apple.com'
    APNS_HOST_PRODUCTION = 'api.push.apple.com'
    APNS_PORT = 443

    # Legacy Binary Interface (已弃用但仍可用)
    APNS_LEGACY_HOST_SANDBOX = 'gateway.sandbox.push.apple.com'
    APNS_LEGACY_HOST_PRODUCTION = 'gateway.push.apple.com'
    APNS_LEGACY_PORT = 2195

    def __init__(self, certificate: APNSCertificate, sandbox: bool = True):
        self.certificate = certificate
        self.sandbox = sandbox
        self.connection = None
        self.ssl_context = None

    def _create_ssl_context(self):
        """创建SSL上下文"""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        # 加载证书
        if self.certificate.cert_path.endswith('.pem'):
            context.load_cert_chain(
                self.certificate.cert_path,
                password=self.certificate.password
            )
        else:
            # 需要先转换为PEM格式
            temp_pem = self._convert_to_pem()
            context.load_cert_chain(temp_pem)
            os.remove(temp_pem)

        return context

    def _convert_to_pem(self) -> str:
        """将证书转换为PEM格式"""
        from cryptography.hazmat.primitives import serialization

        temp_file = f"/tmp/temp_cert_{int(time.time())}.pem"

        with open(temp_file, 'wb') as f:
            # 写入证书
            if self.certificate.certificate:
                f.write(self.certificate.certificate.public_bytes(
                    serialization.Encoding.PEM
                ))

            # 写入私钥
            if self.certificate.private_key:
                f.write(self.certificate.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

        return temp_file


class APNSPusher:
    """APNS推送发送器 - 使用HTTP/2协议"""

    def __init__(self, certificate: APNSCertificate, sandbox: bool = True):
        self.certificate = certificate
        self.sandbox = sandbox
        self.base_url = f"https://api{'sandbox.' if sandbox else ''}.push.apple.com"

    def send_push(self,
                  device_token: str,
                  payload: Dict,
                  topic: Optional[str] = None,
                  priority: int = 10,
                  expiration: int = 0,
                  collapse_id: Optional[str] = None,
                  push_type: str = 'alert') -> Tuple[bool, Optional[str]]:
        """
        发送推送通知

        Args:
            device_token: 设备Token
            payload: 推送内容
            topic: 主题(通常是Bundle ID)
            priority: 优先级 (10=立即, 5=省电)
            expiration: 过期时间戳
            collapse_id: 折叠ID
            push_type: 推送类型 (alert, background, voip, complication, fileprovider, mdm)

        Returns:
            (成功标志, 错误信息)
        """

        # 清理device token
        device_token = device_token.replace(' ', '').replace('<', '').replace('>', '')

        # 构建URL
        url = f"{self.base_url}/3/device/{device_token}"

        # 准备请求头
        headers = {
            'apns-push-type': push_type,
            'apns-priority': str(priority),
        }

        if topic:
            headers['apns-topic'] = topic

        if expiration > 0:
            headers['apns-expiration'] = str(expiration)

        if collapse_id:
            headers['apns-collapse-id'] = collapse_id

        # 准备payload
        if isinstance(payload, dict):
            payload_data = json.dumps(payload).encode('utf-8')
        else:
            payload_data = payload.encode('utf-8')

        # 检查payload大小 (最大4KB)
        if len(payload_data) > 4096:
            return False, f"Payload太大: {len(payload_data)} bytes (最大4096)"

        try:
            # 创建临时PEM文件用于请求
            temp_pem = self._prepare_cert_file()

            # 使用httpx发送HTTP/2请求
            with httpx.Client(
                http2=True,
                cert=temp_pem if temp_pem else None,
                verify=False
            ) as client:
                response = client.post(
                    url,
                    content=payload_data,
                    headers=headers,
                    timeout=30.0
                )

            # 清理临时文件
            if temp_pem and os.path.exists(temp_pem):
                os.remove(temp_pem)

            # 处理响应
            if response.status_code == 200:
                return True, None
            else:
                error_data = response.json() if response.content else {}
                error_reason = error_data.get('reason', f'HTTP {response.status_code}')
                return False, error_reason

        except Exception as e:
            return False, str(e)

    def _prepare_cert_file(self) -> Optional[str]:
        """准备证书文件"""
        if not self.certificate.certificate or not self.certificate.private_key:
            return None

        from cryptography.hazmat.primitives import serialization

        temp_file = f"/tmp/apns_cert_{int(time.time())}.pem"

        with open(temp_file, 'wb') as f:
            # 写入私钥
            f.write(self.certificate.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

            # 写入证书
            f.write(self.certificate.certificate.public_bytes(
                serialization.Encoding.PEM
            ))

        return temp_file


class PushHistory:
    """推送历史记录管理"""

    HISTORY_FILE = Path.home() / '.apns_push_history.pkl'
    MAX_HISTORY_SIZE = 1000

    def __init__(self):
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, 'rb') as f:
                    return pickle.load(f)
            except:
                return []
        return []

    def _save_history(self):
        """保存历史记录"""
        # 限制历史记录大小
        if len(self.history) > self.MAX_HISTORY_SIZE:
            self.history = self.history[-self.MAX_HISTORY_SIZE:]

        with open(self.HISTORY_FILE, 'wb') as f:
            pickle.dump(self.history, f)

    def add_record(self,
                   device_token: str,
                   payload: Dict,
                   certificate_name: str,
                   success: bool,
                   error_message: Optional[str] = None,
                   sandbox: bool = True):
        """添加历史记录"""
        record = {
            'timestamp': datetime.now(),
            'device_token': device_token,
            'payload': payload,
            'certificate_name': certificate_name,
            'success': success,
            'error_message': error_message,
            'sandbox': sandbox
        }

        self.history.append(record)
        self._save_history()

    def get_recent(self, count: int = 10) -> List[Dict]:
        """获取最近的历史记录"""
        return self.history[-count:]

    def search_by_token(self, token: str) -> List[Dict]:
        """按设备Token搜索"""
        return [r for r in self.history if token in r['device_token']]

    def clear_all(self):
        """清除所有历史"""
        self.history = []
        self._save_history()


class APNSManager:
    """APNS推送管理器 - 主入口类"""

    def __init__(self):
        self.certificates = {}  # 证书缓存
        self.history = PushHistory()
        self.current_cert = None
        self.current_cert_name = None

    def load_certificate(self, cert_path: str, password: Optional[str] = None) -> bool:
        """加载证书"""
        try:
            cert = APNSCertificate(cert_path, password)

            # 生成证书名称
            cert_name = Path(cert_path).stem
            if cert.cert_info.get('common_name'):
                cert_name = cert.cert_info['common_name']

            # 缓存证书
            self.certificates[cert_name] = cert
            self.current_cert = cert
            self.current_cert_name = cert_name

            return True

        except Exception as e:
            print(f"加载证书失败: {e}")
            return False

    def list_certificates(self) -> List[Dict]:
        """列出所有已加载的证书"""
        certs = []
        for name, cert in self.certificates.items():
            info = {
                'name': name,
                'path': cert.cert_path,
                'valid': cert.is_valid(),
                'days_until_expiry': cert.days_until_expiry(),
                'environment': cert.cert_info.get('environment', 'unknown'),
                'bundle_id': cert.cert_info.get('bundle_id', 'unknown')
            }
            certs.append(info)
        return certs

    def send_push(self,
                  device_token: str,
                  alert_message: str = None,
                  badge: Optional[int] = None,
                  sound: str = 'default',
                  custom_data: Optional[Dict] = None,
                  sandbox: bool = True,
                  **kwargs) -> Tuple[bool, Optional[str]]:
        """
        发送推送 - 简化接口

        Args:
            device_token: 设备Token
            alert_message: 推送消息
            badge: 角标数字
            sound: 声音
            custom_data: 自定义数据
            sandbox: 是否使用沙盒环境
            **kwargs: 其他APNS参数

        Returns:
            (成功标志, 错误信息)
        """

        if not self.current_cert:
            return False, "未加载证书"

        # 构建payload
        payload = {'aps': {}}

        if alert_message:
            payload['aps']['alert'] = alert_message

        if badge is not None:
            payload['aps']['badge'] = badge

        if sound:
            payload['aps']['sound'] = sound

        # 添加自定义数据
        if custom_data:
            payload.update(custom_data)

        # 发送推送
        pusher = APNSPusher(self.current_cert, sandbox)
        success, error = pusher.send_push(
            device_token,
            payload,
            topic=kwargs.get('topic', self.current_cert.cert_info.get('bundle_id')),
            priority=kwargs.get('priority', 10),
            expiration=kwargs.get('expiration', 0),
            collapse_id=kwargs.get('collapse_id'),
            push_type=kwargs.get('push_type', 'alert')
        )

        # 记录历史
        self.history.add_record(
            device_token,
            payload,
            self.current_cert_name,
            success,
            error,
            sandbox
        )

        return success, error

    def send_custom_payload(self,
                           device_token: str,
                           payload: Dict,
                           sandbox: bool = True,
                           **kwargs) -> Tuple[bool, Optional[str]]:
        """发送自定义payload"""
        if not self.current_cert:
            return False, "未加载证书"

        pusher = APNSPusher(self.current_cert, sandbox)
        success, error = pusher.send_push(device_token, payload, **kwargs)

        # 记录历史
        self.history.add_record(
            device_token,
            payload,
            self.current_cert_name,
            success,
            error,
            sandbox
        )

        return success, error

    def get_history(self, count: int = 10) -> List[Dict]:
        """获取历史记录"""
        return self.history.get_recent(count)


# 命令行工具
def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='iOS APNS推送工具')
    parser.add_argument('--cert', '-c', required=True, help='证书文件路径')
    parser.add_argument('--password', '-p', help='证书密码')
    parser.add_argument('--token', '-t', required=True, help='设备Token')
    parser.add_argument('--message', '-m', default='Test notification', help='推送消息')
    parser.add_argument('--badge', '-b', type=int, help='角标数字')
    parser.add_argument('--sound', '-s', default='default', help='提示音')
    parser.add_argument('--sandbox', action='store_true', help='使用沙盒环境')
    parser.add_argument('--payload', help='自定义JSON payload')

    args = parser.parse_args()

    # 初始化管理器
    manager = APNSManager()

    # 加载证书
    if not manager.load_certificate(args.cert, args.password):
        print("证书加载失败")
        return 1

    # 发送推送
    if args.payload:
        # 使用自定义payload
        try:
            payload = json.loads(args.payload)
            success, error = manager.send_custom_payload(
                args.token,
                payload,
                sandbox=args.sandbox
            )
        except json.JSONDecodeError:
            print("无效的JSON payload")
            return 1
    else:
        # 使用简单接口
        success, error = manager.send_push(
            args.token,
            alert_message=args.message,
            badge=args.badge,
            sound=args.sound,
            sandbox=args.sandbox
        )

    if success:
        print("✅ 推送发送成功")
        return 0
    else:
        print(f"❌ 推送发送失败: {error}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())