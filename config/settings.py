# config/settings.py
"""
Centralized configuration for the RAG system.
All tunable parameters in one place.

Environment Variables (Optional):
    - OPENAI_API_KEY: API key for OpenAI/compatible service
    - LLM_MODEL_NAME: Model name (default: gpt-4o-mini)
    - LLM_BASE_URL: Base URL for LLM API (default: OpenAI)
    - USE_CLOUD_LLM: true/false (default: true)
    - DEBUG_LOGGING: true/false (default: true)
    - ENABLE_LANGSMITH: true/false (default: false)
    - LANGCHAIN_API_KEY: LangSmith API key (if enabled)
"""
import os
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class EmbeddingConfig:
    """Configuration for embedding model"""
    model_name: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"
    # batch_size: int = 32
    normalize_embeddings: bool = True
    
@dataclass
class ChunkingConfig:
    """Configuration for text chunking"""
    chunk_size: int = 500
    chunk_overlap: int = 200
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", " ", ""])
    min_chunk_words: int = 10
    max_digit_ratio: float = 0.15

@dataclass
class RetrievalConfig:
    """Configuration for retrieval pipeline"""
    initial_k: int = 60  # Number of candidates to retrieve
    rerank_top_n: int = 10  # Number after reranking
    rerank_model: str = "ms-marco-MiniLM-L-12-v2"
    relevance_threshold: float = 0.5  # Minimum score to keep
    search_type: Literal["similarity", "mmr"] = "similarity"

@dataclass
class LLMConfig:
    """Configuration for LLM"""
    # Local LLM settings (for development/testing)
    local_model_name: str = "google/flan-t5-large"
    local_base_url: str = "http://localhost:8000/v1"
    local_api_key: str = "EMPTY"
    
    # Cloud LLM settings (OpenAI-compatible API)
    # Can be OpenAI, Azure OpenAI, or any compatible endpoint
    cloud_model_name: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    )
    cloud_base_url: str = field(
        default_factory=lambda: os.getenv(
            "LLM_BASE_URL", 
            "https://api.openai.com/v1"  # Default to OpenAI
        )
    )
    cloud_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    
    # Common settings
    temperature: float = 1.0
    streaming: bool = True
    presence_penalty: float = 0.1
    repetition_penalty: float = 1.1
    max_history_messages: int = 10

@dataclass
class PathConfig:
    """File and directory paths"""
    chroma_persist_dir: str = "./data/chroma_db"
    logs_dir: str = "./logs"
    eval_results_dir: str = "./evaluation/results"

@dataclass
class SystemConfig:
    """System-level configuration"""
    use_cloud_llm: bool = field(
        default_factory=lambda: os.getenv("USE_CLOUD_LLM", "true").lower() == "true"
    )
    enable_debug_logging: bool = field(
        default_factory=lambda: os.getenv("DEBUG_LOGGING", "true").lower() == "true"
    )
    enable_langsmith: bool = field(
        default_factory=lambda: os.getenv("ENABLE_LANGSMITH", "false").lower() == "true"
    )
    user_agent: str = "production-rag-system/4.0"
    
    # LangSmith settings (optional observability)
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = field(default_factory=lambda: os.getenv("LANGCHAIN_API_KEY", ""))

@dataclass
class Settings:
    """Master settings container"""
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    def __post_init__(self):
        """Create necessary directories"""
        os.makedirs(self.paths.chroma_persist_dir, exist_ok=True)
        os.makedirs(self.paths.logs_dir, exist_ok=True)
        os.makedirs(self.paths.eval_results_dir, exist_ok=True)
    
    def get_llm_config(self):
        """Get the appropriate LLM config based on mode."""
        if self.system.use_cloud_llm:
            return {
                "model": self.llm.cloud_model_name,
                "base_url": self.llm.cloud_base_url,
                "api_key": self.llm.cloud_api_key,
            }
        else:
            return {
                "model": self.llm.local_model_name,
                "base_url": self.llm.local_base_url,
                "api_key": self.llm.local_api_key,
            }

# Global settings instance
settings = Settings()
