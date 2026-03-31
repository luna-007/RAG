# src/retrieval/retriever.py
"""
Enhanced retrieval with relevance filtering and error handling.
"""
from typing import List, Optional, Tuple
from langchain_classic.schema import Document
from langchain_chroma import Chroma
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_classic.retrievers import ContextualCompressionRetriever
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger("retriever")


class EnhancedRetriever:
    """Retriever with reranking and relevance filtering"""
    
    def __init__(self, vectorstore: Chroma):
        self.vectorstore = vectorstore
        self.compression_retriever = None
        self._setup_retriever()
    
    def _setup_retriever(self):
        """Setup retrieval pipeline with reranking"""
        logger.info("Setting up retrieval pipeline...")
        
        try:
            # Reranker
            compressor = FlashrankRerank(
                model=settings.retrieval.rerank_model,
                top_n=settings.retrieval.rerank_top_n
            )
            
            # Base retriever
            base_retriever = self.vectorstore.as_retriever(
                search_type=settings.retrieval.search_type,
                search_kwargs={"k": settings.retrieval.initial_k}
            )
            
            # Compression retriever (combines base + reranker)
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
            
            logger.info("Retrieval pipeline ready",
                       initial_k=settings.retrieval.initial_k,
                       rerank_top_n=settings.retrieval.rerank_top_n)
            
        except Exception as e:
            logger.error("Failed to setup retriever", error=str(e))
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def retrieve(self, query: str) -> List[Document]:
        """
        Retrieve documents for a query with retry logic.
        
        Args:
            query: Search query
            
        Returns:
            List of retrieved documents
        """
        logger.info("Retrieving documents", query=query[:100])
        
        try:
            docs = self.compression_retriever.get_relevant_documents(query)
            
            logger.info("Documents retrieved",
                       query=query[:100],
                       num_docs=len(docs))
            
            return docs
            
        except Exception as e:
            logger.error("Retrieval failed", query=query[:100], error=str(e))
            raise
    
    def retrieve_with_filter(
        self,
        query: str,
        min_score: Optional[float] = None
    ) -> Tuple[Optional[List[Document]], Optional[str]]:
        """
        Retrieve with relevance threshold filtering.
        
        Args:
            query: Search query
            min_score: Minimum relevance score (uses config default if None)
            
        Returns:
            Tuple of (documents, error_message)
            - If successful: (docs, None)
            - If no relevant docs: (None, error_message)
        """
        if min_score is None:
            min_score = settings.retrieval.relevance_threshold
        
        logger.info("Retrieving with filter",
                   query=query[:100],
                   min_score=min_score)
        
        try:
            docs = self.retrieve(query)
            
            # Filter by relevance score
            relevant_docs = [
                doc for doc in docs
                if doc.metadata.get('relevance_score', 0) >= min_score
            ]
            
            if not relevant_docs:
                logger.warning("No relevant documents found",
                              query=query[:100],
                              min_score=min_score,
                              candidates=len(docs))
                return None, "I don't have relevant information about that in my knowledge base."
            
            logger.info("Relevant documents found",
                       query=query[:100],
                       relevant=len(relevant_docs),
                       total=len(docs))
            
            return relevant_docs, None
            
        except Exception as e:
            logger.error("Retrieval with filter failed",
                        query=query[:100],
                        error=str(e))
            return None, f"An error occurred during retrieval: {str(e)}"
    
    def get_retriever(self):
        """Get the underlying retriever for chain building"""
        return self.compression_retriever
