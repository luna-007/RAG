# Quick Reference Guide

Fast lookups for common tasks in the Production RAG System.

---

## 🚀 Common Tasks

### Start the System

```bash
# Web RAG
python main.py

# ServiceNow RAG
python servicenow_rag.py
```

### Check Cache Statistics

```python
stats = rag_system.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Size: {stats['size']} queries")
```

Or during chat:
```
🧑 You: stats
```

### Clear Cache

```python
rag_system.clear_cache()
```

### Switch Vector Store Backend

```python
from config.constants import VectorStoreType
from src.retrieval.vectorstore_factory import VectorStoreFactory

factory = VectorStoreFactory(store_type=VectorStoreType.FAISS)
vectorstore = factory.create_from_documents(docs, persist=True)
```

### Validate User Input

```python
from src.utils.validators import InputValidator

validator = InputValidator()
is_valid, error = validator.validate_query(user_input)

if not is_valid:
    print(error)
else:
    # Process query
    ...
```

### Check Response Quality

```python
from src.utils.response_validator import ResponseValidator

quality = ResponseValidator.get_quality_score(response, context_docs)
print(f"Quality: {quality:.2f}/1.0")

is_grounded, overlap = ResponseValidator.check_context_overlap(
    response, context_docs
)
print(f"Grounding: {overlap:.1%}")
```

---

## ⚙️ Configuration

### Change Chunk Size

```python
# In config/settings.py
chunk_size: int = 700  # Increase from 500
chunk_overlap: int = 150  # Adjust overlap
```

### Change Retrieval Settings

```python
# In config/settings.py
initial_k: int = 80  # Retrieve more candidates
rerank_top_n: int = 15  # Keep more after reranking
relevance_threshold: float = 0.6  # Stricter filtering
```

### Change Cache Settings

```python
# In config/constants.py
class CacheConfig:
    MAX_CACHE_SIZE = 2000  # More cache entries
    CACHE_TTL_SECONDS = 7200  # 2 hours instead of 1
```

### Use Different LLM

```bash
# In .env
OPENAI_API_KEY=sk-your-key
LLM_MODEL_NAME=gpt-4o  # Change model
LLM_BASE_URL=https://api.openai.com/v1
```

---

## 🛠️ Extending the System

### Add a New Document Source

```python
# 1. Create new RAG system
from src.rag_system import BaseRAGSystem
from langchain_classic.schema import Document
from typing import List

class PDFRAGSystem(BaseRAGSystem):
    def __init__(self):
        super().__init__(collection_name="pdf")
    
    def _load_documents(self, pdf_path: str) -> List[Document]:
        # Your PDF loading logic
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLof_path)
        return loader.load()
    
    def _get_cleaner(self, **kwargs):
        # Your PDF cleaner
        return PDFDocumentCleaner()

# 2. Create cleaner
from src.processors.base_cleaner import BaseDocumentCleaner

class PDFDocumentCleaner(BaseDocumentCleaner):
    def __init__(self):
        super().__init__("pdf")
    
    def clean_text(self, text: str) -> str:
        # Remove PDF artifacts
        text = text.replace("\x00", "")
        return text.strip()
    
    def should_keep_chunk(self, chunk: str) -> bool:
        return len(chunk.split()) >= 10

# 3. Use it
rag = PDFRAGSystem()
rag.setup(pdf_path="document.pdf")
```

### Add Custom Validation Rules

```python
# In config/constants.py
class ValidationRules:
    MAX_QUERY_LENGTH = 2000  # Increase limit
    
    SUSPICIOUS_PATTERNS = [
        "<script",
        "DROP TABLE",
        "rm -rf",  # Add custom patterns
    ]
```

### Add Custom Error Messages

```python
# In config/constants.py
class ErrorMessages:
    CUSTOM_ERROR = (
        "❌ Your custom error message\n"
        "  → Helpful suggestion 1\n"
        "  → Helpful suggestion 2"
    )
```

---

## 🐛 Debugging

### Enable Debug Logging

```bash
# In .env
DEBUG_LOGGING=true
```

### Check Logs

```bash
# View latest log
tail -f logs/rag_system.log

# Search for errors
grep ERROR logs/rag_system.log

# View specific component
grep "vectorstore" logs/rag_system.log
```

### Measure Performance

```python
import time

start = time.time()
answer = rag_system.query(query, history)
end = time.time()

print(f"Query took {end - start:.2f}s")
```

### Inspect Cache

```python
from src.utils.cache import query_cache

stats = query_cache.get_stats()
print(f"Cache size: {stats['size']}")
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

---

## 📊 Monitoring

### Track Token Usage

```python
from src.utils.token_counter import TokenCounter

