import uuid
from typing import List

from tqdm import tqdm

from app.database.config import open_async_connection
from app.database.tables import Documents, Chunks
from app.embeddings.model import compute_embedding
from sqlalchemy import select


async def add_documents(document_contents:  List[dict]):
    async with open_async_connection() as session:
        for doc in tqdm(document_contents):
            splitted = split_doc(doc)

            result = await session.execute(
                select(Documents.id).where(Documents.name == splitted["name"])
            )
            existing_doc_id = result.scalar()

            if existing_doc_id is not None:
                continue

            doc_id = uuid.uuid4()

            new_doc = Documents(
                id=doc_id,
                name=splitted["name"],
                content=splitted["content"]
            )
            session.add(new_doc)
            await session.flush()

            for chunk in splitted["chunks"]:
                chunk_id = uuid.uuid4()
                new_chunk = Chunks(
                    id=chunk_id,
                    doc_id=doc_id,
                    embedding=compute_embedding(chunk),
                    content_debud=chunk
                )
                session.add(new_chunk)

        await session.commit()

def split_doc(document: dict, size = 1000, overlap = 200):
    content = document.get("content", "")
    if not content:
        return []

    step = size - overlap
    chunks = []

    for i in range(0, len(content), step):
        chunk = content[i:i + size]
        chunks.append(chunk)

    return {
        "name": document["name"],
        "content": document["content"],
        "chunks": chunks
    }

async def retrieve_similar_documents(query: str, limit_docs: int = 3, limit_chunks: int = 20):
    async with open_async_connection() as session:
        embedding = compute_embedding(query)

        similarity_column = Chunks.embedding.cosine_distance(embedding)

        chunks_stmt = (
            select(Chunks.doc_id, similarity_column.label("similarity_score"))
            .order_by(similarity_column.asc())
            .limit(limit_chunks)
        )

        chunks = (await session.execute(chunks_stmt)).fetchall()

        documents = {}
        for chunk in chunks:
            doc_id = chunk[0]
            documents.setdefault(doc_id, {"score": 0})
            documents[doc_id]["score"] += (1 - chunk[1])

        top_docs = [doc_id for doc_id, score in sorted(documents.items(), key=lambda item: item[1]["score"], reverse=True)][:limit_docs]

        docs_stmt = (
            select(Documents)
            .where(Documents.id.in_(top_docs))
        )

        documents = (await session.execute(docs_stmt)).fetchall()

        return documents










