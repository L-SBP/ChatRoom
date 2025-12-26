#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络管理器
负责客户端与服务器之间的网络通信
"""

from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import socket
import json
import time
import os
import base64
from datetime import datetime
from io import BytesIO

# 尝试导入Pillow库用于图片压缩
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from client.models.vo import MessageVO, FileVO, UserVO
from common.log import client_log as log


class NetworkThread(QThread):
    """网络通信线程类，负责与服务器通信"""
    # 信号定义
    message_received = pyqtSignal(object)      # 接收到的消息(VO对象)
    user_list_updated = pyqtSignal(list)       # 用户列表更新
    connection_status = pyqtSignal(bool, str)  # 连接状态, 消息
    file_received = pyqtSignal(str, str)       # 文件名, 文件路径
    login_response = pyqtSignal(bool, str)     # 登录响应(成功/失败, 消息)
    register_response = pyqtSignal(bool, str)  # 注册响应(成功/失败, 消息)
    system_message = pyqtSignal(str)           # 系统消息
    
    def __init__(self, server_host: str, server_port: int):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.buffer_size = 1024
        self.username = None
        self._recv_buffer = b""  # 添加接收缓冲区
        
    def run(self):
        try:
            # 创建TCP连接
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            # 连接到服务器
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.running = True
            self.connection_status.emit(True, "连接成功")
            
            # 开始接收消息
            while self.running:
                try:
                    datas = self.receive_data()
                    if datas:
                        for data in datas:
                            self.handle_message(data)
                    else:
                        # 没有数据，可能是连接断开
                        # 添加延迟以避免空循环占用CPU
                        time.sleep(0.01)
                except socket.timeout:
                    # 超时，继续循环
                    continue
                except ConnectionResetError:
                    # 连接被重置
                    self.connection_status.emit(False, "连接被服务器重置")
                    break
                except OSError as e:
                    # 套接字错误
                    self.connection_status.emit(False, f"套接字错误: {str(e)}")
                    break
                except Exception as e:
                    # 其他异常
                    self.connection_status.emit(False, f"接收数据时出错: {str(e)}")
                    break
        except ConnectionRefusedError:
            self.connection_status.emit(False, "连接被拒绝，请检查服务器是否运行")
        except socket.timeout:
            self.connection_status.emit(False, "连接超时，请检查服务器地址和端口")
        except Exception as e:
            self.connection_status.emit(False, f"连接失败: {str(e)}")
        finally:
            self.close_connection()
    
    def handle_message(self, data: dict):
        """处理接收到的消息"""
        log.debug(f"网络层接收到原始数据: {data}")
        msg_type = data.get('type')
        
        if msg_type in ['text', 'image', 'video', 'file', 'audio']:
            username = data.get('username', '')
            content = data.get('content', '')
            content_type = msg_type
            timestamp = data.get('timestamp', time.time())
            
            # 确保timestamp是数值类型
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                except ValueError:
                    timestamp = time.time()
            
            # 如果是文件类型消息，需要处理文件数据
            file_vo = None
            if content_type in ['image', 'video', 'audio', 'file']:
                filename = data.get('filename', '')
                file_url = data.get('file_url', '')
                file_size = data.get('size', 0)
                if isinstance(file_size, str):
                    try:
                        file_size = int(file_size)
                    except ValueError:
                        file_size = 0
                
                # 创建文件VO对象
                file_vo = FileVO(
                    file_id=data.get('file_id', ''),
                    file_name=filename,
                    file_url=file_url,
                    file_type=content_type,
                    file_size=file_size,
                    created_at=datetime.fromtimestamp(timestamp) if timestamp else None
                )
                
                # 如果是服务器转发的消息且有file_data，则保存文件
                file_data = data.get('data', '')
                if file_data:
                    # 保存文件
                    file_path = self.save_file(filename, file_data)
                    if file_path:
                        # 更新file_vo的file_url为本地保存路径
                        file_vo.file_url = file_path
                        # 发送文件接收信号
                        self.file_received.emit(filename, file_path)
            
            # 创建消息VO对象用于界面展示
            message_vo = MessageVO(
                message_id=data.get('message_id', ''),
                user_id=data.get('user_id', ''),
                username=username,
                content_type=content_type,
                content=content,
                file_vo=file_vo,
                created_at=datetime.fromtimestamp(timestamp) if timestamp else None
            )
            
            self.message_received.emit(message_vo)
            
        elif msg_type == 'user_list':
            users = data.get('users', [])
            self.user_list_updated.emit(users)
            
        elif msg_type == 'system':
            # 处理系统消息
            message = data.get('message', '')
            timestamp = data.get('timestamp', time.time())
            
            # 确保timestamp是数值类型
            if isinstance(timestamp, str):
                try:
                    # 如果是时间字符串格式如'15:35:49'，我们需要转换为时间戳
                    if ':' in timestamp:
                        # 将时间字符串转换为当日的时间戳
                        import datetime as dt_module
                        current_date = dt_module.date.today()
                        time_obj = dt_module.datetime.strptime(timestamp, '%H:%M:%S').time()
                        dt = dt_module.datetime.combine(current_date, time_obj)
                        timestamp = dt.timestamp()
                    else:
                        timestamp = float(timestamp)
                except ValueError:
                    timestamp = time.time()
            
            # 创建系统消息VO对象
            message_vo = MessageVO(
                message_id="",
                user_id="",
                username="系统",
                content_type="system",
                content=message,
                created_at=datetime.fromtimestamp(timestamp) if timestamp else None
            )
            
            log.debug(f"网络层处理系统消息: {message_vo}")
            # 只发送系统消息VO对象，不要同时发送系统消息信号，避免重复
            self.message_received.emit(message_vo)
            
        elif msg_type == 'file':
            filename = data.get('filename', '')
            file_data = data.get('data', '')
            # 确保file_size是整数类型
            file_size = data.get('size', 0)
            if isinstance(file_size, str):
                try:
                    file_size = int(file_size)
                except ValueError:
                    file_size = 0
            
            # 保存文件
            file_path = self.save_file(filename, file_data)
            if file_path:
                self.file_received.emit(filename, file_path)
                
        elif msg_type == 'login_success':
            self.username = data.get('username', '')
            # 设置连接状态为已连接
            self.connection_status.emit(True, "登录成功")
            self.login_response.emit(True, "登录成功")
            
        elif msg_type == 'login_failed':
            self.login_response.emit(False, data.get('message', '登录失败'))
            
        elif msg_type == 'register_success':
            self.register_response.emit(True, "注册成功")
            
        elif msg_type == 'register_failed':
            self.register_response.emit(False, data.get('message', '注册失败'))
            
        elif msg_type == 'get_history':
            # 处理历史消息响应
            success = data.get('success', False)
            messages = data.get('messages', [])
            
            if success and messages:
                message_vos = []
                for msg in messages:
                    # 转换时间戳
                    timestamp_str = msg.get('timestamp')
                    created_at = None
                    if timestamp_str:
                        try:
                            # 如果是ISO格式的时间字符串，直接解析
                            if isinstance(timestamp_str, str):
                                created_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                # 如果是时间戳，转换为datetime对象
                                created_at = datetime.fromtimestamp(timestamp_str)
                        except ValueError:
                            # 如果解析失败，使用当前时间
                            created_at = datetime.now()
                    
                    # 处理文件类型消息
                    file_vo = None
                    content_type = msg.get('content_type', 'text')
                    if content_type in ['image', 'video', 'audio', 'file']:
                        filename = msg.get('file_name', '') or msg.get('filename', '')
                        file_size = msg.get('file_size', 0)
                        if isinstance(file_size, str):
                            try:
                                file_size = int(file_size)
                            except ValueError:
                                file_size = 0
                    
                        # 创建文件VO对象
                        file_vo = FileVO(
                            file_id=msg.get('file_id', ''),
                            file_name=filename,
                            file_url=msg.get('file_url', ''),
                            file_type=content_type,
                            file_size=file_size,
                            created_at=created_at
                        )
                        
                        # 尝试从本地下载目录查找文件
                        if filename:
                            # 构建本地文件路径（与save_file方法一致）
                            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ChatRoom')
                            local_file_path = os.path.join(download_dir, filename)
                            if os.path.exists(local_file_path):
                                # 如果本地文件存在，更新file_url为本地路径
                                file_vo.file_url = local_file_path
                    
                    # 创建消息VO对象
                    message_vo = MessageVO(
                        message_id=msg.get('message_id', ''),
                        user_id='',
                        username=msg.get('username', ''),
                        content_type=content_type,
                        content=msg.get('content', ''),
                        file_vo=file_vo,
                        created_at=created_at
                    )
                    message_vos.append(message_vo)
                
                # 发送历史消息信号
                self.message_received.emit(message_vos)
            else:
                # 如果没有历史消息，发送空列表
                self.message_received.emit([])
    
    def login(self, username: str, password: str) -> None:
        """发送登录请求"""
        log.debug(f"NetworkThread.login 开始发送登录请求: 用户名={username}, running={self.running}, client_socket={self.client_socket}")
        if self.client_socket and self.running:
            login_data = {
                'type': 'login',
                'username': username,
                'password': password
            }
            log.debug(f"NetworkThread.login 发送登录数据: {login_data}")
            self.send_data(login_data)
            log.debug(f"NetworkThread.login 登录请求发送完成")
        else:
            log.error(f"NetworkThread.login 登录请求发送失败: client_socket={self.client_socket}, running={self.running}")
    
    def register(self, user_vo: UserVO) -> None:
        """发送注册请求"""
        if self.client_socket and self.running:
            data = user_vo.to_dict()
            data['type'] = 'register'

            self.send_data(data)
    
    def send_message(self, message_vo: MessageVO) -> bool:
        """发送消息"""
        if self.client_socket and self.running:
            # 将VO对象转换为字典进行传输
            data = message_vo.to_dict()
            data['type'] = message_vo.content_type  # 使用content_type作为type字段
            
            self.send_data(data)
            return True
        return False
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        log.debug(f"NetworkThread.send_file 开始发送文件: {file_path}")
        
        if not self.client_socket or not self.running:
            log.error("NetworkThread.send_file 发送失败: 未连接到服务器")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 检查文件大小
            max_file_size = 10 * 1024 * 1024  # 10MB
            if len(file_data) > max_file_size:
                log.error(f"NetworkThread.send_file 文件大小超过限制: {len(file_data)} > {max_file_size}")
                return False
            
            # 图片压缩处理
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] and PIL_AVAILABLE:
                log.info(f"NetworkThread.send_file 开始压缩图片: {file_path}")
                
                # 使用Pillow进行图片压缩
                try:
                    # 打开图片
                    image = Image.open(BytesIO(file_data))
                    
                    # 获取原始尺寸
                    original_width, original_height = image.size
                    log.debug(f"NetworkThread.send_file 原始图片尺寸: {original_width}x{original_height}")
                    
                    # 计算压缩后的尺寸（保持宽高比，最大边不超过800px）
                    max_size = 800
                    # 即使图片尺寸小于max_size，也进行一定比例的压缩（如果是大图的话）
                    if original_width > max_size or original_height > max_size:
                        ratio = max_size / max(original_width, original_height)
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                    elif original_width > 600 or original_height > 600:
                        # 对于600-800px的图片，进行轻微压缩
                        ratio = 0.8  # 缩小20%
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                    else:
                        # 对于小于600px的图片，保持尺寸不变，只进行质量压缩
                        new_width, new_height = original_width, original_height
                    
                    # 调整图片大小（如果需要的话）
                    if new_width != original_width or new_height != original_height:
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        log.debug(f"NetworkThread.send_file 压缩后图片尺寸: {new_width}x{new_height}")
                    
                    # 保存压缩后的图片到BytesIO对象
                    compressed_buffer = BytesIO()
                    
                    # 根据文件类型设置保存格式和压缩参数
                    if file_extension in ['.jpg', '.jpeg']:
                        # JPEG格式可以设置质量，降低质量以提高压缩率
                        image.save(compressed_buffer, format='JPEG', quality=75, optimize=True, progressive=True)
                    elif file_extension == '.png':
                        # PNG格式可以设置压缩级别，提高压缩级别以获得更好的压缩效果
                        image.save(compressed_buffer, format='PNG', compress_level=9, optimize=True)
                    elif file_extension == '.gif':
                        # GIF格式
                        image.save(compressed_buffer, format='GIF', optimize=True)
                    else:
                        # 其他格式使用默认设置
                        image.save(compressed_buffer, format=image.format, optimize=True)
                    
                    # 获取压缩后的文件数据
                    compressed_data = compressed_buffer.getvalue()
                    
                    # 计算压缩率
                    original_size = len(file_data)
                    compressed_size = len(compressed_data)
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    
                    log.info(f"NetworkThread.send_file 图片压缩完成: 原始大小 {original_size/1024:.1f}KB -> 压缩后 {compressed_size/1024:.1f}KB ({compression_ratio:.1f}% 压缩率)")
                    
                    # 使用压缩后的数据
                    file_data = compressed_data
                    
                except Exception as e:
                    log.error(f"NetworkThread.send_file 图片压缩失败: {e}")
                    # 压缩失败时继续使用原始数据
                    pass
            
            filename = os.path.basename(file_path)
            log.info(f"NetworkThread.send_file 发送文件: {filename}, 大小: {len(file_data)} 字节")
            
            # 判断文件类型
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                file_type = 'image'
            elif file_extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv']:
                file_type = 'video'
            elif file_extension in ['.mp3', '.wav', '.ogg', '.aac']:
                file_type = 'audio'
            else:
                file_type = 'file'
            
            log.debug(f"NetworkThread.send_file 文件类型: {file_type}, 扩展名: {file_extension}")
            
            # 创建文件VO对象
            file_vo = FileVO(
                file_id="",  # 会在服务端生成
                file_name=filename,
                file_url="",  # 会在服务端生成
                file_type=file_type,
                file_size=len(file_data),  # 确保是整数类型
                created_at=datetime.now()
            )
            
            # 将VO对象转换为字典进行传输
            data = {
                'type': file_type,  # 根据文件类型发送不同类型
                'username': self.username,  # 添加用户名信息
                'filename': filename,  # 服务器期望的字段名
                'data': base64.b64encode(file_data).decode('utf-8'),  # 使用base64编码
                'size': len(file_data)  # 确保是整数类型
            }
            
            log.debug(f"NetworkThread.send_file 准备发送数据: {file_type} 类型, 用户名: {self.username}")
            self.send_data(data)
            log.info(f"NetworkThread.send_file 文件发送成功: {filename}")
            return True
        except Exception as e:
            log.error(f"NetworkThread.send_file 发送文件失败: {e}")
            return False
    
    def send_data(self, data: dict):
        """发送数据到服务器"""
        if self.client_socket:
            try:
                log.debug(f"NetworkThread发送数据: {data}")
                json_data = json.dumps(data)
                self.client_socket.send(json_data.encode('utf-8'))
                log.debug(f"NetworkThread数据发送成功: {data['type']}")
            except Exception as e:
                log.error(f"NetworkThread发送数据失败: {e}")
                self.connection_status.emit(False, f"发送数据失败: {str(e)}")
    
    def get_history_messages(self, message_id: str = None, limit: int = 50):
        """获取历史消息"""
        log.debug(f"NetworkThread.get_history_messages被调用: client_socket={self.client_socket}, running={self.running}")
        if self.client_socket and self.running:
            data = {
                'type': 'get_history',
                'message_id': message_id,
                'limit': limit
            }
            log.debug(f"NetworkThread.get_history_messages: 准备发送请求数据: {data}")
            self.send_data(data)
            log.debug(f"NetworkThread.get_history_messages: 请求数据已发送到send_data方法")
        else:
            log.debug(f"NetworkThread.get_history_messages: client_socket或running条件不满足，无法发送请求")
    
    def receive_data(self) -> Optional[list]:
        """从服务器接收数据"""
        if self.client_socket and self.running:
            try:
                # 接收更多数据
                chunk = self.client_socket.recv(self.buffer_size)
                if not chunk:
                    # 连接已关闭
                    return None
                    
                self._recv_buffer += chunk
                
                # 尝试解析缓冲区中的所有完整JSON对象
                results = []
                while True:
                    try:
                        # 尝试解析当前缓冲区中的数据
                        decoded_data = self._recv_buffer.decode('utf-8')
                        
                        # 尝试找到第一个完整的JSON对象
                        obj, index = self._extract_json_object(decoded_data)
                        if obj is not None:
                            results.append(obj)
                            # 正确更新缓冲区：使用已解析的字符串长度对应的字节数
                            # 将已解析的字符串转换回字节，获取正确的字节长度
                            parsed_bytes = decoded_data[:index].encode('utf-8')
                            self._recv_buffer = self._recv_buffer[len(parsed_bytes):]
                        else:
                            # 没有找到完整的JSON对象，退出循环
                            break
                    except UnicodeDecodeError:
                        # 如果解码失败，继续接收更多数据
                        break
                    except Exception as e:
                        print(f"JSON解析失败: {e}")
                        # 清空缓冲区以避免持续错误
                        self._recv_buffer = b""
                        break
                
                return results if results else None
                    
            except socket.timeout:
                # 超时是正常的，继续下一次循环
                pass
            except OSError as e:
                # 套接字错误，可能是连接已关闭
                if e.errno == 10038:  # 在一个非套接字上尝试了一个操作
                    self.connection_status.emit(False, "连接已断开")
                    self.running = False
                else:
                    print(f"套接字错误: {e}")
                return None
            except Exception as e:
                print(f"接收数据失败: {e}")
                # 清空缓冲区以避免持续错误
                self._recv_buffer = b""
        return None
    
    def _extract_json_object(self, text):
        """从文本中提取第一个完整的JSON对象"""
        brace_count = 0
        in_string = False
        escape_next = False
        start_index = -1
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"':
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    if brace_count == 0:
                        start_index = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_index != -1:
                        # 找到完整的JSON对象
                        json_text = text[start_index:i+1]
                        try:
                            obj = json.loads(json_text)
                            return obj, i + 1
                        except json.JSONDecodeError:
                            # 如果解析失败，继续查找下一个对象
                            pass
        
        # 没有找到完整的JSON对象
        return None, 0
    
    def save_file(self, filename: str, file_data: str) -> Optional[str]:
        """
        保存接收到的文件
        """
        log.debug(f"NetworkThread.save_file 开始保存文件: {filename}")
        
        try:
            # 创建接收文件目录
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ChatRoom')
            os.makedirs(download_dir, exist_ok=True)
            log.debug(f"NetworkThread.save_file 保存目录: {download_dir}")
            
            file_path = os.path.join(download_dir, filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(download_dir, f"{name}_{timestamp}{ext}")
                log.debug(f"NetworkThread.save_file 文件已存在，使用新文件名: {os.path.basename(file_path)}")
            
            # 对Base64编码的文件数据进行解码
            decoded_data = base64.b64decode(file_data)
            
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            
            log.info(f"NetworkThread.save_file 文件保存成功: {os.path.basename(file_path)}, 保存路径: {file_path}")
            return file_path
        except Exception as e:
            log.error(f"NetworkThread.save_file 保存文件失败: {e}")
            return None
    
    def close_connection(self):
        """关闭连接"""
        if not self.running:
            return  # 如果已经停止，直接返回
        
        self.running = False
        if self.client_socket:
            try:
                # 发送退出消息
                logout_data = {'type': 'logout'}
                self.send_data(logout_data)
            except:
                pass  # 忽略发送登出消息的错误
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        # 清空接收缓冲区
        self._recv_buffer = b""


class NetworkManager(QObject):
    """网络管理器类（单例模式）"""
    
    # 信号定义
    message_received = pyqtSignal(object)      # 接收到的消息(VO对象)
    user_list_updated = pyqtSignal(list)       # 用户列表更新
    connection_status = pyqtSignal(bool, str)  # 连接状态, 消息
    file_received = pyqtSignal(str, str)       # 文件名, 文件路径
    login_response = pyqtSignal(bool, str)     # 登录响应(成功/失败, 消息)
    register_response = pyqtSignal(bool, str)  # 注册响应(成功/失败, 消息)
    system_message = pyqtSignal(str)           # 系统消息
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            super().__init__()
            self.network_thread: Optional[NetworkThread] = None
            self.connected = False
            self.server_host = None
            self.server_port = None
            self.username = None
            self._initialized = True
    
    def connect_to_server(self, server_host: str, server_port: int) -> bool:
        """连接到服务器"""
        # 如果已有连接，先断开
        if self.network_thread and self.network_thread.isRunning():
            self.disconnect_from_server()
            
        self.server_host = server_host
        self.server_port = server_port
        
        # 启动网络线程
        self.network_thread = NetworkThread(server_host, server_port)
        self.network_thread.message_received.connect(self.on_message_received)
        self.network_thread.user_list_updated.connect(self.on_user_list_updated)
        self.network_thread.connection_status.connect(self.on_connection_status)
        self.network_thread.file_received.connect(self.on_file_received)
        self.network_thread.login_response.connect(self.on_login_response)
        self.network_thread.register_response.connect(self.on_register_response)
        self.network_thread.system_message.connect(self.on_system_message)
        self.network_thread.start()
        
        return True
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return (self.network_thread is not None and 
                self.network_thread.isRunning() and 
                self.connected)
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        if self.network_thread:
            self.network_thread.close_connection()
            # 等待线程结束
            if self.network_thread.isRunning():
                self.network_thread.wait(3000)  # 最多等待3秒
            self.network_thread = None
        self.connected = False
        self.username = None
    
    def login(self, username: str, password: str) -> None:
        """用户登录"""
        if self.network_thread and self.network_thread.running:
            self.network_thread.login(username, password)
        else:
            self.login_response.emit(False, "未连接到服务器")
    
    def register(self, user_vo: UserVO) -> None:
        """用户注册"""
        if self.network_thread and self.network_thread.running:
            self.network_thread.register(user_vo)
        else:
            self.register_response.emit(False, "未连接到服务器")
    
    def send_message(self, message_vo: MessageVO) -> bool:
        """发送消息"""
        if self.network_thread and self.connected:
            return self.network_thread.send_message(message_vo)
        return False
    
    def send_file(self, file_path: str) -> bool:
        """发送文件"""
        if self.network_thread and self.connected:
            return self.network_thread.send_file(file_path)
        return False
    
    def send_data(self, data: dict):
        """发送数据到服务器"""
        if self.network_thread and self.connected:
            self.network_thread.send_data(data)
    
    def get_history_messages(self, message_id: str = None, limit: int = 50):
        """获取历史消息"""
        log.debug(f"NetworkManager.get_history_messages被调用: is_connected={self.is_connected()}, network_thread={self.network_thread}, network_thread.isRunning={self.network_thread.isRunning() if self.network_thread else False}, connected={self.connected}")
        if self.is_connected():
            self.network_thread.get_history_messages(message_id, limit)
            log.debug(f"NetworkManager.get_history_messages: 请求已发送到network_thread")
            return True
        else:
            log.debug(f"NetworkManager.get_history_messages: 连接未建立，请求发送失败")
            return False
    
    def on_message_received(self, message_vo):
        """处理接收到的消息"""
        self.message_received.emit(message_vo)
    
    def on_user_list_updated(self, users: list):
        """处理用户列表更新"""
        self.user_list_updated.emit(users)
    
    def on_connection_status(self, success: bool, message: str):
        """处理连接状态变化"""
        self.connected = success
        self.connection_status.emit(success, message)
    
    def on_file_received(self, filename: str, file_path: str):
        """处理接收到的文件"""
        self.file_received.emit(filename, file_path)
    
    def on_login_response(self, success: bool, message: str):
        """处理登录响应"""
        if success:
            # 可以在这里保存用户名等信息
            self.connected = True  # 设置连接状态为已连接
        self.login_response.emit(success, message)
    
    def on_register_response(self, success: bool, message: str):
        """处理注册响应"""
        self.register_response.emit(success, message)

    def on_system_message(self, message: str):
        """处理系统消息"""
        self.system_message.emit(message)
