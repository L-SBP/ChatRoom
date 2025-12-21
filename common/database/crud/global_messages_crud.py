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
            query = select(GlobalMessage).order_by(GlobalMessage.created_at.desc()).limit(num)
            result = await db.execute(query)
            messages = await_only(result.scalars().all())
            log.info(f"获取最新{num}条全局消息成功: {messages}")
            return messages
        except Exception as e:
            log.error(f"获取最新{num}条全局消息失败: {e}")
            raise e

    @staticmethod
    async def get_before_message(db: AsyncSession, message_id: int, num: int = 50):
        """
        获取这条消息之前的num条消息
        """
        try:
            query = select(GlobalMessage).where(GlobalMessage.message_id < message_id).order_by(GlobalMessage.message_id.desc()).limit(num)
            result = await db.execute(query)
            messages = await_only(result.scalars().all())
            log.info(f"获取这条消息之前的{num}条消息成功: {messages}")
            return messages
        except Exception as e:
            log.error(f"获取这条消息之前的{num}条消息失败: {e}")
            raise e