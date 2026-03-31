# src/generation/rag_chain.py
"""
RAG chain assembly with error handling.
"""
from typing import Optional
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from config.prompts import REPHRASE_PROMPT, QA_PROMPT
from src.generation.llm_client import LLMClient
from src.retrieval.retriever import EnhancedRetriever
from src.utils.logging_utils import get_logger

logger = get_logger("rag_chain")


class RAGChainBuilder:
    """Build and manage RAG chains"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        retriever: EnhancedRetriever
    ):
        self.llm_client = llm_client
        self.retriever = retriever
        self.rag_chain = None
    
    def build(self):
        """Build the RAG chain"""
        logger.info("Building RAG chain...")
        
        try:
            llm = self.llm_client.get_llm()
            compression_retriever = self.retriever.get_retriever()
            
            # History-aware retriever (query reformulation)
            history_aware_retriever = create_history_aware_retriever(
                llm,
                compression_retriever,
                REPHRASE_PROMPT
            )
            
            # Document chain (answer generation)
            document_chain = create_stuff_documents_chain(llm, QA_PROMPT)
            
            # Final RAG chain
            self.rag_chain = create_retrieval_chain(
                history_aware_retriever,
                document_chain
            )
            
            logger.info("RAG chain built successfully")
            return self.rag_chain
            
        except Exception as e:
            logger.error("Failed to build RAG chain", error=str(e))
            raise
    
    def invoke(self, query: str, chat_history: list):
        """
        Invoke the RAG chain with error handling.
        
        Args:
            query: User query
            chat_history: Conversation history
            
        Returns:
            Response dict
        """
        if self.rag_chain is None:
            raise ValueError("RAG chain not built. Call build() first.")
        
        logger.info("Invoking RAG chain", query=query[:100])
        
        try:
            response = self.rag_chain.invoke({
                "input": query,
                "chat_history": chat_history
            })
            
            logger.info("RAG chain invocation successful",
                       answer_length=len(response.get("answer", "")))
            
            return response
            
        except Exception as e:
            logger.error("RAG chain invocation failed",
                        query=query[:100],
                        error=str(e))
            raise
    
    def stream(self, query: str, chat_history: list):
        """
        Stream RAG chain response.
        
        Args:
            query: User query
            chat_history: Conversation history
            
        Yields:
            Response chunks
        """
        if self.rag_chain is None:
            raise ValueError("RAG chain not built. Call build() first.")
        
        logger.info("Streaming RAG chain response", query=query[:100])
        
        try:
            for chunk in self.rag_chain.stream({
                "input": query,
                "chat_history": chat_history
            }):
                yield chunk
        except Exception as e:
            logger.error("RAG chain streaming failed",
                        query=query[:100],
                        error=str(e))
            raise
