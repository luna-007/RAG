# src/processors/news_cleaner.py
"""
Specialized cleaner for news websites.
Removes bylines, timestamps, and news-specific boilerplate.
"""
import re
from .base_cleaner import BaseDocumentCleaner
from config.settings import settings

class NewsArticleCleaner(BaseDocumentCleaner):
    """News website cleaner"""
    
    def __init__(self):
        super().__init__(source_type="news")
        
        self.news_junk = {
            "breaking news", "developing story", "this is a developing story",
            "read more:", "related coverage:", "editor's note:",
            "updated at", "published on", "by associated press",
            "subscribe to", "sign up for", "get the latest"
        }
    
    def clean_text(self, text: str) -> str:
        """News-specific cleaning"""
        
        # 1. Remove datelines (CITY, Month Day (Agency) - ...)
        text = re.sub(
            r'^[A-Z\s]+,\s+\w+\s+\d+\s+\([A-Za-z\s]+\)\s*[-–]\s*',
            '',
            text,
            flags=re.MULTILINE
        )
        
        # 2. Remove timestamps
        text = re.sub(r'\d{1,2}:\d{2}\s*[AP]M\s*[A-Z]{2,4}', '', text)
        
        # 3. Remove "Updated:" lines
        text = re.sub(r'Updated:?\s+\w+\s+\d+,\s+\d{4}', '', text)
        text = re.sub(r'Published:?\s+\w+\s+\d+,\s+\d{4}', '', text)
        
        # 4. Remove bylines (By AUTHOR NAME -)
        text = re.sub(r'^By\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*[-–]?\s*', '', text, flags=re.MULTILINE)
        
        # 5. Standard web cleaning
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def should_keep_chunk(self, chunk: str) -> bool:
        """News-specific filtering"""
        
        # News chunks should be more substantial
        if not chunk or len(chunk.split()) < 15:
            return False
        
        chunk_lower = chunk.lower()
        
        # Filter news boilerplate
        if any(junk in chunk_lower for junk in self.news_junk):
            return False
        
        # News shouldn't be too numeric (but more lenient than Wikipedia)
        digit_ratio = sum(c.isdigit() for c in chunk) / len(chunk)
        if digit_ratio > 0.25:
            return False
        
        return True
