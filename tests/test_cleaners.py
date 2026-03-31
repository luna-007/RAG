# tests/test_cleaners.py
"""
Unit tests for document cleaners.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.wikipedia_cleaner import WikipediaDocumentCleaner
from src.processors.generic_cleaner import GenericWebCleaner
from src.processors.cleaner_factory import CleanerFactory


class TestWikipediaClean:
    """Test Wikipedia cleaner"""
    
    def setup_method(self):
        self.cleaner = WikipediaDocumentCleaner()
    
    def test_removes_citations(self):
        text = "India[1] is a country[2] in South Asia."
        cleaned = self.cleaner.clean_text(text)
        assert "[1]" not in cleaned
        assert "[2]" not in cleaned
        assert "India" in cleaned
    
    def test_removes_urls(self):
        text = "Visit https://wikipedia.org for more info."
        cleaned = self.cleaner.clean_text(text)
        assert "https://" not in cleaned
        assert "Visit" in cleaned
    
    def test_removes_wikipedia_artifacts(self):
        text = "India listenⓘ is a country. Wikimedia Commonsvte"
        cleaned = self.cleaner.clean_text(text)
        assert "listenⓘ" not in cleaned
        assert "Wikimedia Commonsvte" not in cleaned
    
    def test_should_keep_valid_chunk(self):
        chunk = "India is the seventh-largest country by area."
        assert self.cleaner.should_keep_chunk(chunk) == True
    
    def test_should_reject_short_chunk(self):
        chunk = "India"
        assert self.cleaner.should_keep_chunk(chunk) == False
    
    def test_should_reject_junk_chunk(self):
        chunk = "See also: List of related articles. External links"
        assert self.cleaner.should_keep_chunk(chunk) == False
    
    def test_should_reject_table_chunk(self):
        chunk = "Year 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019"
        assert self.cleaner.should_keep_chunk(chunk) == False


class TestGenericCleaner:
    """Test generic web cleaner"""
    
    def setup_method(self):
        self.cleaner = GenericWebCleaner()
    
    def test_removes_urls(self):
        text = "Check out https://example.com for more."
        cleaned = self.cleaner.clean_text(text)
        assert "https://" not in cleaned
    
    def test_removes_emails(self):
        text = "Contact us at info@example.com"
        cleaned = self.cleaner.clean_text(text)
        assert "@" not in cleaned
    
    def test_should_keep_valid_chunk(self):
        chunk = "This is a valid paragraph with enough content to be meaningful."
        assert self.cleaner.should_keep_chunk(chunk) == True
    
    def test_should_reject_navigation(self):
        chunk = "Subscribe to newsletter. Follow us on social media."
        assert self.cleaner.should_keep_chunk(chunk) == False


class TestCleanerFactory:
    """Test cleaner factory"""
    
    def test_detects_wikipedia(self):
        url = "https://en.wikipedia.org/wiki/India"
        source_type = CleanerFactory.detect_source_type(url)
        assert source_type == "wikipedia"
    
    def test_detects_news(self):
        url = "https://www.bbc.com/news/world"
        source_type = CleanerFactory.detect_source_type(url)
        assert source_type == "news"
    
    def test_returns_generic_for_unknown(self):
        url = "https://random-blog.com/article"
        source_type = CleanerFactory.detect_source_type(url)
        assert source_type == "generic"
    
    def test_gets_correct_cleaner(self):
        cleaner = CleanerFactory.get_cleaner("wikipedia")
        assert isinstance(cleaner, WikipediaDocumentCleaner)
        
        cleaner = CleanerFactory.get_cleaner("generic")
        assert isinstance(cleaner, GenericWebCleaner)
