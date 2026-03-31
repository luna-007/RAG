# src/generation/llm_client.py
"""
LLM client with abstraction for local vs cloud models.
Supports any OpenAI-compatible API endpoint.
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger("llm_client")


class LLMClient:
    """
    LLM client with support for local and Element Gateway.
    Handles initialization, error handling, and mode switching.
    """
    
    def __init__(self, use_cloud: Optional[bool] = None):
        """
        Initialize LLM client.
        
        Args:
            use_cloud: Override settings to use cloud LLM (default: from settings)
        """
        self.use_cloud = use_cloud if use_cloud is not None else settings.system.use_cloud_llm
        self.llm = None
        self._initialize_llm()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _initialize_llm(self):
        """Initialize LLM with retry logic."""
        llm_config = settings.get_llm_config()
        
        mode = "Cloud" if self.use_cloud else "Local"
        logger.info(f"Initializing LLM in {mode} mode",
                   model=llm_config['model'],
                   base_url=llm_config['base_url'])
        
        try:
            # Build model kwargs conditionally
            model_kwargs = {}
            
            # Only add extra_body for local models (may not be supported by all APIs)
            if not self.use_cloud:
                model_kwargs["extra_body"] = {
                    "repetition_penalty": settings.llm.repetition_penalty
                }
            
            self.llm = ChatOpenAI(
                model=llm_config['model'],
                base_url=llm_config['base_url'],
                api_key=llm_config['api_key'],
                temperature=settings.llm.temperature,
                streaming=settings.llm.streaming,
                presence_penalty=settings.llm.presence_penalty,
                model_kwargs=model_kwargs,
            )
            
            logger.info("LLM initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize LLM", error=str(e))
            raise
    
    def get_llm(self) -> ChatOpenAI:
        """Get the LLM instance"""
        if self.llm is None:
            raise ValueError("LLM not initialized")
        return self.llm
    
    def switch_mode(self, use_cloud: bool):
        """
        Switch between local and cloud LLM.
        
        Args:
            use_cloud: True for cloud, False for local
        """
        if use_cloud == self.use_cloud:
            logger.info("Already in requested mode", use_cloud=use_cloud)
            return
        
        logger.info("Switching LLM mode",
                   from_mode="Cloud" if self.use_cloud else "Local",
                   to_mode="Cloud" if use_cloud else "Local")
        
        self.use_cloud = use_cloud
        self._initialize_llm()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def invoke(self, messages, **kwargs):
        """
        Invoke LLM with retry logic.
        
        Args:
            messages: Messages to send to LLM
            **kwargs: Additional arguments
            
        Returns:
            LLM response
        """
        try:
            response = self.llm.invoke(messages, **kwargs)
            logger.debug("LLM invocation successful")
            return response
        except Exception as e:
            logger.error("LLM invocation failed", error=str(e))
            raise
    
    def stream(self, messages, **kwargs):
        """
        Stream LLM response with error handling.
        
        Args:
            messages: Messages to send
            **kwargs: Additional arguments
            
        Yields:
            Response chunks
        """
        try:
            for chunk in self.llm.stream(messages, **kwargs):
                yield chunk
        except Exception as e:
            logger.error("LLM streaming failed", error=str(e))
            raise
