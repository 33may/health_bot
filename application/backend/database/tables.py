from sqlalchemy import String, Column,  ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Documents(Base):
    __tablename__ = 'documents'
    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    content = Column(JSONB, nullable=False)

class Chunks(Base):
    __tablename__ = 'chunks'
    id = Column(UUID, primary_key=True)
    doc_id = Column(UUID, ForeignKey('documents.id'))
    embedding = Column(Vector(768), nullable=False)
    content_debud = Column(JSONB, nullable=False)