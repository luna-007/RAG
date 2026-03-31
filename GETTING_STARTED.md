# Getting Started with RAG Pipeline

## 🐶 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd C:\Users\r0k083y\Downloads\RAG_pipeline
pip install -r requirements.txt
```

**Note:** This will download ~2GB of models (transformers, embeddings, etc.)

### Step 2: Run Your First Query

```bash
python main.py
```

**You'll see:**
1. Choose a data source (try option 1 for Wikipedia India)
2. Wait for it to process (~30 seconds first time)
3. Ask questions!

**Example questions:**
- "What is the capital of India?"
- "Tell me about India's population"
- "What languages are spoken in India?"

### Step 3: Understand What Happened

The system just:
1. ✅ Downloaded the Wikipedia page
2. ✅ Cleaned and chunked the text
3. ✅ Created vector embeddings
4. ✅ Stored them in a local database (Chroma)
5. ✅ Set up a local LLM connection

**Next time you run it:** Just press 'N' when asked to rebuild - it will use the cached data!

---

## 🔧 What You Need Running

### For Local LLM (Default Setup)

You need a local LLM server running on `http://localhost:8000`

Options:
1. **vLLM** (recommended for Walmart)
2. **Ollama**
3. **llama.cpp**

**Using vLLM:**
```bash
# Install
pip install vllm

# Run server
vllm serve Qwen/Qwen2.5-3B-Instruct --port 8000
```

### For Element LLM Gateway (Cloud)

1. Get your Element API key from #element-genai-support
2. Edit `config/settings.py`:
   ```python
   use_element_gateway = True  # Change to True
   ```
3. Set your API key in `.env`:
   ```
   ELEMENT_API_KEY=your_key_here
   ```

---

## 📋 Common Commands

```bash
# Run the chatbot
python main.py

# Run evaluation (tests system quality)
python scripts/run_evaluation.py

# Run tests
pytest tests/ -v

# Clear the vector database (start fresh)
rm -rf data/chroma_db/*
```

---

## 🐛 Troubleshooting

### "Connection refused" error
➡️ Your local LLM server isn't running. Start it first!

### "No module named 'transformers'"
➡️ Run `pip install -r requirements.txt`

### "CUDA out of memory"
➡️ Edit `config/settings.py`, change `device = "cpu"` instead of GPU

### Slow performance
➡️ First run downloads models. Subsequent runs are faster!

### Questions aren't answered well
➡️ Try:
1. Using a better/larger LLM model
2. Adjusting chunk sizes in `config/settings.py`
3. Increasing `retrieval.initial_k` to get more context

---

## 🎯 Next Steps

1. **Try different data sources**
   - Wikipedia articles
   - News sites (BBC, Reuters)
   - Internal docs

2. **Tune the configuration**
   - Experiment with chunk sizes
   - Adjust retrieval parameters
   - Try different embedding models

3. **Add your own cleaner**
   - See `src/processors/` for examples
   - Create a cleaner for your document type
   - Register it in the factory

4. **Run evaluation**
   - See how well the system performs
   - Create your own eval datasets
   - Track improvements over time

---

## 📚 Learning Resources

- **LangChain Tutorial**: https://python.langchain.com/docs/tutorials/
- **RAG Explained**: https://www.youtube.com/watch?v=T-D1OfcDW1M
- **Vector Databases**: https://www.pinecone.io/learn/vector-database/

---

## ❓ Need Help?

Reach out on:
- Slack: #element-genai-support
- Teams: [Python GenAI Enablement Channel]

Happy coding! 🎉