counter = TokenCounter()
stats = counter.count_tokens_documents(docs, model="embedding")

print(f"Total tokens: {stats['total_tokens']}")
print(f"Avg per doc: {stats['avg_tokens_per_doc']}")
print(f"Max: {stats['max_tokens']}")
print(f"Min: {stats['min_tokens']}")
```

### Monitor Query Quality

```python
from src.utils.response_validator import ResponseValidator

for query, response in queries:
    quality = ResponseValidator.get_quality_score(response, context)
    if quality < 0.5:
        print(f"Low quality response for: {query[:50]}")
        print(f"  Quality: {quality:.2f}")
```

### Track Retrieval Success

```python
from src.retrieval.retriever import EnhancedRetriever

docs = retriever.retrieve(query)
print(f"Retrieved {len(docs)} documents")

for doc in docs:
    score = doc.metadata.get('relevance_score', 0)
    print(f"  Score: {score:.2f} - {doc.page_content[:50]}")
```

---

## 📝 Environment Variables Reference

```bash
# Required
OPENAI_API_KEY=sk-...           # Your API key

# Optional - LLM Config
LLM_MODEL_NAME=gpt-4o-mini      # Model to use
LLM_BASE_URL=https://...        # API endpoint
USE_CLOUD_LLM=true              # Cloud vs local

# Optional - System
DEBUG_LOGGING=true              # Enable debug logs
ENABLE_LANGSMITH=false          # LangSmith tracing

# Optional - ServiceNow
SERVICENOW_USERNAME=...         # SN username
SERVICENOW_PASSWORD=...         # SN password
SERVICENOW_API_TOKEN=...        # Or use token

# Optional - Vector Stores
PINECONE_API_KEY=...            # For Pinecone
QDRANT_URL=...                  # For Qdrant
```

---

## 🔧 Troubleshooting Quick Fixes

### "No documents loaded"

```bash
# Check URL accessibility
curl -I <url>

# Try different URL
python main.py  # Select option 1 (Wikipedia)
```

### "API key not set"

```bash
# Set in .env
echo "OPENAI_API_KEY=sk-your-key" >> .env

# Or export temporarily
export OPENAI_API_KEY=sk-your-key
```

### "Out of memory"

```python
# In config/settings.py
chunk_size: int = 300  # Reduce from 500

# Or process fewer documents
limit = 50  # In servicenow_rag.py
```

### "Vector store corrupted"

```bash
# Delete and rebuild
rm -rf data/chroma_db/
python main.py
```

### "Cache not working"

```python
# Check cache is enabled
from config.constants import CacheConfig
print(CacheConfig.ENABLE_QUERY_CACHE)  # Should be True

# Clear cache and retry
rag_system.clear_cache()
```

---

## 📚 Useful Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Check code style
black src/ --check

# Type checking
mypy src/

# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage
open htmlcov/index.html

# Clean up
rm -rf data/ logs/ .cache/

# Rebuild everything
python main.py  # Select rebuild option
```

---

## 🔗 Important File Paths

```
config/settings.py         # Main configuration
config/constants.py        # Constants and rules
config/prompts.py          # LLM prompts

src/rag_system.py          # Base system
src/utils/validators.py    # Input validation
src/utils/cache.py         # Caching logic

logs/                      # Application logs
data/chroma_db/            # Vector store

.env                       # Environment variables
requirements.txt          # Dependencies
```

---

## 🎯 Common Patterns

### Pattern: Create Custom RAG System

```python
class MyRAGSystem(BaseRAGSystem):
    def _load_documents(self, **kwargs):
        # Load your documents
        pass
    
    def _get_cleaner(self, **kwargs):
        # Return your cleaner
        pass
```

### Pattern: Add Validation

```python
from src.utils.validators import InputValidator

validator = InputValidator()
is_valid, error = validator.validate_query(query)
if not is_valid:
    print(error)
    return
```

### Pattern: Check Quality

```python
from src.utils.response_validator import ResponseValidator

is_valid, warning, meta = ResponseValidator.validate_response(
    response, context_docs
)
if not is_valid:
    print(warning)
```

### Pattern: Use Cache

```python
# Automatic in query()
answer = rag_system.query(query, use_cache=True)

# Manual
from src.utils.cache import query_cache

cached = query_cache.get(query)
if cached:
    return cached

# ... generate response ...

query_cache.set(query, response)
```

---

For more details, see:
- **README.md** - Full documentation
- **INSTALLATION.md** - Setup guide
- **CHANGELOG.md** - Version history
- **REFACTORING_SUMMARY.md** - Improvement details
