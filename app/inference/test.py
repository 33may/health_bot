import asyncio
from app.database.config import open_async_connection
from app.database.tables import Chunks
from app.embeddings.model import compute_embedding
from sqlalchemy import select


async def main():
    query = "У мене завжди болить голова в кінці дня?"

    embedding = compute_embedding(query)

    similarity_column = Chunks.embedding.cosine_distance(embedding)

    stmt = (
        select(Chunks)
        .add_columns(similarity_column.label("similarity_score"))
        .order_by(similarity_column.asc())
        .limit(3)
    )

    async with open_async_connection() as connection:
        result = await connection.execute(stmt)
        rows = result.fetchall()
        res = []
        for row in rows:
            row_dict = dict(row._mapping)
            res.append(row_dict)
        print(33)



if __name__ == '__main__':
    asyncio.run(main())
