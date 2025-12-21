from sqlalchemy import Column, UUID, VARCHAR, TEXT, Boolean, DateTime, func, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from common.database.models.base_model import BaseModel


class GlobalMessage(BaseModel):
    """全局消息模型"""
    __tablename__ = "global_messages"

    __table_args__ = (
        CheckConstraint("content_type IN ('text', 'image', 'video', 'file', 'audio', 'system')", name="global_messages_content_type_check"),
    )

    message_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=False
    )

    content_type = Column(
        VARCHAR(20),
        server_default="text"
    )

    content = Column(TEXT)

    file_url = Column(TEXT)

    file_name = Column(VARCHAR(255))

    file_size = Column(TEXT)  # BIGINT在SQLAlchemy中映射为TEXT

    metadata_ = Column("metadata", JSONB)

    is_edited = Column(Boolean, server_default="FALSE")

    edited_at = Column(DateTime(timezone=True))

    is_deleted = Column(Boolean, server_default="FALSE")

    deleted_at = Column(DateTime(timezone=True))

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

    # 关系
    user = relationship("Users", foreign_keys=[user_id])