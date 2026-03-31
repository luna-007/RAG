# src/processors/base_cleaner.py
"""
Abstract base class for document cleaners.
All cleaners must implement these methods.
"""
from abc import ABC, abstractmethod
from typing import List
from langchain_classic.schema import Document
from src.utils.logging_utils import get_logger

logger = get_logger("processors")

class BaseDocumentCleaner(ABC):
    """
    Abstract base for document cleaners.
    Implement clean_text() and should_keep_chunk() for each source type.
    """
    
    def __init__(self, source_type: str):
        self.source_type = source_type
        logger.info(f"Initialized {self.__class__.__name__}", source_type=source_type)
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """
        Clean raw text from the source.
        Implement source-specific cleaning logic here.
        """
        pass
    
    @abstractmethod
    def should_keep_chunk(self, chunk: str) -> bool:
        """
        Decide if a chunk should be kept after splitting.
        Return True to keep, False to filter out.
        """
        pass
    
    def clean_documents(self, docs: List[Document]) -> List[Document]:
        """
        Apply cleaning to all documents.
        This method is the same for all cleaners.
        """
        cleaned = []
        original_count = len(docs)
        
        for i, doc in enumerate(docs):
            try:
                cleaned_text = self.clean_text(doc.page_content)
                if cleaned_text.strip():
                    doc.page_content = cleaned_text
                    cleaned.append(doc)
            except Exception as e:
                logger.error(
                    f"Failed to clean document {i}",
                    error=str(e),
                    source_type=self.source_type
                )
        
        logger.info(
            "Documents cleaned",
            original=original_count,
            cleaned=len(cleaned),
            filtered=original_count - len(cleaned)
        )
        
        return cleaned
    
    def filter_chunks(self, chunks: List[Document]) -> List[Document]:
        """
        Filter chunks based on quality criteria.
        This method is the same for all cleaners.
        """
        original_count = len(chunks)
        kept = []
        
        for chunk in chunks:
            try:
                if self.should_keep_chunk(chunk.page_content):
                    kept.append(chunk)
            except Exception as e:
                logger.error(
                    "Error filtering chunk",
                    error=str(e),
                    chunk_preview=chunk.page_content[:100]
                )
        
        logger.info(
            "Chunks filtered",
            original=original_count,
            kept=len(kept),
            filtered=original_count - len(kept)
        )
        
        return kept
