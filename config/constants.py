# config/constants.py
"""
Centralized constants and enums for the RAG system.
No more magic strings scattered everywhere!
"""
from enum import Enum


class CollectionNames:
    """Vector store collection names"""
    MAIN = "main"
    SERVICENOW = "servicenow"
    NEWS = "news"
    CUSTOM = "custom"


class VectorStoreType(Enum):
    """Supported vector store backends"""
    CHROMA = "chroma"
    FAISS = "faiss"
    PINECONE = "pinecone"
    QDRANT = "qdrant"


class ChunkingStrategy(Enum):
    """Document chunking strategies"""
    FIXED = "fixed"  # Fixed size chunks
    SEMANTIC = "semantic"  # Semantic-based chunking
    HYBRID = "hybrid"  # Mix of both


class LogLevel:
    """Logging level constants"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorMessages:
    """User-friendly error messages"""
    
    # Setup errors
    NO_DOCUMENTS_LOADED = (
        "❌ Failed to load documents. Please check:\n"
        "  → URL is accessible\n"
        "  → Internet connection is working\n"
        "  → URL contains actual content"
    )
    
    NO_DOCUMENTS_AFTER_CLEANING = (
        "❌ No documents remained after cleaning. This might mean:\n"
        "  → Source content was too short\n"
        "  → Content was filtered as low-quality\n"
        "  → Try a different source URL"
    )
    
    NO_CHUNKS_AFTER_FILTERING = (
        "❌ No chunks remained after filtering. This could be because:\n"
        "  → Chunk size is too large for the content\n"
        "  → Quality filters are too strict\n"
        "  → Content doesn't meet minimum quality thresholds"
    )
    
    # Authentication errors
    AUTH_FAILED = (
        "❌ Authentication failed. Please check:\n"
        "  → Username and password are correct\n"
        "  → API token is valid and not expired\n"
        "  → Account has necessary permissions"
    )
    
    # Vector store errors
    VECTORSTORE_INIT_FAILED = (
        "❌ Failed to initialize vector store. Possible causes:\n"
        "  → Insufficient disk space\n"
        "  → Corrupt existing database\n"
        "  → Try deleting data/chroma_db/ and rebuilding"
    )
    
    # LLM errors
    LLM_INIT_FAILED = (
        "❌ Failed to initialize LLM. Check:\n"
        "  → API key is set correctly\n"
        "  → Endpoint URL is accessible\n"
        "  → Internet connection is working"
    )
    
    LLM_QUERY_FAILED = (
        "❌ Query failed. This could be:\n"
        "  → Temporary network issue (try again)\n"
        "  → API rate limit reached (wait a moment)\n"
        "  → Service outage (check status page)"
    )
    
    # Retrieval errors
    RETRIEVAL_FAILED = (
        "❌ Document retrieval failed. Possible reasons:\n"
        "  → Vector store is corrupted\n"
        "  → Embeddings model is unavailable\n"
        "  → Try rebuilding the vector store"
    )
    
    # Input validation errors
    QUERY_TOO_LONG = (
        "❌ Query is too long (max 1000 characters).\n"
        "  → Please shorten your question\n"
        "  → Break complex queries into multiple questions"
    )
    
    QUERY_EMPTY = (
        "❌ Query cannot be empty.\n"
        "  → Please ask a question"
    )
    
    # Generic fallback
    GENERIC_ERROR = (
        "❌ An unexpected error occurred.\n"
        "  → Check logs/ directory for details\n"
        "  → Try restarting the system\n"
        "  → Report persistent issues"
    )


class RejectionPhrases:
    """Phrases indicating the model couldn't answer"""
    PHRASES = [
        "don't have",
        "no information",
        "cannot answer",
        "not in my knowledge",
        "insufficient context",
        "unable to find",
        "not available",
    ]


class ValidationRules:
    """Input validation rules"""
    MAX_QUERY_LENGTH = 1000
    MIN_QUERY_LENGTH = 3
    MAX_CHUNK_SIZE = 2000
    MIN_CHUNK_SIZE = 50
    MAX_DOCUMENTS_PER_BATCH = 1000
    
    # Security patterns (basic injection detection)
    SUSPICIOUS_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onclick=",
        "eval(",
        "exec(",
    ]


class CacheConfig:
    """Cache configuration"""
    MAX_CACHE_SIZE = 1000  # Max cached queries
    CACHE_TTL_SECONDS = 3600  # 1 hour
    ENABLE_EMBEDDING_CACHE = True
    ENABLE_QUERY_CACHE = True
