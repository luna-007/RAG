# servicenow_rag.py
"""
ServiceNow Knowledge Article RAG System.
Load and query ServiceNow knowledge articles.
"""
import os
import sys
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.schema import Document

from config.settings import settings
from config.constants import CollectionNames, ErrorMessages
from src.rag_system import BaseRAGSystem
from src.loaders.servicenow_loader import ServiceNowKnowledgeLoader
from src.processors.servicenow_cleaner import ServiceNowDocumentCleaner
from src.utils.logging_utils import get_logger

logger = get_logger("servicenow_rag")


class ServiceNowRAGSystem(BaseRAGSystem):
    """
    RAG system for ServiceNow knowledge articles.
    Extends BaseRAGSystem with ServiceNow-specific loading.
    """
    
    def __init__(self):
        """Initialize ServiceNow RAG system."""
        super().__init__(collection_name=CollectionNames.SERVICENOW)
        self.sn_loader = None
        logger.info("ServiceNowRAGSystem initialized")
    
    def _load_documents(
        self,
        instance_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_token: Optional[str] = None,
        limit: int = 100,
        query: Optional[str] = None
    ) -> List[Document]:
        """
        Load documents from ServiceNow.
        
        Args:
            instance_url: ServiceNow instance URL
            username: ServiceNow username (optional if using env vars)
            password: ServiceNow password (optional if using env vars) 
            api_token: ServiceNow API token (optional)
            limit: Max number of articles to load
            query: Custom ServiceNow query filter
            
        Returns:
            List of loaded documents
            
        Raises:
            Exception: If loading fails
        """
        logger.info("Connecting to ServiceNow", instance=instance_url)
        
        try:
            # Get credentials from environment if not provided
            if not username and not api_token:
                username = os.getenv('SERVICENOW_USERNAME')
                password = os.getenv('SERVICENOW_PASSWORD')
                api_token = os.getenv('SERVICENOW_API_TOKEN')
            
            if not username and not api_token:
                raise ValueError(
                    f"{ErrorMessages.AUTH_FAILED}\n\n"
                    "Set environment variables SERVICENOW_USERNAME/PASSWORD or SERVICENOW_API_TOKEN"
                )
            
            self.sn_loader = ServiceNowKnowledgeLoader(
                instance_url=instance_url,
                username=username,
                password=password,
                api_token=api_token
            )
            
            logger.info("Loading knowledge articles", limit=limit)
            docs = self.sn_loader.load(limit=limit, query=query)
            
            logger.info(f"Loaded {len(docs)} knowledge articles")
            return docs
        
        except Exception as e:
            logger.error("Failed to load ServiceNow documents", error=str(e))
            raise
    
    def _get_cleaner(self, **kwargs):
        """
        Get ServiceNow document cleaner.
        
        Returns:
            ServiceNow document cleaner instance
        """
        cleaner = ServiceNowDocumentCleaner()
        logger.info("Using ServiceNow document cleaner")
        return cleaner
    
    def setup_from_servicenow(
        self,
        instance_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_token: Optional[str] = None,
        limit: int = 100,
        query: Optional[str] = None,
        force_rebuild: bool = False
    ) -> bool:
        """
        Setup RAG system from ServiceNow knowledge articles.
        Convenience method that calls base setup().
        
        Args:
            instance_url: ServiceNow instance URL
            username: ServiceNow username (optional if using env vars)
            password: ServiceNow password (optional if using env vars)
            api_token: ServiceNow API token (optional)
            limit: Max number of articles to load
            query: Custom ServiceNow query filter
            force_rebuild: Force rebuild even if vector store exists
            
        Returns:
            True if successful, False otherwise
        """
        return self.setup(
            force_rebuild=force_rebuild,
            instance_url=instance_url,
            username=username,
            password=password,
            api_token=api_token,
            limit=limit,
            query=query
        )



def main():
    """Main CLI interface for ServiceNow RAG."""
    print("🐶 ServiceNow Knowledge Article RAG System v4.0 (Refactored & Optimized)\n")
    
    # Get ServiceNow credentials
    print("\n=== ServiceNow Configuration ===")
    
    instance_url = input("ServiceNow instance URL (e.g., walmart.service-now.com): ").strip()
    if not instance_url.startswith('http'):
        instance_url = f"https://{instance_url}"
    
    print("\nAuthentication options:")
    print("1. Use environment variables (SERVICENOW_USERNAME/PASSWORD or SERVICENOW_API_TOKEN)")
    print("2. Enter credentials now")
    
    auth_choice = input("\nChoose option (1-2): ").strip()
    
    username = None
    password = None
    api_token = None
    
    if auth_choice == "2":
        print("\nEnter credentials:")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
    
    # Get query parameters
    limit = input("\nMax articles to load (default: 100): ").strip()
    limit = int(limit) if limit else 100
    
    custom_query = input("Custom ServiceNow query filter (optional, press Enter to skip): ").strip()
    custom_query = custom_query if custom_query else None
    
    # Check if we should rebuild
    rebuild = input("\nRebuild vector store? (y/N): ").strip().lower() == 'y'
    
    # Initialize system
    print("\n🔧 Initializing ServiceNow RAG system...")
    rag_system = ServiceNowRAGSystem()
    
    if not rag_system.setup_from_servicenow(
        instance_url=instance_url,
        username=username,
        password=password,
        api_token=api_token,
        limit=limit,
        query=custom_query,
        force_rebuild=rebuild
    ):
        print("\n❌ Failed to setup RAG system. Check logs/ for details.")
        sys.exit(1)
    
    # Chat loop
    chat_history = []
    
    print("\n✅ System ready! Ask questions about ServiceNow knowledge articles.")
    print("💡 Commands: 'exit' to quit, 'clear' to clear history, 'stats' for cache stats\n")
    
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                # Show final stats
                stats = rag_system.get_cache_stats()
                if stats['hits'] > 0 or stats['misses'] > 0:
                    print(f"\n📊 Cache Stats: {stats['hits']} hits, {stats['misses']} misses")
                    print(f"   Hit rate: {stats['hit_rate']:.1%}")
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "clear":
                chat_history = []
                print("🗑️  History cleared!")
                continue
            
            if user_input.lower() == "stats":
                stats = rag_system.get_cache_stats()
                print(f"\n📊 Cache Statistics:")
                print(f"   Size: {stats['size']} cached queries")
                print(f"   Hits: {stats['hits']}")
                print(f"   Misses: {stats['misses']}")
                print(f"   Hit rate: {stats['hit_rate']:.1%}")
                print(f"   TTL: {stats['ttl_seconds']}s")
                continue
            
            # Query the system (with validation and caching built-in)
            print("\n🤖 AI: ", end="", flush=True)
            
            answer = rag_system.query(
                user_input,
                chat_history=chat_history,
                stream=True,
                validate_response=True,
                use_cache=True
            )
            
            if answer is None:
                # Error already printed by query() method
                continue
            
            # Update history
            chat_history.extend([
                HumanMessage(content=user_input),
                AIMessage(content=answer),
            ])
            
            # Trim history if too long
            if len(chat_history) > settings.llm.max_history_messages:
                chat_history = chat_history[-settings.llm.max_history_messages:]
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error("Unexpected error in main loop", error=str(e))
            print(f"\n❌ Unexpected error: {e}")
            print("   Check logs/ directory for details.")


if __name__ == "__main__":
    main()
