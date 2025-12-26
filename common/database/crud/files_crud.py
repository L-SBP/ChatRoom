from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.models.files import File
from common.log import log


class FilesCRUD:
    """文件CRUD类"""

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        """
        在数据库创建文件实例
        """
        file = File(**kwargs)

        try:
            db.add(file)
            await db.commit()
            await db.refresh(file)
            log.info(f"创建文件记录成功: {file.file_name}")
            return file
        except Exception as e:
            await db.rollback()
            log.error(f"创建文件记录失败: {e}")
            raise e

    @staticmethod
    async def get_by_file_id(db: AsyncSession, file_id):
        """
        根据文件ID获取文件实例
        """
        try:
            query = select(File).where(File.file_id == file_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            log.error(f"获取文件失败: {e}")
            raise e

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id, limit: int = 100):
        """
        根据用户ID获取文件列表
        """
        try:
            query = select(File).where(File.user_id == user_id).order_by(File.created_at.desc()).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            log.error(f"获取用户文件列表失败: {e}")
            raise e
