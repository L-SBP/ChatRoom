import os
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker


class PgHelper:
    """
    PostgreSQL数据库操作类
    """

    _engine: AsyncEngine = None
    _session_factory = None

    @classmethod
    def get_async_engine(cls) -> AsyncEngine:
        """
        获取异步引擎（单例模式）
        """
        if cls._engine is None:
            cls._engine = create_async_engine(
                url=URL.create(
                    drivername='postgresql+asyncpg',
                    username=os.environ.get('DB_USER', 'user'),
                    password=os.environ.get('DB_PASSWORD', 'user_secure_2025'),
                    host=os.environ.get('DB_HOST', 'localhost'),
                    port=int(os.environ.get('DB_PORT', 5432)),
                    database=os.environ.get('DB_NAME', 'ChatRoom')
                ),
                echo=True,
                pool_size=10,              # 连接池大小
                max_overflow=20,            # 超出pool_size后最多允许的额外连接数
                pool_pre_ping=True,         # 检查连接有效性
                pool_recycle=3600,          # 连接回收时间（秒）
            )
        return cls._engine

    @classmethod
    def get_async_session(cls, engine: AsyncEngine) -> AsyncSession:
        """
        获取异步会话
        """
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return cls._session_factory()

    @classmethod
    async def close_async_engine(cls):
        """
        关闭异步引擎
        """
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None