# src/retrieval/vectorstore.py
"""
Vector store management with error handling and persistence.
"""
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_classic.schema import Document
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger("vectorstore")


class VectorStoreManager:
    """Manages vector store operations with error handling"""
    
    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self.embeddings = None
        self.vectorstore = None
        logger.info("VectorStoreManager initialized", collection=collection_name)
    
    def _initialize_embeddings(self):
        """Initialize embedding model with retry logic"""
        if self.embeddings is not None:
            return
        
        logger.info("Initializing embeddings...", model=settings.embedding.model_name)
        
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding.model_name,
                model_kwargs={
                    'device': settings.embedding.device,
                    # 'batch_size': settings.embedding.batch_size
                },
                encode_kwargs={'normalize_embeddings': settings.embedding.normalize_embeddings}
            )
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize embeddings", error=str(e))
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_from_documents(
        self,
        documents: List[Document],
        persist: bool = True
    ) -> Chroma:
        """
        Create vector store from documents with retry logic.
        
        Args:
            documents: List of documents to embed
            persist: Whether to persist to disk
            
        Returns:
            Chroma vector store instance
        """
        self._initialize_embeddings()
        
        logger.info("Creating vector store...", 
                   num_docs=len(documents),
                   persist=persist)
        
        try:
            if persist:
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=settings.paths.chroma_persist_dir,
                    collection_name=self.collection_name,
                    collection_metadata={"hnsw:space": "cosine"}
                )
            else:
                # In-memory only
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=self.collection_name,
                    collection_metadata={"hnsw:space": "cosine"}
                )
            
            logger.info("Vector store created successfully")
            return self.vectorstore
            
        except Exception as e:
            logger.error("Failed to create vector store", error=str(e))
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def load_existing(self) -> Optional[Chroma]:
        """
        Load existing vector store from disk.
        
        Returns:
            Loaded Chroma instance or None if not found
        """
        self._initialize_embeddings()
        
        logger.info("Loading existing vector store...", 
                   path=settings.paths.chroma_persist_dir,
                   collection=self.collection_name)
        
        try:
            self.vectorstore = Chroma(
                persist_directory=settings.paths.chroma_persist_dir,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
            
            # Check if it has documents
            count = self.vectorstore._collection.count()
            
            if count == 0:
                logger.warning("Vector store exists but is empty")
                return None
            
            logger.info("Vector store loaded successfully", document_count=count)
            return self.vectorstore
            
        except Exception as e:
            logger.warning("Could not load existing vector store", error=str(e))
            return None
    
    def add_documents(self, documents: List[Document]):
        """Add documents to existing vector store"""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call create_from_documents() first.")
        
        logger.info("Adding documents to vector store...", num_docs=len(documents))
        
        try:
            self.vectorstore.add_documents(documents)
            logger.info("Documents added successfully")
        except Exception as e:
            logger.error("Failed to add documents", error=str(e))
            raise
    
    def get_vectorstore(self) -> Chroma:
        """Get the vector store instance"""
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized")
        return self.vectorstore
