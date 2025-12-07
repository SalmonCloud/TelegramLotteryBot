from typing import Optional

import asyncmy

from app.config import DbConfig


_pool: Optional[asyncmy.Pool] = None


async def init_db_pool(db_config: DbConfig) -> None:
    global _pool
    if _pool:
        return

    _pool = await asyncmy.create_pool(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        db=db_config.database,
        autocommit=True,
        minsize=1,
        maxsize=5,
    )


def get_db_pool() -> asyncmy.Pool:
    if not _pool:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
