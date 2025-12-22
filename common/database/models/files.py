from sqlalchemy import Column, UUID, VARCHAR, TEXT, Integer, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from common.database.models.base_model import BaseModel


class File(BaseModel):
    """文件存储模型"""
    __tablename__ = "files"

    file_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL")
    )

    file_name = Column(VARCHAR(255), nullable=False)

    file_path = Column(TEXT, nullable=False)

    file_url = Column(TEXT, nullable=False)

    file_type = Column(VARCHAR(100))

    mime_type = Column(VARCHAR(100))

    file_size = Column(TEXT)  # BIGINT在SQLAlchemy中映射为TEXT

    width = Column(Integer)

    height = Column(Integer)

    duration = Column(Integer)

    thumbnail_url = Column(TEXT)

    upload_status = Column(VARCHAR(20), server_default="completed")

    is_temp = Column(Boolean, server_default="FALSE")

    expires_at = Column(DateTime(timezone=True))

    # 音频特定字段
    bitrate = Column(Integer)      # 比特率（kbps）
    sample_rate = Column(Integer)  # 采样率（Hz）
    channels = Column(Integer, server_default="1")  # 声道数

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

    class Config:
        from_attributes = True