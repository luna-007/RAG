# src/processors/wikipedia_cleaner.py
"""
Wikipedia-specific document cleaner.
Handles Wikipedia's unique formatting, citations, and navigation elements.
"""
import re
from typing import Set
from .base_cleaner import BaseDocumentCleaner
from config.settings import settings

class WikipediaDocumentCleaner(BaseDocumentCleaner):
    """Specialized cleaner for Wikipedia content"""
    
    def __init__(self):
        super().__init__(source_type="wikipedia")
        
        # Wikipedia-specific junk indicators
        self.junk_indicators = {
            "isbn", "preceded by", "succeeded by", "official website",
            "archived from", "external links", "see also", "navigation menu",
            "view t e", "navbox", "wikimedia commons", "listenⓘ",
            "media related to", "contents"
        }
        
        # Track unique chunks for deduplication
        self.seen_fingerprints: Set[str] = set()
    
    def clean_text(self, text: str) -> str:
        """Wikipedia-specific text cleaning"""
        
        # 1. Fix spacing issues (CamelCase splits)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 2. Remove citations [1], [2], [citation needed], etc.
        text = re.sub(r'\[[0-9a-zA-Z\s]+\]', '', text)
        
        # 3. Remove phonetic symbols [ˈɪndiə]
        text = re.sub(r'\[[^\]]*[\u0250-\u02AF][^\]]*\]', '', text)
        
        # 4. Remove Wikipedia-specific artifacts
        replacements = {
            "Wikimedia Commonsvte": "",
            "listenⓘ": "",
            "Ahmedabadthe": "Ahmedabad the",
            "Contents": "",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 5. Clean whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' {2,}', ' ', text)  # Single spaces
        
        # 6. Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # 7. Remove ISBNs
        text = re.sub(r'ISBN\s*\d{10,13}', '', text)
        text = re.sub(r'ISBN\s*(?:\d+[-\s]){3,}\d+', '', text)
        
        # 8. Remove stray markers
        text = re.sub(r'^\s*[\^]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'—{2,}', '', text)
        
        return text.strip()
    
    def should_keep_chunk(self, chunk: str) -> bool:
        """Wikipedia-specific chunk filtering with deduplication"""
        
        # 1. Length check
        if not chunk or len(chunk.split()) < settings.chunking.min_chunk_words:
            return False
        
        chunk_lower = chunk.lower()
        
        # 2. Junk keyword filter
        if any(indicator in chunk_lower for indicator in self.junk_indicators):
            return False
        
        # 3. Table/list filter (digit ratio)
        digit_ratio = sum(c.isdigit() for c in chunk) / len(chunk)
        if digit_ratio > settings.chunking.max_digit_ratio:
            return False
        
        # 4. Hybrid deduplication
        # Check both start and middle of chunk
        start_fingerprint = chunk[:100].lower().strip()
        
        core_fingerprint = ""
        if len(chunk) > 250:
            core_fingerprint = chunk[100:250].lower().strip()
        else:
            core_fingerprint = chunk.lower().strip()
        
        # If we've seen either part before, skip
        if start_fingerprint in self.seen_fingerprints:
            return False
        if core_fingerprint in self.seen_fingerprints:
            return False
        
        # Mark as seen
        self.seen_fingerprints.add(start_fingerprint)
        if core_fingerprint:
            self.seen_fingerprints.add(core_fingerprint)
        
        return True
    
    def reset_dedup(self):
        """Reset deduplication state (useful for processing new documents)"""
        self.seen_fingerprints.clear()
