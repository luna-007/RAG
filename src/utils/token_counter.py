# src/utils/token_counter.py
"""
Token counting utilities for cost and context window management.
"""
from typing import List, Dict
from transformers import AutoTokenizer
from langchain_classic.schema import Document
from config.settings import settings

class TokenCounter:
    """Count tokens for different models"""
    
    def __init__(self):
        self.embedding_tokenizer = AutoTokenizer.from_pretrained(
            settings.embedding.model_name,
            trust_remote_code=True
        )
        
        # Get LLM config
        llm_config = settings.get_llm_config()
        try:
            self.llm_tokenizer = AutoTokenizer.from_pretrained(
                llm_config['model'],
                trust_remote_code=True
            )
        except:
            # Fallback to embedding tokenizer if LLM tokenizer unavailable
            self.llm_tokenizer = self.embedding_tokenizer
    
    def count_tokens_text(self, text: str, model: str = "llm") -> int:
        """Count tokens in a text string"""
        tokenizer = self.llm_tokenizer if model == "llm" else self.embedding_tokenizer
        return len(tokenizer.encode(text, add_special_tokens=True))
    
    def count_tokens_documents(self, docs: List[Document], model: str = "llm") -> Dict:
        """Count tokens across multiple documents"""
        texts = [doc.page_content for doc in docs]
        tokenizer = self.llm_tokenizer if model == "llm" else self.embedding_tokenizer
        
        token_counts = [
            len(tokenizer.encode(text, add_special_tokens=True))
            for text in texts
        ]
        
        return {
            "total_tokens": sum(token_counts),
            "max_tokens": max(token_counts) if token_counts else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "avg_tokens": sum(token_counts) / len(token_counts) if token_counts else 0,
            "num_documents": len(docs)
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4") -> float:
        """Estimate cost based on token usage"""
        # Pricing as of 2024 (update as needed)
        PRICING = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-3.5-turbo": {"input": 0.0015 / 1000, "output": 0.002 / 1000},
            "local": {"input": 0, "output": 0}  # Local is free!
        }
        
        price = PRICING.get(model, PRICING["gpt-4"])
        return (input_tokens * price["input"]) + (output_tokens * price["output"])


# Standalone function for quick checks
def count_tokens(text: str) -> int:
    """Quick token count for any text"""
    counter = TokenCounter()
    return counter.count_tokens_text(text)
