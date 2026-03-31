# src/utils/response_validator.py
"""
Response validation to detect hallucinations and ensure quality.
"""
from typing import List, Tuple, Optional
from langchain_classic.schema import Document
from config.constants import RejectionPhrases
from src.utils.logging_utils import get_logger

logger = get_logger("response_validator")


class ResponseValidator:
    """
    Validates LLM responses for quality and groundedness.
    Helps detect hallucinations and ensure responses cite context.
    """
    
    @staticmethod
    def is_rejection(response: str) -> bool:
        """
        Check if response is a proper rejection ("I don't know").
        
        Args:
            response: The LLM's response
            
        Returns:
            True if response indicates inability to answer
            
        Examples:
            >>> ResponseValidator.is_rejection("I don't have information about that.")
            True
            >>> ResponseValidator.is_rejection("The capital is Paris.")
            False
        """
        response_lower = response.lower()
        
        for phrase in RejectionPhrases.PHRASES:
            if phrase in response_lower:
                logger.debug("Rejection detected", phrase=phrase)
                return True
        
        return False
    
    @staticmethod
    def check_context_overlap(
        response: str,
        context_docs: List[Document],
        min_overlap: float = 0.3
    ) -> Tuple[bool, float]:
        """
        Check if response has sufficient overlap with context.
        Helps detect hallucinations by ensuring response uses source material.
        
        Args:
            response: The LLM's response
            context_docs: Retrieved context documents
            min_overlap: Minimum overlap ratio (0.0 to 1.0)
            
        Returns:
            Tuple of (is_grounded, overlap_ratio)
            - is_grounded: True if response is sufficiently grounded
            - overlap_ratio: Fraction of response words found in context
            
        Examples:
            >>> docs = [Document(page_content="Python is a programming language")]
            >>> ResponseValidator.check_context_overlap(
            ...     "Python is a language",
            ...     docs,
            ...     min_overlap=0.5
            ... )
            (True, 0.75)
        """
        if not context_docs:
            logger.warning("No context docs provided for overlap check")
            return False, 0.0
        
        # Combine all context
        context_text = " ".join([doc.page_content for doc in context_docs])
        context_lower = context_text.lower()
        
        # Get response words (excluding common stop words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", 
                      "to", "for", "of", "with", "by", "is", "are", "was", "were"}
        
        response_words = [
            word.strip('.,!?;:"\')').lower()
            for word in response.split()
            if len(word) > 2  # Ignore very short words
        ]
        
        # Filter out stop words
        meaningful_words = [
            word for word in response_words
            if word not in stop_words
        ]
        
        if not meaningful_words:
            logger.warning("No meaningful words in response")
            return False, 0.0
        
        # Count how many response words appear in context
        words_in_context = sum(
            1 for word in meaningful_words
            if word in context_lower
        )
        
        overlap_ratio = words_in_context / len(meaningful_words)
        
        is_grounded = overlap_ratio >= min_overlap
        
        logger.debug(
            "Context overlap check",
            overlap_ratio=f"{overlap_ratio:.2%}",
            is_grounded=is_grounded,
            words_checked=len(meaningful_words),
            words_in_context=words_in_context
        )
        
        return is_grounded, overlap_ratio
    
    @staticmethod
    def validate_response(
        response: str,
        context_docs: List[Document],
        check_grounding: bool = True
    ) -> Tuple[bool, Optional[str], dict]:
        """
        Comprehensive response validation.
        
        Args:
            response: The LLM's response
            context_docs: Retrieved context documents
            check_grounding: Whether to check context overlap
            
        Returns:
            Tuple of (is_valid, warning_message, metadata)
            - is_valid: True if response passes all checks
            - warning_message: Warning if validation failed (or None)
            - metadata: Dict with validation details
            
        Examples:
            >>> docs = [Document(page_content="Python is great")]
            >>> ResponseValidator.validate_response(
            ...     "Python is an amazing language",
            ...     docs
            ... )
            (True, None, {"is_rejection": False, "grounding_score": 0.5})
        """
        metadata = {}
        
        # Check if it's a rejection
        is_reject = ResponseValidator.is_rejection(response)
        metadata["is_rejection"] = is_reject
        
        if is_reject:
            logger.debug("Response is a rejection, skipping grounding check")
            return True, None, metadata
        
        # Check minimum response length
        if len(response.strip()) < 10:
            warning = "⚠️ Response seems too short, might be low quality"
            logger.warning("Response too short", length=len(response))
            metadata["warning"] = "too_short"
            return False, warning, metadata
        
        # Check context grounding
        if check_grounding and context_docs:
            is_grounded, overlap = ResponseValidator.check_context_overlap(
                response, context_docs
            )
            
            metadata["grounding_score"] = overlap
            metadata["is_grounded"] = is_grounded
            
            if not is_grounded:
                warning = (
                    f"⚠️ Low context overlap ({overlap:.1%}). "
                    "Response might contain hallucinations."
                )
                logger.warning(
                    "Poor grounding detected",
                    overlap=f"{overlap:.2%}"
                )
                return False, warning, metadata
        
        logger.debug("Response validation passed", metadata=metadata)
        return True, None, metadata
    
    @staticmethod
    def get_quality_score(response: str, context_docs: List[Document]) -> float:
        """
        Calculate an overall quality score for the response.
        
        Args:
            response: The LLM's response
            context_docs: Retrieved context documents
            
        Returns:
            Quality score from 0.0 to 1.0
            - 1.0 = Perfect response
            - 0.0 = Very poor response
        """
        score = 0.0
        
        # Length score (prefer 50-500 chars)
        length = len(response)
        if 50 <= length <= 500:
            score += 0.3
        elif 500 < length <= 1000:
            score += 0.2
        elif length < 50:
            score += 0.1
        
        # Grounding score
        if context_docs:
            _, overlap = ResponseValidator.check_context_overlap(
                response, context_docs
            )
            score += overlap * 0.5  # Up to 0.5 points
        
        # Structure score (has punctuation, proper sentences)
        has_punctuation = any(p in response for p in '.!?')
        if has_punctuation:
            score += 0.1
        
        # Not a rejection (means it actually answered)
        if not ResponseValidator.is_rejection(response):
            score += 0.1
        
        logger.debug("Quality score calculated", score=f"{score:.2f}")
        return min(score, 1.0)  # Cap at 1.0
