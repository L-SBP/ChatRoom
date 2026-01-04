# 客户端与服务端交互信息的JSON模型总结（更新版）

基于对代码的分析和优化，我总结出了客户端与服务端交互的所有JSON模型，包括请求、响应和数据传输格式。

## 1. 认证相关JSON模型

### 1.1 登录请求
```json
{
  "type": "login",
  "username": "string",
  "password": "string"
}
```

### 1.2 登录成功响应
```json
{
  "type": "login_success",
  "success": true,
  "message": "登录成功",
  "username": "string"
}
```

### 1.3 登录失败响应
```json
{
  "type": "login_failed",
  "success": false,
  "message": "错误信息"
}
```

### 1.4 注册请求
```json
{
  "type": "register",
  "username": "string",
  "password": "string",
  "email": "string",
  "display_name": "string"
}
```

### 1.5 注册成功响应
```json
{
  "type": "register_success",
  "success": true,
  "message": "注册成功"
}
```

### 1.6 注册失败响应
```json
{
  "type": "register_failed",
  "success": false,
  "message": "错误信息"
}
```

### 1.7 注销请求
```json
{
  "type": "logout",
  "username": "string"
}
```

### 1.8 注销成功响应
```json
{
  "type": "logout_success",
  "success": true,
  "message": "注销成功"
}
```

## 2. 消息相关JSON模型（优化版）

### 2.1 文本消息请求
```json
{
  "type": "text",
  "username": "string",
  "content": "string",
  "timestamp": "number"
}
```

### 2.2 图片消息请求
```json
{
  "type": "image",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "number"
}
```

### 2.3 视频消息请求
```json
{
  "type": "video",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "number"
}
```

### 2.4 音频消息请求
```json
{
  "type": "audio",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "number"
}
```

### 2.5 文件消息请求
```json
{
  "type": "file",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "number"
}
```

### 2.6 消息发送成功响应
```json
{
  "type": "message_sent",
  "success": true,
  "message": "消息发送成功"
}
```

### 2.7 广播文本消息
```json
{
  "type": "text",
  "username": "string",
  "content": "string",
  "timestamp": "string"
}
```

### 2.8 广播图片消息
```json
{
  "type": "image",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "string"
}
```

### 2.9 广播视频消息
```json
{
  "type": "video",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "string"
}
```

### 2.10 广播音频消息
```json
{
  "type": "audio",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "string"
}
```

### 2.11 广播文件消息
```json
{
  "type": "file",
  "username": "string",
  "content": "string",
  "filename": "string",
  "data": "base64_encoded_string",
  "size": "number",
  "timestamp": "string"
}
```

### 2.12 系统消息
```json
{
  "type": "system",
  "message": "string",
  "timestamp": "string"
}
```

## 3. 用户管理JSON模型

### 3.1 刷新用户列表请求
```json
{
  "type": "refresh_users",
  "username": "string"
}
```

### 3.2 用户列表响应
```json
{
  "type": "user_list",
  "users": ["user1", "user2", "user3"]
}
```

### 3.3 用户列表刷新成功响应
```json
{
  "type": "user_list_refreshed",
  "success": true,
  "message": "用户列表已刷新"
}
```

## 4. 错误响应JSON模型

### 4.1 通用错误响应
```json
{
  "type": "error",
  "success": false,
  "message": "错误信息"
}
```

## 5. 数据库存储JSON模型

