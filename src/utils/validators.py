# src/utils/validators.py
"""
Input validation utilities for security and quality.
"""
import re
from typing import Tuple, Optional
from config.constants import ValidationRules, ErrorMessages
from src.utils.logging_utils import get_logger

logger = get_logger("validators")


class InputValidator:
    """
    Validates user inputs for security and quality.
    Prevents injection attacks and ensures input meets requirements.
    """
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a user query.
        
        Args:
            query: The user's query string
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
            
        Examples:
            >>> validator = InputValidator()
            >>> validator.validate_query("What is Python?")
            (True, None)
            >>> validator.validate_query("")
            (False, "Query cannot be empty...")
        """
        # Check if empty or whitespace only
        if not query or not query.strip():
            logger.warning("Empty query rejected")
            return False, ErrorMessages.QUERY_EMPTY
        
        # Check length
        if len(query) < ValidationRules.MIN_QUERY_LENGTH:
            logger.warning("Query too short", length=len(query))
            return False, f"❌ Query too short (min {ValidationRules.MIN_QUERY_LENGTH} characters)"
        
        if len(query) > ValidationRules.MAX_QUERY_LENGTH:
            logger.warning("Query too long", length=len(query))
            return False, ErrorMessages.QUERY_TOO_LONG
        
        # Check for suspicious patterns (basic injection detection)
        query_lower = query.lower()
        for pattern in ValidationRules.SUSPICIOUS_PATTERNS:
            if pattern in query_lower:
                logger.warning(
                    "Suspicious pattern detected in query",
                    pattern=pattern,
                    query_preview=query[:50]
                )
                return False, (
                    "❌ Query contains potentially unsafe content.\n"
                    "  → Please rephrase your question"
                )
        
        logger.debug("Query validated successfully", query_length=len(query))
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not url.strip():
            return False, "❌ URL cannot be empty"
        
        # Basic URL pattern check
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            logger.warning("Invalid URL format", url=url[:100])
            return False, (
                "❌ Invalid URL format.\n"
                "  → Must start with http:// or https://\n"
                "  → Example: https://example.com/page"
            )
        
        logger.debug("URL validated successfully", url=url[:100])
        return True, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename safe for filesystem operations
            
        Examples:
            >>> InputValidator.sanitize_filename("../../../etc/passwd")
            'etc_passwd'
            >>> InputValidator.sanitize_filename("my file.txt")
            'my_file.txt'
        """
        # Remove path components
        filename = filename.split('/')[-1]
        filename = filename.split('\\')[-1]
        
        # Replace unsafe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        logger.debug("Filename sanitized", original=filename[:50])
        return filename
    
    @staticmethod
    def validate_chunk_size(chunk_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate chunk size configuration.
        
        Args:
            chunk_size: Proposed chunk size
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if chunk_size < ValidationRules.MIN_CHUNK_SIZE:
            return False, (
                f"❌ Chunk size too small (min {ValidationRules.MIN_CHUNK_SIZE}).\n"
                "  → Increase chunk_size in config"
            )
        
        if chunk_size > ValidationRules.MAX_CHUNK_SIZE:
            return False, (
                f"❌ Chunk size too large (max {ValidationRules.MAX_CHUNK_SIZE}).\n"
                "  → Decrease chunk_size in config"
            )
        
        return True, None


def validate_and_handle(validation_result: Tuple[bool, Optional[str]]) -> bool:
    """
    Helper function to validate and print error if needed.
    
    Args:
        validation_result: Tuple from a validator function
        
    Returns:
        True if valid, False if invalid (also prints error)
        
    Examples:
        >>> result = InputValidator.validate_query(user_input)
        >>> if not validate_and_handle(result):
        >>>     continue  # Skip processing
    """
    is_valid, error_msg = validation_result
    
    if not is_valid and error_msg:
        print(f"\n{error_msg}\n")
    
    return is_valid
