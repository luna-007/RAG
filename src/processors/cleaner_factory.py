# src/processors/cleaner_factory.py
"""
Factory for selecting appropriate cleaner based on document source.
This is the KEY to handling multiple document types automatically!
"""
from urllib.parse import urlparse
from typing import Optional
from .base_cleaner import BaseDocumentCleaner
from .wikipedia_cleaner import WikipediaDocumentCleaner
from .generic_cleaner import GenericWebCleaner
from .news_cleaner import NewsArticleCleaner
from .servicenow_cleaner import ServiceNowDocumentCleaner
from src.utils.logging_utils import get_logger

logger = get_logger("cleaner_factory")

class CleanerFactory:
    """
    Factory that selects the right cleaner based on document source.
    Supports both URL-based and content-based detection.
    """
    
    # Registry of cleaners (easy to extend!)
    CLEANERS = {
        'wikipedia': WikipediaDocumentCleaner,
        'news': NewsArticleCleaner,
        'servicenow': ServiceNowDocumentCleaner,
        'generic': GenericWebCleaner,
        # Add more as needed:
        # 'technical_docs': TechnicalDocsCleaner,
        # 'code': CodeCleaner,
        # 'pdf': PDFCleaner,
    }
    
    # News domains (expand as needed)
    NEWS_DOMAINS = {
        'cnn.com', 'bbc.com', 'bbc.co.uk', 'reuters.com',
        'apnews.com', 'nytimes.com', 'wsj.com', 'bloomberg.com',
        'theguardian.com', 'washingtonpost.com', 'npr.org'
    }
    
    @staticmethod
    def detect_source_type(url: str, content: str = "") -> str:
        """
        Detect document source type from URL or content.
        
        Args:
            url: Source URL
            content: Optional content for content-based detection
            
        Returns:
            Source type string (e.g., 'wikipedia', 'news', 'generic')
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # URL-based detection (fast path)
        if 'wikipedia.org' in domain:
            logger.debug("Detected Wikipedia source", url=url)
            return 'wikipedia'
        
        if any(news_domain in domain for news_domain in CleanerFactory.NEWS_DOMAINS):
            logger.debug("Detected news source", url=url, domain=domain)
            return 'news'
        
        if 'readthedocs.io' in domain or 'docs.' in domain:
            logger.debug("Detected technical docs", url=url)
            return 'technical_docs'  # Future extension
        
        if 'github.com' in domain:
            logger.debug("Detected code source", url=url)
            return 'code'  # Future extension
        
        # Content-based detection (if URL is ambiguous)
        if content:
            content_lower = content.lower()
            
            # Wikipedia signatures
            if 'wikimedia' in content_lower or 'from wikipedia' in content_lower:
                logger.debug("Detected Wikipedia from content")
                return 'wikipedia'
            
            # News signatures
            news_signatures = ['breaking news', 'reuters', 'associated press', 'byline']
            if any(sig in content_lower for sig in news_signatures):
                logger.debug("Detected news from content")
                return 'news'
            
            # Technical docs signatures
            tech_signatures = ['api reference', 'documentation', 'parameters:', 'returns:']
            if any(sig in content_lower for sig in tech_signatures):
                logger.debug("Detected technical docs from content")
                return 'technical_docs'
            
            # Code signatures
            if content.count('def ') > 5 or content.count('class ') > 3:
                logger.debug("Detected code from content")
                return 'code'
        
        # Default fallback
        logger.debug("Using generic cleaner", url=url)
        return 'generic'
    
    @classmethod
    def get_cleaner(cls, source_type: str, **kwargs) -> BaseDocumentCleaner:
        """
        Get appropriate cleaner for source type.
        
        Args:
            source_type: Type of source ('wikipedia', 'news', etc.)
            **kwargs: Additional arguments for cleaner initialization
            
        Returns:
            Appropriate cleaner instance
        """
        cleaner_class = cls.CLEANERS.get(source_type, GenericWebCleaner)
        
        logger.info("Creating cleaner", source_type=source_type, cleaner=cleaner_class.__name__)
        
        return cleaner_class(**kwargs)
    
    @classmethod
    def get_cleaner_for_url(
        cls,
        url: str,
        content: str = "",
        **kwargs
    ) -> BaseDocumentCleaner:
        """
        Convenience method: detect source type and return appropriate cleaner.
        
        Args:
            url: Source URL
            content: Optional content for detection
            **kwargs: Additional cleaner arguments
            
        Returns:
            Appropriate cleaner instance
        """
        source_type = cls.detect_source_type(url, content)
        return cls.get_cleaner(source_type, **kwargs)
    
    @classmethod
    def register_cleaner(cls, source_type: str, cleaner_class: type):
        """
        Register a new cleaner type (for extensibility).
        
        Args:
            source_type: Name of the source type
            cleaner_class: Cleaner class to register
        """
        cls.CLEANERS[source_type] = cleaner_class
        logger.info("Registered new cleaner", source_type=source_type, cleaner=cleaner_class.__name__)


# Convenience function
def get_cleaner_for_url(url: str, content: str = "") -> BaseDocumentCleaner:
    """Get appropriate cleaner for a URL (convenience function)"""
    return CleanerFactory.get_cleaner_for_url(url, content)
