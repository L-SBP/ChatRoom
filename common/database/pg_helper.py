from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker


class PgHelper:
    """
    PostgreSQL数据库操作类
    """

    @classmethod
    def get_async_engine(cls) -> AsyncEngine:
        """
        获取异步引擎
        """
        return create_async_engine(
            url=URL.create(
                drivername='postgresql+asyncpg',
                username='user',
                password='user_secure_2025',
                host='localhost',
                port=5432,
                database='ChatRoom'
            ),
            echo=True,
        )

    @classmethod
    def get_async_session(cls, engine: AsyncEngine) -> AsyncSession:
        """
        获取异步会话
        """
        return async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )()

    @classmethod
    async def close_async_engine(cls, engine: AsyncEngine):
        """
        关闭异步引擎
        """
        await engine.dispose()