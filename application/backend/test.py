import asyncio
from application.backend.logic.inference.chat import rag_logic, test_rag_query

async def main():
    result = await rag_logic(test_rag_query)
    print(result)

asyncio.run(main())