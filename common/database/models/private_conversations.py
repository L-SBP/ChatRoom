from sqlalchemy import Column, UUID, Integer, Boolean, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from common.database.models.base_model import BaseModel


class PrivateConversation(BaseModel):
    """私聊会话模型"""
    __tablename__ = "private_conversations"

    conversation_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    user1_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    user2_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    last_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("private_messages.message_id", ondelete="SET NULL")
    )

    last_message_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp()
    )

    unread_count_user1 = Column(Integer, server_default="0")

    unread_count_user2 = Column(Integer, server_default="0")

    is_muted_user1 = Column(Boolean, server_default="FALSE")

    is_muted_user2 = Column(Boolean, server_default="FALSE")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # 约束：确保user1_id < user2_id且唯一
    __table_args__ = (
        CheckConstraint("user1_id < user2_id", name="unique_user_pair"),
    )

    # 关系
    user1 = relationship("Users", foreign_keys=[user1_id])
    user2 = relationship("Users", foreign_keys=[user2_id])
    last_message = relationship("PrivateMessage", foreign_keys=[last_message_id])