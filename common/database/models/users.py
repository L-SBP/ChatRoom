from sqlalchemy import Column, UUID, func, VARCHAR, TEXT
from sqlalchemy.dialects.postgresql import TIMESTAMP

from common.database.models.base_model import BaseModel


class Users(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    username = Column(
        VARCHAR(50),
        nullable=False,
        unique=True
    )

    display_name = Column(VARCHAR(100))

    avatar_url = Column(TEXT)

    password_hash = Column(VARCHAR(255), nullable=False)

    email = Column(VARCHAR(100), unique=True)

    phone = Column(VARCHAR(20), unique=True)

    status = Column(
        VARCHAR(20),
        server_default='offline'
    )

    last_seen = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )