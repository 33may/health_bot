import uuid
from typing import List

from tqdm import tqdm


from sqlalchemy import select

from application.backend.database.config import open_connection
from application.backend.database.tables import Documents, Chunks
from application.backend.logic.embeddings.model import compute_embedding


def add_documents(document_contents:  List[dict]):
    with open_connection() as session:
        for doc in tqdm(document_contents):
            splitted = split_doc(doc)

            result = session.execute(
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
            session.flush()

            for chunk in splitted["chunks"]:
                chunk_id = uuid.uuid4()
                new_chunk = Chunks(
                    id=chunk_id,
                    doc_id=doc_id,
                    embedding=compute_embedding(chunk),
                    content_debud=chunk
                )
                session.add(new_chunk)

        session.commit()

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


def retrieve_similar_documents(query: str, limit_docs: int = 3, limit_chunks: int = 20):
    with open_connection() as session:
        embedding = compute_embedding(query)
        similarity_column = Chunks.embedding.cosine_distance(embedding)

        # Get chunk information with document IDs
        chunks_stmt = (
            select(Chunks.doc_id, similarity_column.label("similarity_score"))
            .order_by(similarity_column.asc())
            .limit(limit_chunks)
        )
        chunks = session.execute(chunks_stmt).fetchall()

        # Process scores
        documents = {}
        for chunk in chunks:
            doc_id = chunk[0]
            documents.setdefault(doc_id, {"score": 0})
            documents[doc_id]["score"] += (1 - chunk[1])

        # Get top document IDs
        top_docs = sorted(documents.items(),
                          key=lambda item: item[1]["score"],
                          reverse=True)[:limit_docs]
        doc_ids = [doc_id for doc_id, _ in top_docs]

        # Load document data as dictionaries
        docs_stmt = (
            select(
                Documents.id,
                Documents.name,
                Documents.content
            )
            .where(Documents.id.in_(doc_ids))
        )

        documents_data = [
            {"id": id, "name": name, "content": content}
            for id, name, content in session.execute(docs_stmt)
        ]

        return documents_data