### 5.1 全局消息数据库模型
```json
{
  "message_id": "uuid",
  "user_id": "uuid",
  "content_type": "text|image|video|file|audio|system",
  "content": "string",
  "file_url": "string",
  "file_name": "string",
  "file_size": "string",
  "metadata": {
    "timestamp": "number",
    "is_system": "boolean"
  },
  "is_edited": "boolean",
  "edited_at": "datetime",
  "is_deleted": "boolean",
  "deleted_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 5.2 文件存储数据库模型
```json
{
  "file_id": "uuid",
  "user_id": "uuid",
  "file_name": "string",
  "file_path": "string",
  "file_url": "string",
  "file_type": "string",
  "mime_type": "string",
  "file_size": "string",
  "width": "number",
  "height": "number",
  "duration": "number",
  "thumbnail_url": "string",
  "upload_status": "pending|completed|failed",
  "is_temp": "boolean",
  "expires_at": "datetime",
  "bitrate": "number",
  "sample_rate": "number",
  "channels": "number",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 5.3 用户数据库模型
```json
{
  "user_id": "uuid",
  "username": "string",
  "display_name": "string",
  "avatar_url": "string",
  "password_hash": "string",
  "email": "string",
  "phone": "string",
  "status": "offline|online|busy|away",
  "last_seen": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 6. VO对象JSON模型

### 6.1 用户VO
```json
{
  "user_id": "string",
  "username": "string",
  "password": "string",
  "email": "string",
  "display_name": "string",
  "avatar_url": "string",
  "status": "offline|online|busy|away",
  "last_seen": "datetime"
}
```

### 6.2 消息VO
```json
{
  "message_id": "string",
  "user_id": "string",
  "username": "string",
  "content_type": "text|image|video|file|audio|system",
  "content": "string",
  "display_name": "string",
  "avatar_url": "string",
  "file_vo": "FileVO",
  "is_edited": "boolean",
  "created_at": "datetime"
}
```

### 6.3 文件VO
```json
{
  "file_id": "string",
  "file_name": "string",
  "file_url": "string",
  "file_type": "image|video|audio|file",
  "file_size": "number",
  "width": "number",
  "height": "number",
  "duration": "number",
  "thumbnail_url": "string",
  "created_at": "datetime"
}
```

## 7. 客户端-服务器交互流程

1. **连接建立**: 客户端连接到服务器
2. **认证阶段**: 
   - 客户端发送登录/注册请求
   - 服务器验证并返回响应
3. **消息传输阶段**:
   - 客户端发送消息请求（type字段使用content_type值：text、image、video、file、audio）
   - 服务器根据type字段路由到对应处理器
   - 服务器广播给所有客户端
4. **用户管理**:
   - 客户端请求刷新用户列表
   - 服务器返回当前在线用户
5. **断开连接**: 客户端发送注销请求

## 8. 优化说明

### 主要改进：
1. **统一的消息类型标识**：将客户端请求的 `type` 字段改为与数据库的 `content_type` 保持一致
   - 文本消息：`type: "text"`
   - 图片消息：`type: "image"`
   - 视频消息：`type: "video"`
   - 音频消息：`type: "audio"`
   - 文件消息：`type: "file"`

2. **简化服务端处理**：移除了专门的文件处理器，统一由消息处理器根据 `content_type` 处理不同类型的消息

3. **改进路由映射**：请求分发器的路由映射直接使用消息类型作为键

4. **客户端适配**：客户端发送消息时使用 `message_vo.content_type` 作为 `type` 字段值

### 优势：
- **一致性**：客户端请求、服务端处理、数据库存储使用相同的消息类型标识
- **可扩展性**：新增消息类型只需在路由映射中添加新的处理器映射
- **清晰性**：消息类型一目了然，便于调试和维护
- **标准化**：与数据库模型保持一致，减少类型转换错误

所有JSON消息都通过TCP套接字传输，使用UTF-8编码，支持多条JSON消息的连续传输。

PyQt5==5.15.9
PyQt5-sip==12.11.0
pyyaml>=6.0           # 配置管理
qdarkstyle>=3.0       # 深色主题
python-dotenv>=1.0    # 环境变量
Pillow>=10.0.0        # 图片处理与压缩

pydantic==2.4.2
pydantic-settings==2.1.0

loguru==0.7.2

asyncpg>=0.29.0
sqlalchemy>=2.0.0