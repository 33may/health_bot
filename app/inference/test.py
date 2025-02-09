import asyncio

from app.database.database_functions import retrieve_similar_documents


async def main():
    query = "У мене завжди болить голова в кінці дня?"

    rows = await retrieve_similar_documents(query)

    res = []
    for row in rows:
        row_dict = dict(row._mapping)
        res.append(row_dict)
    print(33)



if __name__ == '__main__':
    asyncio.run(main())
