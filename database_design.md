```postgresql
-- =============================================
-- 基础配置（PostgreSQL 环境适配）
-- =============================================
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- =============================================
-- 1. 用户表：users
-- 存储用户核心信息（账号、状态、个人信息等）
-- =============================================
CREATE TABLE public.users (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL COMMENT '用户唯一ID（主键）',
    username character varying(50) NOT NULL COMMENT '用户名（唯一）',
    display_name character varying(100) COMMENT '用户昵称',
    avatar_url text COMMENT '用户头像URL',
    password_hash character varying(255) NOT NULL COMMENT '密码哈希值',
    email character varying(100) COMMENT '邮箱（唯一）',
    phone character varying(20) COMMENT '手机号（唯一）',
    status character varying(20) DEFAULT 'offline'::character varying COMMENT '在线状态：offline/online/busy/away',
    last_seen timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '最后上线时间',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 检查约束：状态值合法性
    CONSTRAINT valid_status CHECK (((status)::text = ANY ((ARRAY['offline'::character varying, 'online'::character varying, 'busy'::character varying, 'away'::character varying])::text[]))),
    -- 主键约束
    CONSTRAINT users_pkey PRIMARY KEY (user_id),
    -- 唯一约束
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_phone_key UNIQUE (phone)
);

ALTER TABLE public.users OWNER TO "user";
COMMENT ON TABLE public.users IS '用户核心信息表';

-- =============================================
-- 2. 文件表：files
-- 存储用户上传的文件（图片/视频/音频/文档等）
-- =============================================
CREATE TABLE public.files (
    file_id uuid DEFAULT gen_random_uuid() NOT NULL COMMENT '文件唯一ID（主键）',
    user_id uuid COMMENT '上传用户ID（关联users表）',
    file_name character varying(255) NOT NULL COMMENT '文件名',
    file_path text NOT NULL COMMENT '文件存储路径',
    file_url text NOT NULL COMMENT '文件访问URL',
    file_type character varying(100) COMMENT '文件类型（image/video/audio/file）',
    mime_type character varying(100) COMMENT 'MIME类型（如image/jpeg）',
    file_size bigint COMMENT '文件大小（字节）',
    width integer COMMENT '图片/视频宽度（像素）',
    height integer COMMENT '图片/视频高度（像素）',
    duration integer COMMENT '音视频时长（秒）',
    thumbnail_url text COMMENT '缩略图URL',
    upload_status character varying(20) DEFAULT 'completed'::character varying COMMENT '上传状态：uploading/completed/failed',
    is_temp boolean DEFAULT false COMMENT '是否临时文件',
    expires_at timestamp with time zone COMMENT '临时文件过期时间',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    bitrate integer COMMENT '音视频码率',
    sample_rate integer COMMENT '音频采样率',
    channels integer DEFAULT 1 COMMENT '音频声道数',
    -- 检查约束：上传状态合法性
    CONSTRAINT files_upload_status_check CHECK (((upload_status)::text = ANY ((ARRAY['uploading'::character varying, 'completed'::character varying, 'failed'::character varying])::text[]))),
    -- 主键约束
    CONSTRAINT files_pkey PRIMARY KEY (file_id)
);

ALTER TABLE public.files OWNER TO "user";
COMMENT ON TABLE public.files IS '用户上传文件信息表';

-- =============================================
-- 3. 全局消息表：global_messages
-- 存储公共聊天室的全局消息
-- =============================================
CREATE TABLE public.global_messages (
    message_id uuid DEFAULT gen_random_uuid() NOT NULL COMMENT '消息唯一ID（主键）',
    user_id uuid COMMENT '发送用户ID（关联users表）',
    content_type character varying(20) DEFAULT 'text'::character varying COMMENT '消息类型：text/image/video/file/audio/system',
    content text COMMENT '文本消息内容',
    file_url text COMMENT '文件消息URL（关联files表）',
    file_name character varying(255) COMMENT '文件名',
    file_size bigint COMMENT '文件大小（字节）',
    metadata jsonb COMMENT '扩展元数据（JSON格式）',
    is_edited boolean DEFAULT false COMMENT '是否编辑过',
    edited_at timestamp with time zone COMMENT '编辑时间',
    is_deleted boolean DEFAULT false COMMENT '是否删除（软删）',
    deleted_at timestamp with time zone COMMENT '删除时间',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 检查约束：消息类型合法性
    CONSTRAINT global_messages_content_type_check CHECK (((content_type)::text = ANY ((ARRAY['text'::character varying, 'image'::character varying, 'video'::character varying, 'file'::character varying, 'audio'::character varying, 'system'::character varying])::text[]))),
    -- 主键约束
    CONSTRAINT global_messages_pkey PRIMARY KEY (message_id)
);

ALTER TABLE public.global_messages OWNER TO "user";
COMMENT ON TABLE public.global_messages IS '全局公共消息表';

-- =============================================
-- 4. 私人会话表：private_conversations
-- 存储用户间的一对一私人会话关系
-- =============================================
CREATE TABLE public.private_conversations (
    conversation_id uuid DEFAULT gen_random_uuid() NOT NULL COMMENT '会话唯一ID（主键）',
    user1_id uuid NOT NULL COMMENT '会话用户1 ID（关联users表）',
    user2_id uuid NOT NULL COMMENT '会话用户2 ID（关联users表）',
    last_message_id uuid COMMENT '最后一条消息ID（关联private_messages表）',
    last_message_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '最后一条消息时间',
    unread_count_user1 integer DEFAULT 0 COMMENT '用户1未读消息数',
    unread_count_user2 integer DEFAULT 0 COMMENT '用户2未读消息数',
    is_muted_user1 boolean DEFAULT false COMMENT '用户1是否静音该会话',
    is_muted_user2 boolean DEFAULT false COMMENT '用户2是否静音该会话',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 检查约束：确保user1_id < user2_id，避免重复会话
    CONSTRAINT unique_user_pair CHECK ((user1_id < user2_id)),
    -- 主键约束
    CONSTRAINT private_conversations_pkey PRIMARY KEY (conversation_id),
    -- 唯一约束：用户对唯一
    CONSTRAINT private_conversations_user1_id_user2_id_key UNIQUE (user1_id, user2_id)
);

ALTER TABLE public.private_conversations OWNER TO "user";
COMMENT ON TABLE public.private_conversations IS '用户一对一私人会话关系表';

-- =============================================
-- 5. 私人消息表：private_messages
-- 存储私人会话的具体消息内容
-- =============================================
CREATE TABLE public.private_messages (
    message_id uuid DEFAULT gen_random_uuid() NOT NULL COMMENT '消息唯一ID（主键）',
    conversation_id uuid NOT NULL COMMENT '所属会话ID（关联private_conversations表）',
    sender_id uuid NOT NULL COMMENT '发送者ID（关联users表）',
    receiver_id uuid NOT NULL COMMENT '接收者ID（关联users表）',
    content_type character varying(20) DEFAULT 'text'::character varying COMMENT '消息类型：text/image/video/file/audio/system',
    content text COMMENT '文本消息内容',
    file_url text COMMENT '文件消息URL（关联files表）',
    file_name character varying(255) COMMENT '文件名',
    file_size bigint COMMENT '文件大小（字节）',
    metadata jsonb COMMENT '扩展元数据（JSON格式）',
    is_read boolean DEFAULT false COMMENT '是否已读',
    read_at timestamp with time zone COMMENT '已读时间',
    is_edited boolean DEFAULT false COMMENT '是否编辑过',
    edited_at timestamp with time zone COMMENT '编辑时间',
    is_deleted boolean DEFAULT false COMMENT '是否删除（软删）',
    deleted_at timestamp with time zone COMMENT '删除时间',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 检查约束：消息类型合法性
    CONSTRAINT private_messages_content_type_check CHECK (((content_type)::text = ANY ((ARRAY['text'::character varying, 'image'::character varying, 'video'::character varying, 'file'::character varying, 'audio'::character varying, 'system'::character varying])::text[]))),
    -- 主键约束
    CONSTRAINT private_messages_pkey PRIMARY KEY (message_id)
);

ALTER TABLE public.private_messages OWNER TO "user";
COMMENT ON TABLE public.private_messages IS '私人会话消息内容表';

-- =============================================
-- 索引创建（优化查询性能）
-- =============================================
-- files表索引
CREATE INDEX idx_files_user_id ON public.files USING btree (user_id);
CREATE INDEX idx_files_upload_status ON public.files USING btree (upload_status);
CREATE INDEX idx_files_is_temp ON public.files USING btree (is_temp) WHERE is_temp;
CREATE INDEX idx_files_created_at ON public.files USING btree (created_at DESC);

-- global_messages表索引
CREATE INDEX idx_global_messages_user_id ON public.global_messages USING btree (user_id);
CREATE INDEX idx_global_messages_is_deleted ON public.global_messages USING btree (is_deleted) WHERE (NOT is_deleted);
CREATE INDEX idx_global_messages_created_at ON public.global_messages USING btree (created_at DESC);

-- private_conversations表索引
CREATE INDEX idx_private_conversations_user1 ON public.private_conversations USING btree (user1_id);
CREATE INDEX idx_private_conversations_user2 ON public.private_conversations USING btree (user2_id);
CREATE INDEX idx_private_conversations_last_message_at ON public.private_conversations USING btree (last_message_at DESC);
CREATE INDEX idx_private_conversations_user1_last_message ON public.private_conversations USING btree (user1_id, last_message_at DESC);
CREATE INDEX idx_private_conversations_user2_last_message ON public.private_conversations USING btree (user2_id, last_message_at DESC);

-- private_messages表索引
CREATE INDEX idx_private_messages_conversation_id ON public.private_messages USING btree (conversation_id);
CREATE INDEX idx_private_messages_sender_receiver ON public.private_messages USING btree (sender_id, receiver_id);
CREATE INDEX idx_private_messages_is_read ON public.private_messages USING btree (is_read) WHERE (NOT is_read);
CREATE INDEX idx_private_messages_created_at ON public.private_messages USING btree (created_at DESC);

-- =============================================
-- 外键约束（保证数据关联完整性）
-- =============================================
-- files表 -> users表
ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;

-- global_messages表 -> users表
ALTER TABLE ONLY public.global_messages
    ADD CONSTRAINT global_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;

-- private_conversations表 -> users表（user1）
ALTER TABLE ONLY public.private_conversations
    ADD CONSTRAINT private_conversations_user1_id_fkey FOREIGN KEY (user1_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

-- private_conversations表 -> users表（user2）
ALTER TABLE ONLY public.private_conversations
    ADD CONSTRAINT private_conversations_user2_id_fkey FOREIGN KEY (user2_id) REFERENCES public.users(user_id) ON DELETE CASCADE;

-- private_conversations表 -> private_messages表（最后一条消息）
ALTER TABLE ONLY public.private_conversations
    ADD CONSTRAINT private_conversations_last_message_id_fkey FOREIGN KEY (last_message_id) REFERENCES public.private_messages(message_id) ON DELETE SET NULL;

-- private_messages表 -> users表（发送者）
ALTER TABLE ONLY public.private_messages
    ADD CONSTRAINT private_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(user_id) ON DELETE SET NULL;

-- private_messages表 -> users表（接收者）
ALTER TABLE ONLY public.private_messages
    ADD CONSTRAINT private_messages_receiver_id_fkey FOREIGN KEY (receiver_id) REFERENCES public.users(user_id) ON DELETE SET NULL;
```