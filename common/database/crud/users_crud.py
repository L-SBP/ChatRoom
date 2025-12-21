from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.log import log
from common.database.models.users import Users


class UsersCRUD:
    """用户CRUD类"""

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        """
        在数据库创建用户实例
        """
        user = Users(**kwargs)

        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info(f"创建用户成功: {user}")
            return user
        except Exception as e:
            await db.rollback()
            log.error(f"创建用户失败: {e}")
            raise e

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str):
        """
        根据用户名获取用户实例
        """
        try:
            query = select(Users).where(Users.username == username)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            log.info(f"获取用户成功: {user}")
            return user
        except Exception as e:
            log.error(f"获取用户失败: {e}")
            raise e

    @staticmethod
    async def update(db: AsyncSession, user: Users, **kwargs):
        """
        更新用户实例
        """
        try:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await db.commit()
            await db.refresh(user)
            log.info(f"更新用户成功: {user}")
            return user
        except Exception as e:
            log.error(f"更新用户失败: {e}")
            await db.rollback()
            raise e

user_crud = UsersCRUD()