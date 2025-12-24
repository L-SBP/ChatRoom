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
from datetime import datetime

from client.models.vo import MessageVO, FileVO, UserVO


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
        from common.log import log
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
            
            # 创建消息VO对象用于界面展示
            message_vo = MessageVO(
                message_id=data.get('message_id', ''),
                user_id=data.get('user_id', ''),
                username=username,
                content_type=content_type,
                content=content,
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
    
    def login(self, username: str, password: str) -> None:
        """发送登录请求"""
        if self.client_socket and self.running:
            login_data = {
                'type': 'login',
                'username': username,
                'password': password
            }
            self.send_data(login_data)
    
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
        if not self.client_socket or not self.running:
            return False
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 检查文件大小
            max_file_size = 10 * 1024 * 1024  # 10MB
            if len(file_data) > max_file_size:
                print(f"文件大小超过限制: {len(file_data)} > {max_file_size}")
                return False
            
            filename = os.path.basename(file_path)
            
            # 创建文件VO对象
            file_vo = FileVO(
                file_id="",  # 会在服务端生成
                file_name=filename,
                file_url="",  # 会在服务端生成
                file_type="file",
                file_size=len(file_data),  # 确保是整数类型
                created_at=datetime.now()
            )
            
            # 将VO对象转换为字典进行传输
            data = file_vo.to_dict()
            data.update({
                'type': 'file',
                'data': file_data.decode('latin-1'),  # 转换为字符串传输
                'size': len(file_data)  # 确保是整数类型
            })
            
            self.send_data(data)
            return True
        except Exception as e:
            print(f"发送文件失败: {e}")
            return False
    
    def send_data(self, data: dict):
        """发送数据到服务器"""
        if self.client_socket:
            try:
                json_data = json.dumps(data)
                self.client_socket.send(json_data.encode('utf-8'))
            except Exception as e:
                print(f"发送数据失败: {e}")
                self.connection_status.emit(False, f"发送数据失败: {str(e)}")
    
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
        """保存接收到的文件"""
        try:
            # 创建接收文件目录
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'ChatRoom')
            os.makedirs(download_dir, exist_ok=True)
            
            file_path = os.path.join(download_dir, filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                file_path = os.path.join(download_dir, f"{name}_{timestamp}{ext}")
            
            with open(file_path, 'wb') as f:
                f.write(file_data.encode('latin-1'))
            
            return file_path
        except Exception as e:
            print(f"保存文件失败: {e}")
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
