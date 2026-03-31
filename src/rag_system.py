# src/rag_system.py
"""
Base RAG system with shared functionality.
Eliminates code duplication between different RAG implementations.
"""
import os
import time
from abc import ABC, abstractmethod
from typing import Optional, List
from transformers import AutoTokenizer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.schema import Document

from config.settings import settings
from config.constants import ErrorMessages, CollectionNames
from src.retrieval.vectorstore import VectorStoreManager
from src.retrieval.retriever import EnhancedRetriever
from src.generation.llm_client import LLMClient
from src.generation.rag_chain import RAGChainBuilder
from src.utils.logging_utils import get_logger
from src.utils.token_counter import TokenCounter
from src.utils.validators import InputValidator, validate_and_handle
from src.utils.response_validator import ResponseValidator
from src.utils.cache import query_cache

logger = get_logger("rag_system")


class BaseRAGSystem(ABC):
    """
    Abstract base class for RAG systems.
    Provides shared functionality and defines interface for subclasses.
    
    Subclasses must implement:
        - _load_documents(): Load documents from source
        - _get_cleaner(): Get appropriate document cleaner
    """
    
    def __init__(self, collection_name: str = CollectionNames.MAIN):
        """
        Initialize base RAG system.
        
        Args:
            collection_name: Name for vector store collection
        """
        self.collection_name = collection_name
        self.vectorstore_manager: Optional[VectorStoreManager] = None
        self.retriever: Optional[EnhancedRetriever] = None
        self.llm_client: Optional[LLMClient] = None
        self.rag_chain_builder: Optional[RAGChainBuilder] = None
        self.rag_chain = None
        self.token_counter = TokenCounter()
        self.validator = InputValidator()
        
        # Setup LangSmith if enabled
        if settings.system.enable_langsmith:
            os.environ['LANGCHAIN_TRACING_V2'] = 'true'
            os.environ['LANGCHAIN_ENDPOINT'] = settings.system.langsmith_endpoint
            os.environ['LANGCHAIN_API_KEY'] = settings.system.langsmith_api_key
        
        os.environ['USER_AGENT'] = settings.system.user_agent
        
        logger.info("BaseRAGSystem initialized", collection=collection_name)
    
    @abstractmethod
    def _load_documents(self, **kwargs) -> List[Document]:
        """
        Load documents from source.
        Must be implemented by subclasses.
        
        Args:
            **kwargs: Source-specific parameters
            
        Returns:
            List of loaded documents
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _load_documents()")
    
    @abstractmethod
    def _get_cleaner(self, **kwargs):
        """
        Get appropriate document cleaner for the source.
        Must be implemented by subclasses.
        
        Args:
            **kwargs: Source-specific parameters
            
        Returns:
            Document cleaner instance
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _get_cleaner()")
    
    def setup(
        self,
        force_rebuild: bool = False,
        **load_kwargs
    ) -> bool:
        """
        Setup RAG system (shared logic for all implementations).
        
        Args:
            force_rebuild: Force rebuild even if vector store exists
            **load_kwargs: Arguments passed to _load_documents()
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting RAG setup", force_rebuild=force_rebuild)
        
        try:
            # Try to load existing vector store first
            if not force_rebuild:
                logger.info("Attempting to load existing vector store...")
                self.vectorstore_manager = VectorStoreManager(
                    collection_name=self.collection_name
                )
                vectorstore = self.vectorstore_manager.load_existing()
                
                if vectorstore is not None:
                    logger.info("Using existing vector store")
                    self._setup_retrieval_and_generation()
                    return True
            
            # Build new vector store
            logger.info("Building new vector store...")
            
            # Load documents (subclass-specific)
            logger.info("Loading documents...")
            docs = self._load_documents(**load_kwargs)
            
            if not docs:
                logger.error("No documents loaded")
                print(f"\n{ErrorMessages.NO_DOCUMENTS_LOADED}")
                return False
            
            logger.info(f"Loaded {len(docs)} documents")
            
            # Clean documents (subclass-specific)
            logger.info("Cleaning documents...")
            cleaner = self._get_cleaner(**load_kwargs)
            docs = cleaner.clean_documents(docs)
            
            if not docs:
                logger.error("No documents after cleaning")
                print(f"\n{ErrorMessages.NO_DOCUMENTS_AFTER_CLEANING}")
                return False
            
            # Split into chunks
            chunks = self._split_documents(docs)
            
            if not chunks:
                logger.error("No chunks created")
                return False
            
            # Filter chunks
            logger.info("Filtering chunks...")
            filtered_chunks = cleaner.filter_chunks(chunks)
            
            if not filtered_chunks:
                logger.error("No chunks after filtering")
                print(f"\n{ErrorMessages.NO_CHUNKS_AFTER_FILTERING}")
                return False
            
            logger.info(f"Kept {len(filtered_chunks)} chunks after filtering")
            
            # Token statistics
            token_stats = self.token_counter.count_tokens_documents(
                filtered_chunks,
                model="embedding"
            )
            logger.info("Token statistics", **token_stats)
            
            # Create vector store
            logger.info("Creating vector store...")
            self.vectorstore_manager = VectorStoreManager(
                collection_name=self.collection_name
            )
            self.vectorstore_manager.create_from_documents(
                filtered_chunks,
                persist=True
            )
            
            # Setup retrieval and generation
            self._setup_retrieval_and_generation()
            
            logger.info("RAG setup complete!")
            return True
        
        except Exception as e:
            logger.error("RAG setup failed", error=str(e))
            print(f"\n{ErrorMessages.GENERIC_ERROR}")
            print(f"Error: {e}")
            return False
    
    def _split_documents(self, docs: List[Document]) -> List[Document]:
        """
        Split documents into chunks (shared logic).
        
        Args:
            docs: Documents to split
            
        Returns:
            List of document chunks
        """
        logger.info("Splitting documents...")
        
        tokenizer = AutoTokenizer.from_pretrained(
            settings.embedding.model_name,
            trust_remote_code=True
        )
        
        text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer,
            chunk_size=settings.chunking.chunk_size,
            chunk_overlap=settings.chunking.chunk_overlap,
            separators=settings.chunking.separators
        )
        
        splits = text_splitter.split_documents(docs)
        logger.info(f"Created {len(splits)} chunks")
        
        return splits
    
    def _setup_retrieval_and_generation(self):
        """
        Setup retrieval and generation components (shared logic).
        
        Raises:
            Exception: If setup fails
        """
        logger.info("Setting up retrieval and generation...")
        
        try:
            # Get vectorstore
            vectorstore = self.vectorstore_manager.get_vectorstore()
            
            # Setup retriever
            self.retriever = EnhancedRetriever(vectorstore)
            
            # Setup LLM
            self.llm_client = LLMClient()
            
            # Build RAG chain
            self.rag_chain_builder = RAGChainBuilder(
                self.llm_client,
                self.retriever
            )
            self.rag_chain = self.rag_chain_builder.build()
            
            logger.info("Retrieval and generation setup complete")
        
        except Exception as e:
            logger.error("Failed to setup retrieval/generation", error=str(e))
            raise
    
    def query(
        self,
        query: str,
        chat_history: Optional[List] = None,
        stream: bool = True,
        validate_response: bool = True,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Query the RAG system with validation and caching.
        
        Args:
            query: User query
            chat_history: Conversation history (defaults to empty list)
            stream: Whether to stream response
            validate_response: Whether to validate response quality
            use_cache: Whether to use query cache
            
        Returns:
            Response string or None if failed
        """
        if chat_history is None:
            chat_history = []
        
        # Validate input
        is_valid, error_msg = self.validator.validate_query(query)
        if not is_valid:
            print(f"\n{error_msg}")
            return None
        
        # Check cache
        if use_cache:
            cached_response = query_cache.get(query)
            if cached_response:
                logger.info("Returning cached response")
                if stream:
                    # Simulate streaming for cached response
                    for char in cached_response:
                        print(char, end="", flush=True)
                        time.sleep(0.001)  # Tiny delay for visual effect
                    print()  # Newline
                return cached_response
        
        if self.rag_chain is None:
            logger.error("RAG chain not initialized")
            print(f"\n{ErrorMessages.GENERIC_ERROR}")
            return None
        
        start_time = time.time()
        logger.info("Processing query", query=query[:100])
        
        try:
            if stream:
                # Streaming mode
                full_answer = ""
                for chunk in self.rag_chain_builder.stream(query, chat_history):
                    if "answer" in chunk:
                        token = chunk["answer"]
                        print(token, end="", flush=True)
                        full_answer += token
                
                print()  # Newline after streaming
                
                elapsed = time.time() - start_time
                logger.info(
                    "Query completed (streaming)",
                    query=query[:100],
                    response_length=len(full_answer),
                    elapsed_seconds=elapsed
                )
                
                # Validate response if requested
                if validate_response and full_answer:
                    self._validate_and_warn(full_answer)
                
                # Cache successful response
                if use_cache and full_answer:
                    query_cache.set(query, full_answer)
                
                return full_answer
            
            else:
                # Non-streaming mode
                response = self.rag_chain_builder.invoke(query, chat_history)
                answer = response.get("answer", "")
                
                elapsed = time.time() - start_time
                logger.info(
                    "Query completed",
                    query=query[:100],
                    response_length=len(answer),
                    elapsed_seconds=elapsed
                )
                
                # Validate response if requested
                if validate_response and answer:
                    self._validate_and_warn(answer)
                
                # Cache successful response
                if use_cache and answer:
                    query_cache.set(query, answer)
                
                return answer
        
        except Exception as e:
            logger.error("Query failed", query=query[:100], error=str(e))
            print(f"\n{ErrorMessages.LLM_QUERY_FAILED}")
            return None
    
    def _validate_and_warn(self, response: str):
        """
        Validate response and print warning if needed.
        
        Args:
            response: LLM response to validate
        """
        # Note: We don't have context_docs here in streaming,
        # but we can still do basic validation
        is_valid, warning, metadata = ResponseValidator.validate_response(
            response,
            context_docs=[],  # TODO: Expose context from retrieval
            check_grounding=False  # Skip grounding check for now
        )
        
        if not is_valid and warning:
            print(f"\n{warning}")
            logger.warning("Response validation warning", metadata=metadata)
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return query_cache.get_stats()
    
    def clear_cache(self):
        """Clear query cache"""
        query_cache.clear()
        logger.info("Cache cleared")
