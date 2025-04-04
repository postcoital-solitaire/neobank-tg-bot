import aiomysql


class DatabaseManager:
    def __init__(self, loop=None):
        self.loop = loop
        self.pool = None

    async def create_pool(self):
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host='92.118.115.96',
                port=3306,
                user='ofice',
                password='some_pass',
                db='cards_db',
                loop=self.loop,
                maxsize=10,
                autocommit=True
            )
        return self.pool

    async def execute_query(self, query_func, where_field=""):
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.cursors.DictCursor) as cur:
                if len(where_field) > 0:
                    return await query_func(cur, where_field=where_field)
                return await query_func(cur)

