# Installation Guide

Quick guide to get the Production RAG System up and running.

## Prerequisites

- **Python**: 3.9 or higher
- **pip**: Latest version recommended
- **Git**: For cloning the repository
- **4GB RAM minimum**: For embedding models
- **API Key**: OpenAI or compatible LLM service

---

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd RAG_pipeline
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will take 5-10 minutes as it downloads ML models.

### 4. Set Up Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your API key
# At minimum, set:
# OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the System

```bash
# For web-based RAG
python main.py

# For ServiceNow RAG
python servicenow_rag.py
```

That's it! 🎉

---

## Detailed Installation

### Option 1: Standard Installation

This installs the core system with Chroma vector store:

```bash
pip install -r requirements.txt
```

### Option 2: With Optional Backends

If you want to use alternative vector stores:

```bash
# Install core
pip install -r requirements.txt

# Add FAISS support
pip install faiss-cpu

# Add Pinecone support
pip install pinecone-client langchain-pinecone

# Add Qdrant support
pip install qdrant-client langchain-qdrant
```

### Option 3: Development Installation

For contributing or testing:

```bash
# Install with dev dependencies
pip install -r requirements.txt

# Install additional dev tools
pip install pytest pytest-cov pytest-asyncio black pylint mypy
```

---

## Configuration

### Basic Configuration

Edit `config/settings.py` or use environment variables:

```python
# In config/settings.py

# Adjust chunk size for your use case
chunk_size: int = 500  # Increase for longer documents

# Adjust retrieval candidates
initial_k: int = 60    # More candidates = better recall
rerank_top_n: int = 10 # Top results after reranking
```

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional - Override defaults
LLM_MODEL_NAME=gpt-4o-mini
USE_CLOUD_LLM=true
DEBUG_LOGGING=true
```

### Using Different LLM Providers

#### OpenAI (Default)
```bash
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

#### Azure OpenAI
```bash
OPENAI_API_KEY=your-azure-key
LLM_MODEL_NAME=gpt-4o
LLM_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/openai/deployments
```

#### Local LLM (e.g., llama.cpp, Ollama)
```bash
USE_CLOUD_LLM=false
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL_NAME=llama2
```

#### Other Providers (Anthropic, Cohere, etc.)
```bash
# Use their OpenAI-compatible endpoints
OPENAI_API_KEY=your-api-key
LLM_BASE_URL=https://provider-endpoint.com/v1
LLM_MODEL_NAME=their-model-name
```

---

## Verification

### Test the Installation

```bash
# Test imports
python -c "from src.rag_system import BaseRAGSystem; print('✅ Imports OK')"

# Run a quick test
python -c "
import sys
from src.utils.validators import InputValidator

validator = InputValidator()
is_valid, error = validator.validate_query('Test query')

if is_valid:
    print('✅ Validation OK')
    sys.exit(0)
else:
    print(f'❌ Validation failed: {error}')
    sys.exit(1)
"

# Run unit tests (if available)
pytest tests/ -v
```

### Expected First Run

1. **First launch**: Downloads embedding model (~90MB)
   - BAAI/bge-small-en-v1.5 from HuggingFace
   - Cached for future use

2. **Document loading**: Depends on source
   - Web pages: 5-30 seconds
   - ServiceNow: Varies by number of articles

3. **Vector store creation**: ~5-10 seconds for 100 chunks

4. **First query**: ~2-3 seconds (uncached)

5. **Subsequent queries**: ~0.01 seconds (if cached), ~2-3 seconds (uncached)

---

## Troubleshooting

### Common Issues

#### "No module named 'transformers'"
```bash
pip install transformers torch
```

#### "chromadb.errors.NoDatapointsException"
```bash
# Delete existing database and rebuild
rm -rf data/chroma_db/
python main.py  # Will rebuild automatically
```

#### "API key not set"
```bash
# Check .env file exists
ls .env

# Verify it contains OPENAI_API_KEY
cat .env | grep OPENAI_API_KEY

# If missing, set it:
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

#### "Out of memory" during embedding
```bash
# Reduce batch size in config/settings.py
chunk_size = 300  # Reduce from 500

# Or process fewer documents at once
# In servicenow_rag.py:
limit = 50  # Reduce from 100
```

#### "SSL Certificate Error"
```bash
# For corporate networks, you may need to disable SSL verification
# (NOT recommended for production)
export CURL_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""
```

### Getting Help

1. **Check logs**: Look in `logs/` directory for detailed error messages
2. **Enable debug logging**: Set `DEBUG_LOGGING=true` in `.env`
3. **Run with verbose output**: `python main.py 2>&1 | tee output.log`
4. **Check dependencies**: `pip list | grep -E "langchain|chroma|transformers"`

---

## Next Steps

Once installed:

1. **Read the README**: Understand architecture and features
2. **Try the examples**: Run `python main.py` with default Wikipedia example
3. **Customize**: Edit `config/settings.py` for your use case
4. **Extend**: Add new document sources (see README → Extending)
5. **Deploy**: Consider FastAPI wrapper for production

---

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 2GB free space
- **Network**: Internet connection for LLM API

### Recommended
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 10GB free (for multiple vector stores)
- **GPU**: Optional, for faster embeddings (CUDA-compatible)

### For Production
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Disk**: SSD recommended
- **GPU**: Recommended for high throughput
- **Network**: Low-latency connection to LLM provider

---

## Updating

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Check CHANGELOG.md for breaking changes
cat CHANGELOG.md

# Rebuild vector stores if needed
rm -rf data/chroma_db/
python main.py
```

---

## Uninstalling

```bash
# Remove virtual environment
deactivate
rm -rf venv/

# Remove data
rm -rf data/
rm -rf logs/
rm -rf .cache/

# Remove the project
cd ..
rm -rf RAG_pipeline/
```
