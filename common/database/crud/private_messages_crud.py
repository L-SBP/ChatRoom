from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.models.private_messages import PrivateMessage
from common.log import log


class PrivateMessageCRUD:
    """私聊消息CRUD类"""

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        """
        在数据库创建私聊消息实例
        """
        message = PrivateMessage(**kwargs)

        try:
            db.add(message)
            await db.commit()
            await db.refresh(message)
            log.info(f"创建私聊消息成功: {message}")
            return message
        except Exception as e:
            await db.rollback()
            log.error(f"创建私聊消息失败: {e}")
            raise e

    @staticmethod
    async def get_by_conversation(db: AsyncSession, conversation_id: str, limit: int = 50):
        """
        根据会话ID获取最新的limit条私聊消息
        """
        try:
            # 获取最新的limit条消息，按时间倒序排列
            query = select(PrivateMessage).where(
                PrivateMessage.conversation_id == conversation_id
            ).order_by(PrivateMessage.created_at.desc()).limit(limit)
            result = await db.execute(query)
            messages = result.scalars().all()
            messages = list(messages)  # 转换为列表以完成查询
            # 反转列表，使其按时间正序排列（最旧的消息在最前面）
            messages.reverse()
            log.info(f"获取会话 {conversation_id} 的最新{limit}条消息成功: {messages}")
            return messages
        except Exception as e:
            log.error(f"获取会话 {conversation_id} 的最新{limit}条消息失败: {e}")
            raise e

    @staticmethod
    async def get_by_conversation_id(db: AsyncSession, conversation_id: str, limit: int = 50):
        """
        根据会话ID获取最新的limit条私聊消息（兼容方法）
        """
        return await PrivateMessageCRUD.get_by_conversation(db, conversation_id, limit)

    @staticmethod
    async def mark_as_read(db: AsyncSession, message_id: str):
        """
        将指定消息标记为已读
        """
        try:
            query = select(PrivateMessage).where(PrivateMessage.message_id == message_id)
            result = await db.execute(query)
            message = result.scalar_one_or_none()
            
            if message:
                message.is_read = True
                await db.commit()
                await db.refresh(message)
                log.info(f"消息 {message_id} 已标记为已读")
                return message
            return None
        except Exception as e:
            await db.rollback()
            log.error(f"标记消息 {message_id} 为已读失败: {e}")
            raise e
