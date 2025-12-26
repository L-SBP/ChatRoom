from common.database.models.global_messages import GlobalMessage


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import await_only

from common.database.models import GlobalMessage
from common.log import log


class GlobalMessageCRUD:
    """全局消息CRUD类"""

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        """
        在数据库创建全局消息实例
        """
        message = GlobalMessage(**kwargs)

        try:
            db.add(message)
            await db.commit()
            await db.refresh(message)
            log.info(f"创建全局消息成功: {message}")
            return message
        except Exception as e:
            await db.rollback()
            log.error(f"创建全局消息失败: {e}")
            raise e

    @staticmethod
    async def get_lasted_message(db: AsyncSession, num: int = 50):
        """
        获取最新的num条全局消息
        """
        try:
            # 获取最新的limit条消息，按时间倒序排列
            query = select(GlobalMessage).order_by(GlobalMessage.created_at.desc()).limit(num)
            result = await db.execute(query)
            messages = result.scalars().all()
            messages = list[GlobalMessage](messages)  # 转换为列表以完成查询
            # 反转列表，使其按时间正序排列（最旧的消息在最前面）
            messages.reverse()
            log.info(f"获取最新{num}条全局消息成功: {messages}")
            return messages
        except Exception as e:
            log.error(f"获取最新{num}条全局消息失败: {e}")
            raise e

    @staticmethod
    async def get_before_message(db: AsyncSession, message_id: str, num: int = 50):
        """
        获取这条消息之前的num条消息
        """
        try:
            # 首先根据message_id获取对应消息的时间戳
            current_msg_query = select(GlobalMessage).where(GlobalMessage.message_id == message_id)
            current_msg_result = await db.execute(current_msg_query)
            current_msg = current_msg_result.scalar_one_or_none()
            
            if current_msg is None:
                # 如果找不到对应的消息，返回最新的消息
                return await GlobalMessageCRUD.get_lasted_message(db, num)
            
            # 获取该时间戳之前的消息，按时间倒序排列
            query = select(GlobalMessage).where(
                GlobalMessage.created_at < current_msg.created_at
            ).order_by(GlobalMessage.created_at.desc()).limit(num)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            messages = list(messages)  # 转换为列表以完成查询
            # 反转列表，使其按时间正序排列（最旧的消息在最前面）
            messages.reverse()
            log.info(f"获取这条消息之前的{num}条消息成功: {messages}")
            return messages
        except Exception as e:
            log.error(f"获取这条消息之前的{num}条消息失败: {e}")
            raise e