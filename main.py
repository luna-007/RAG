# main.py
"""
Web-based RAG system.
Loads documents from URLs and enables Q&A.
"""
import sys
from typing import List
import bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_classic.schema import Document
from langchain_core.messages import HumanMessage, AIMessage

from config.settings import settings
from config.constants import CollectionNames
from src.rag_system import BaseRAGSystem
from src.processors.cleaner_factory import get_cleaner_for_url
from src.utils.logging_utils import get_logger
from src.utils.validators import InputValidator, validate_and_handle

logger = get_logger("main")


class WebRAGSystem(BaseRAGSystem):
    """
    RAG system for web-based documents.
    Extends BaseRAGSystem with URL loading functionality.
    """
    
    def __init__(self):
        """Initialize web RAG system."""
        super().__init__(collection_name=CollectionNames.MAIN)
        self.url = None
        logger.info("WebRAGSystem initialized")
    
    def _load_documents(self, url: str) -> List[Document]:
        """
        Load documents from a URL.
        
        Args:
            url: Web URL to load documents from
            
        Returns:
            List of loaded documents
            
        Raises:
            Exception: If loading fails
        """
        # Validate URL
        validator = InputValidator()
        if not validate_and_handle(validator.validate_url(url)):
            return []
        
        self.url = url
        
        logger.info("Loading web documents", url=url)
        
        try:
            loader = WebBaseLoader(
                web_paths=(url,),
                bs_kwargs=dict(
                    parse_only=bs4.SoupStrainer(["h1", "h2", "h3", "p", "article"])
                )
            )
            docs = loader.load()
            
            logger.info(f"Loaded {len(docs)} documents from web")
            return docs
        
        except Exception as e:
            logger.error("Failed to load web documents", url=url, error=str(e))
            raise
    
    def _get_cleaner(self, url: str):
        """
        Get appropriate cleaner for the URL.
        
        Args:
            url: The URL being processed
            
        Returns:
            Document cleaner instance
        """
        # Get content preview for cleaner detection
        content = ""
        if hasattr(self, '_loaded_docs') and self._loaded_docs:
            content = self._loaded_docs[0].page_content
        
        cleaner = get_cleaner_for_url(url, content=content)
        logger.info(f"Using cleaner: {cleaner.__class__.__name__}")
        
        return cleaner
    
    def setup_from_url(self, url: str, force_rebuild: bool = False) -> bool:
        """
        Setup RAG system from a URL.
        Convenience method that calls base setup().
        
        Args:
            url: Document URL
            force_rebuild: Force rebuild even if vector store exists
            
        Returns:
            True if successful, False otherwise
        """
        return self.setup(force_rebuild=force_rebuild, url=url)


def main():
    """Main CLI interface."""
    print("🐶 Production RAG System v4.0 (Refactored & Optimized)\n")
    
    # Get document URL
    print("Example sources:")
    print("1. Wikipedia: https://en.wikipedia.org/wiki/India")
    print("2. BBC News: https://www.bbc.com/news")
    print("3. Custom URL\n")
    
    choice = input("Select source (1-3) or paste URL: ").strip()
    
    if choice == "1":
        url = "https://en.wikipedia.org/wiki/India"
    elif choice == "2":
        url = "https://www.bbc.com/news"
    elif choice == "3":
        url = input("Enter URL: ").strip()
    else:
        url = choice
    
    # Check if we should rebuild
    rebuild = input("\nRebuild vector store? (y/N): ").strip().lower() == 'y'
    
    # Initialize system
    print("\n🔧 Initializing RAG system...")
    rag_system = WebRAGSystem()
    
    if not rag_system.setup_from_url(url, force_rebuild=rebuild):
        print("\n❌ Failed to setup RAG system. Check logs/ for details.")
        sys.exit(1)
    
    # Chat loop
    chat_history = []
    
    print("\n✅ System ready! Ask questions.")
    print(f"📊 Config: chunk_size={settings.chunking.chunk_size}, k={settings.retrieval.initial_k}")
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
                    print(f"\n📊 Cache Stats: {stats['hits']} hits, {stats['misses']} misses ")
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
