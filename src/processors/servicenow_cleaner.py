# src/processors/servicenow_cleaner.py
"""
ServiceNow Knowledge Article Cleaner.
Cleans and processes ServiceNow HTML content.
"""
import re
from typing import List
from langchain.docstore.document import Document
from src.processors.base_cleaner import BaseDocumentCleaner
from src.utils.logging_utils import get_logger

logger = get_logger("servicenow_cleaner")


class ServiceNowDocumentCleaner(BaseDocumentCleaner):
    """
    Cleaner specifically for ServiceNow knowledge articles.
    Handles HTML tags, ServiceNow-specific formatting, and metadata.
    """
    
    def clean_text(self, text: str) -> str:
        """
        Clean ServiceNow article text.
        
        Args:
            text: Raw text from ServiceNow
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove ServiceNow-specific markers
        text = re.sub(r'\[code\].*?\[/code\]', '', text, flags=re.DOTALL)  # Keep code blocks for now
        text = re.sub(r'\[attachment:.*?\]', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = text.strip()
        
        return text
    
    def should_keep_chunk(self, chunk: str) -> bool:
        """
        Determine if a chunk should be kept.
        
        Args:
            chunk: Text chunk
            
        Returns:
            True if chunk should be kept, False otherwise
        """
        if not chunk or len(chunk.strip()) < 10:
            return False
        
        # Must have minimum word count
        words = chunk.split()
        if len(words) < 5:
            return False
        
        # Filter out chunks that are mostly symbols/navigation
        alpha_chars = sum(c.isalpha() for c in chunk)
        if alpha_chars < len(chunk) * 0.5:  # At least 50% alphabetic
            return False
        
        # Filter out common ServiceNow boilerplate
        boilerplate_phrases = [
            'click here to view',
            'please contact',
            'for more information',
            'see also',
            'related articles',
            'was this article helpful',
            'rate this article',
        ]
        
        chunk_lower = chunk.lower()
        # Don't filter if it's mostly boilerplate
        boilerplate_count = sum(1 for phrase in boilerplate_phrases if phrase in chunk_lower)
        if boilerplate_count > 2 and len(words) < 50:
            return False
        
        return True
    
    def clean_documents(self, documents: List[Document]) -> List[Document]:
        """
        Clean ServiceNow documents.
        
        Args:
            documents: Raw documents
            
        Returns:
            Cleaned documents
        """
        logger.info(f"Cleaning {len(documents)} ServiceNow documents")
        
        cleaned_docs = []
        for doc in documents:
            cleaned_text = self.clean_text(doc.page_content)
            
            if cleaned_text and len(cleaned_text) > 50:
                doc.page_content = cleaned_text
                cleaned_docs.append(doc)
        
        logger.info(f"Kept {len(cleaned_docs)} documents after cleaning")
        return cleaned_docs
    
    def filter_chunks(self, chunks: List[Document]) -> List[Document]:
        """
        Filter ServiceNow chunks.
        
        Args:
            chunks: Document chunks
            
        Returns:
            Filtered chunks
        """
        logger.info(f"Filtering {len(chunks)} ServiceNow chunks")
        
        filtered = []
        seen_fingerprints = set()
        
        for chunk in chunks:
            # Check if should keep
            if not self.should_keep_chunk(chunk.page_content):
                continue
            
            # Deduplication
            fingerprint = self.create_fingerprint(chunk.page_content)
            if fingerprint in seen_fingerprints:
                continue
            
            seen_fingerprints.add(fingerprint)
            filtered.append(chunk)
        
        logger.info(f"Kept {len(filtered)} chunks after filtering")
        return filtered
