import os
import asyncpg


class Database(object):

    def __new__(cls):
        if not hasattr(cls, '__instance'):
            cls.__instance = super(Database, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self.__pool = None

    async def get_pool(self):
        if self.__pool:
            return self.__pool
        return await self.__set_pool()

    async def __set_pool(self):
        self.__pool = await asyncpg.create_pool(
            min_size=1,
            max_size=3,
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_NAME'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        return self.__pool

    async def close(self):
        if self.__pool:
            await self.__pool.close()
        self.__pool = None


def connection(func):
    async def wrap(*args, **kwargs):
        pool = await Database().get_pool()
        async with pool.acquire() as conn:
            res = await func(*args, **kwargs, conn=conn)
            await conn.close()
        return res

    return wrap

