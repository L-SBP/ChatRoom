from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.models.private_conversations import PrivateConversation
from common.log import log


class PrivateConversationCRUD:
    """私聊会话CRUD类"""

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        """
        在数据库创建私聊会话实例
        """
        conversation = PrivateConversation(**kwargs)

        try:
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            log.info(f"创建私聊会话成功: {conversation}")
            return conversation
        except Exception as e:
            await db.rollback()
            log.error(f"创建私聊会话失败: {e}")
            raise e

    @staticmethod
    async def get_by_users(db: AsyncSession, user1_id: str, user2_id: str):
        """
        根据两个用户ID获取会话（不区分顺序）
        """
        try:
            # 确保user1_id < user2_id，匹配数据库约束
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
                
            query = select(PrivateConversation).where(
                PrivateConversation.user1_id == user1_id,
                PrivateConversation.user2_id == user2_id
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            log.info(f"获取用户 {user1_id} 和 {user2_id} 的会话: {conversation}")
            return conversation
        except Exception as e:
            log.error(f"获取用户 {user1_id} 和 {user2_id} 的会话失败: {e}")
            raise e

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: str):
        """
        根据会话ID获取会话
        """
        try:
            query = select(PrivateConversation).where(
                PrivateConversation.conversation_id == conversation_id
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            log.info(f"获取会话 {conversation_id}: {conversation}")
            return conversation
        except Exception as e:
            log.error(f"获取会话 {conversation_id} 失败: {e}")
            raise e

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str):
        """
        根据用户ID获取该用户参与的所有会话
        """
        try:
            query = select(PrivateConversation).where(
                (PrivateConversation.user1_id == user_id) | 
                (PrivateConversation.user2_id == user_id)
            ).order_by(PrivateConversation.updated_at.desc())
            result = await db.execute(query)
            conversations = result.scalars().all()
            log.info(f"获取用户 {user_id} 的所有会话: {len(conversations)} 个")
            return conversations
        except Exception as e:
            log.error(f"获取用户 {user_id} 的会话列表失败: {e}")
            raise e

    @staticmethod
    async def update_last_message(db: AsyncSession, conversation_id: str, message_id: str):
        """
        更新会话的最后一条消息信息
        """
        try:
            query = select(PrivateConversation).where(
                PrivateConversation.conversation_id == conversation_id
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                conversation.last_message_id = message_id
                await db.commit()
                await db.refresh(conversation)
                log.info(f"更新会话 {conversation_id} 的最后一条消息: {message_id}")
                return conversation
            return None
        except Exception as e:
            await db.rollback()
            log.error(f"更新会话 {conversation_id} 的最后一条消息失败: {e}")
            raise e

    @staticmethod
    async def increment_unread_count(db: AsyncSession, conversation_id: str, user_id: str):
        """
        增加指定用户的未读消息计数
        """
        try:
            query = select(PrivateConversation).where(
                PrivateConversation.conversation_id == conversation_id
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                if conversation.user1_id == user_id:
                    conversation.unread_count_user1 += 1
                else:
                    conversation.unread_count_user2 += 1
                await db.commit()
                await db.refresh(conversation)
                log.info(f"增加用户 {user_id} 在会话 {conversation_id} 的未读消息计数")
                return conversation
            return None
        except Exception as e:
            await db.rollback()
            log.error(f"增加未读消息计数失败: {e}")
            raise e

    @staticmethod
    async def reset_unread_count(db: AsyncSession, conversation_id: str, user_id: str):
        """
        重置指定用户的未读消息计数
        """
        try:
            query = select(PrivateConversation).where(
                PrivateConversation.conversation_id == conversation_id
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                if conversation.user1_id == user_id:
                    conversation.unread_count_user1 = 0
                else:
                    conversation.unread_count_user2 = 0
                await db.commit()
                await db.refresh(conversation)
                log.info(f"重置用户 {user_id} 在会话 {conversation_id} 的未读消息计数")
                return conversation
            return None
        except Exception as e:
            await db.rollback()
            log.error(f"重置未读消息计数失败: {e}")
            raise e
