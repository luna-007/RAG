# src/retrieval/vectorstore_factory.py
"""
Factory pattern for vector store creation.
Supports multiple backends (Chroma, FAISS, Pinecone, Qdrant).
"""
from typing import List, Optional
from langchain_classic.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
from config.constants import VectorStoreType
from src.utils.logging_utils import get_logger

logger = get_logger("vectorstore_factory")


class VectorStoreFactory:
    """
    Factory for creating different types of vector stores.
    Abstracts away implementation details of each backend.
    """
    
    def __init__(self, store_type: VectorStoreType = VectorStoreType.CHROMA):
        """
        Initialize vector store factory.
        
        Args:
            store_type: Type of vector store to create
        """
        self.store_type = store_type
        self.embeddings = None
        logger.info("Vector store factory initialized", type=store_type.value)
    
    def _initialize_embeddings(self):
        """Initialize embedding model (shared across all stores)"""
        if self.embeddings is not None:
            return
        
        logger.info("Initializing embeddings", model=settings.embedding.model_name)
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding.model_name,
            model_kwargs={'device': settings.embedding.device},
            encode_kwargs={'normalize_embeddings': settings.embedding.normalize_embeddings}
        )
        
        logger.info("Embeddings initialized")
    
    def create_from_documents(
        self,
        documents: List[Document],
        collection_name: str = "default",
        persist: bool = True,
        **kwargs
    ):
        """
        Create vector store from documents.
        
        Args:
            documents: Documents to embed and store
            collection_name: Name for the collection/index
            persist: Whether to persist to disk/cloud
            **kwargs: Additional store-specific arguments
            
        Returns:
            Vector store instance (type depends on store_type)
            
        Raises:
            ValueError: If store type is not supported
        """
        self._initialize_embeddings()
        
        logger.info(
            "Creating vector store",
            type=self.store_type.value,
            num_docs=len(documents),
            persist=persist
        )
        
        if self.store_type == VectorStoreType.CHROMA:
            return self._create_chroma(documents, collection_name, persist, **kwargs)
        
        elif self.store_type == VectorStoreType.FAISS:
            return self._create_faiss(documents, collection_name, persist, **kwargs)
        
        elif self.store_type == VectorStoreType.PINECONE:
            return self._create_pinecone(documents, collection_name, **kwargs)
        
        elif self.store_type == VectorStoreType.QDRANT:
            return self._create_qdrant(documents, collection_name, **kwargs)
        
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    def _create_chroma(
        self,
        documents: List[Document],
        collection_name: str,
        persist: bool,
        **kwargs
    ):
        """Create Chroma vector store"""
        from langchain_chroma import Chroma
        
        logger.info("Creating Chroma vector store")
        
        if persist:
            return Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=settings.paths.chroma_persist_dir,
                collection_name=collection_name,
                collection_metadata={"hnsw:space": "cosine"}
            )
        else:
            return Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                collection_metadata={"hnsw:space": "cosine"}
            )
    
    def _create_faiss(
        self,
        documents: List[Document],
        collection_name: str,
        persist: bool,
        **kwargs
    ):
        """Create FAISS vector store"""
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            raise ImportError(
                "FAISS not installed. Install with: pip install faiss-cpu"
            )
        
        logger.info("Creating FAISS vector store")
        
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        if persist:
            import os
            persist_path = os.path.join(
                settings.paths.chroma_persist_dir.replace("chroma_db", "faiss_db"),
                collection_name
            )
            os.makedirs(persist_path, exist_ok=True)
            vectorstore.save_local(persist_path)
            logger.info("FAISS index saved", path=persist_path)
        
        return vectorstore
    
    def _create_pinecone(
        self,
        documents: List[Document],
        collection_name: str,
        **kwargs
    ):
        """Create Pinecone vector store"""
        try:
            from langchain_pinecone import PineconeVectorStore
            import pinecone
        except ImportError:
            raise ImportError(
                "Pinecone not installed. Install with: pip install pinecone-client langchain-pinecone"
            )
        
        logger.info("Creating Pinecone vector store")
        
        # Note: Requires PINECONE_API_KEY in environment
        index_name = kwargs.get('index_name', collection_name)
        
        return PineconeVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            index_name=index_name
        )
    
    def _create_qdrant(
        self,
        documents: List[Document],
        collection_name: str,
        **kwargs
    ):
        """Create Qdrant vector store"""
        try:
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
        except ImportError:
            raise ImportError(
                "Qdrant not installed. Install with: pip install qdrant-client langchain-qdrant"
            )
        
        logger.info("Creating Qdrant vector store")
        
        # Can use in-memory or persistent
        url = kwargs.get('url', ':memory:')
        
        client = QdrantClient(url=url)
        
        return QdrantVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=collection_name,
            client=client
        )
    
    def load_existing(
        self,
        collection_name: str = "default",
        **kwargs
    ) -> Optional[object]:
        """
        Load existing vector store.
        
        Args:
            collection_name: Name of collection to load
            **kwargs: Store-specific arguments
            
        Returns:
            Loaded vector store or None if not found
        """
        self._initialize_embeddings()
        
        logger.info(
            "Loading existing vector store",
            type=self.store_type.value,
            collection=collection_name
        )
        
        try:
            if self.store_type == VectorStoreType.CHROMA:
                return self._load_chroma(collection_name)
            
            elif self.store_type == VectorStoreType.FAISS:
                return self._load_faiss(collection_name)
            
            elif self.store_type == VectorStoreType.PINECONE:
                return self._load_pinecone(collection_name, **kwargs)
            
            elif self.store_type == VectorStoreType.QDRANT:
                return self._load_qdrant(collection_name, **kwargs)
            
            else:
                logger.error("Unsupported store type", type=self.store_type)
                return None
        
        except Exception as e:
            logger.warning("Failed to load existing store", error=str(e))
            return None
    
    def _load_chroma(self, collection_name: str):
        """Load existing Chroma store"""
        from langchain_chroma import Chroma
        
        vectorstore = Chroma(
            persist_directory=settings.paths.chroma_persist_dir,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        
        # Check if has documents
        if vectorstore._collection.count() == 0:
            logger.warning("Chroma store is empty")
            return None
        
        logger.info("Chroma store loaded", count=vectorstore._collection.count())
        return vectorstore
    
    def _load_faiss(self, collection_name: str):
        """Load existing FAISS store"""
        from langchain_community.vectorstores import FAISS
        import os
        
        persist_path = os.path.join(
            settings.paths.chroma_persist_dir.replace("chroma_db", "faiss_db"),
            collection_name
        )
        
        if not os.path.exists(persist_path):
            logger.warning("FAISS index not found", path=persist_path)
            return None
        
        vectorstore = FAISS.load_local(
            persist_path,
            self.embeddings,
            allow_dangerous_deserialization=True  # Required for FAISS
        )
        
        logger.info("FAISS store loaded", path=persist_path)
        return vectorstore
    
    def _load_pinecone(self, collection_name: str, **kwargs):
        """Load existing Pinecone store"""
        from langchain_pinecone import PineconeVectorStore
        
        index_name = kwargs.get('index_name', collection_name)
        
        vectorstore = PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings
        )
        
        logger.info("Pinecone store loaded", index=index_name)
        return vectorstore
    
    def _load_qdrant(self, collection_name: str, **kwargs):
        """Load existing Qdrant store"""
        from langchain_qdrant import QdrantVectorStore
        from qdrant_client import QdrantClient
        
        url = kwargs.get('url', 'http://localhost:6333')
        client = QdrantClient(url=url)
        
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=self.embeddings
        )
        
        logger.info("Qdrant store loaded", collection=collection_name)
        return vectorstore
