"""
Modèle KnowledgeDocument — Registre des documents de connaissance IA
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database.db import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Fichier
    filename = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # État
    is_active = Column(Boolean, default=True, nullable=False)

    # Métadonnées
    file_size = Column(Integer, nullable=True)       # En octets
    chunk_count = Column(Integer, default=0)          # Chunks indexés dans ChromaDB
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    # Horodatages
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, filename={self.filename}, active={self.is_active})>"
