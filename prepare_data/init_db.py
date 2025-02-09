import os
import asyncio
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

from sqlalchemy import text

from app.database.config import engine
from app.database.database_functions import add_documents
from app.database.tables import Base


async def init_db_tables():
    """
    Initializes the database by creating all tables defined in Base.
    Uses the async engine's run_sync to execute the synchronous create_all.
    """
    async with engine.begin() as conn:

        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created (if they did not exist).")

def load_and_process_pdfs(data_dir: str):
    """
    Loads PDF files from the specified folder using DirectoryLoader and PyPDFLoader,
    then converts them into a list of dictionaries with "name" and "content" keys.
    """
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    documents = loader.load()
    processed_docs = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        file_name = os.path.basename(source)
        doc_dict = {
            "name": file_name.replace(".pdf", ""),
            "content": doc.page_content
        }
        processed_docs.append(doc_dict)
    return processed_docs


async def main():

    await init_db_tables()

    data_dir = os.path.join(os.getcwd(), "documents")

    document_contents = load_and_process_pdfs(data_dir)

    await add_documents(document_contents)
    print("PDF documents processed and uploaded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
