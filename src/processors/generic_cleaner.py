# src/processors/generic_cleaner.py
"""
Generic web cleaner for most websites.
Handles common web artifacts without being too aggressive.
"""
import re
from .base_cleaner import BaseDocumentCleaner
from config.settings import settings

class GenericWebCleaner(BaseDocumentCleaner):
    """Generic cleaner for most websites"""
    
    def __init__(self):
        super().__init__(source_type="generic")
        
        # Common junk across websites
        self.common_junk = {
            "cookie policy", "privacy policy", "terms of service",
            "subscribe to newsletter", "follow us on", "share this",
            "related articles", "advertisement", "sponsored content",
            "sign up", "log in", "create account"
        }
    
    def clean_text(self, text: str) -> str:
        """Generic web text cleaning"""
        
        # 1. Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # 2. Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # 3. Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # 4. Remove HTML entities that slip through BeautifulSoup
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        
        # 5. Remove non-ASCII (optional - might want to keep for multilingual)
        # text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # 6. Clean up after removals
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def should_keep_chunk(self, chunk: str) -> bool:
        """Generic chunk quality filtering"""
        
        # 1. Length check
        if not chunk or len(chunk.split()) < settings.chunking.min_chunk_words:
            return False
        
        chunk_lower = chunk.lower()
        
        # 2. Filter common junk
        if any(junk in chunk_lower for junk in self.common_junk):
            return False
        
        # 3. Filter overly numeric (tables/lists)
        digit_ratio = sum(c.isdigit() for c in chunk) / len(chunk)
        if digit_ratio > 0.20:  # More lenient than Wikipedia
            return False
        
        # 4. Filter chunks with too few letters (likely navigation/UI elements)
        alpha_ratio = sum(c.isalpha() for c in chunk) / len(chunk)
        if alpha_ratio < 0.50:  # At least 50% letters
            return False
        
        # 5. Filter very short chunks even if word count passes
        if len(chunk) < 50:  # Less than 50 characters
            return False
        
        return True
