# ServiceNow Knowledge Article RAG Integration

## Overview

This extends your RAG pipeline to ingest and query **ServiceNow Knowledge Articles**!

Perfect for Operations teams who need quick answers from ServiceNow documentation.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd C:\Users\r0k083y\Downloads\RAG_pipeline
pip install -r requirements.txt
```

### 2. Set Up ServiceNow Credentials

**Option A: Environment Variables** (Recommended)

Create a `.env` file in the project root:

```bash
# For username/password auth
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# OR for API token auth (preferred)
SERVICENOW_API_TOKEN=your_api_token

# Element LLM Gateway (required for generation)
ELEMENT_API_KEY=your_element_key
```

**Option B: Interactive Entry**

The script will prompt you for credentials if not found in environment variables.

### 3. Get Element LLM Gateway API Key

You need an Element API key to power the AI responses:

1. Go to Microsoft Teams: [Element GenAI Support](https://teams.microsoft.com/l/channel/19%3AGbP8DGJjrXq1sL3IlXErZc5U7hk-IEqsokmnImcKyP41%40thread.tacv2/General?groupId=51caa2b5-ff58-4dc0-9ee0-c20eea1de9f8&tenantId=3cbcc3d3-094d-4006-9849-0d11d61f484d)
2. Request an API key
3. Add it to your `.env` file

### 4. Run the ServiceNow RAG System

```bash
python servicenow_rag.py
```

You'll be prompted for:
- ServiceNow instance URL (e.g., `walmart.service-now.com`)
- Credentials (if not in .env)
- Number of articles to load
- Optional custom query filters

---

## 🔧 How It Works

1. **Connects to ServiceNow** via REST API
2. **Fetches knowledge articles** (published articles by default)
3. **Cleans HTML content** and removes boilerplate
4. **Chunks and embeds** the content
5. **Stores in ChromaDB** for fast retrieval
6. **Answers your questions** using RAG + Element LLM Gateway

---

## 📊 Usage Examples

### Example Queries

Once running, ask questions like:

```
🧑 You: How do I reset a user's password?
🤖 AI: [Retrieves relevant KB article and provides step-by-step guide]

🧑 You: What's the process for requesting new hardware?
🤖 AI: [Pulls from hardware request KB articles]

🧑 You: How do I escalate a P1 incident?
🤖 AI: [Finds escalation procedures from incident management articles]
```

### Filtering Articles

You can use ServiceNow query syntax to filter articles:

```
# Only IT category articles
category=IT

# Multiple categories
category=IT^ORcategory=HR

# Specific knowledge base
kb_knowledge_base=<sys_id>

# Recently updated
sys_updated_on>2024-01-01
```

---

## 🔐 ServiceNow API Access

### Getting API Access

1. **Check if you have access**: Try logging into ServiceNow and see if you can view KB articles
2. **Request API access**: Contact your ServiceNow admin or IT support
3. **Get credentials**:
   - Username/password (your ServiceNow login)
   - OR API token (more secure, request from admin)

### Authentication Methods

The system supports two auth methods:

**Method 1: Basic Auth (Username + Password)**
```python
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
```

**Method 2: OAuth Token** (Preferred)
```python
SERVICENOW_API_TOKEN=your_token_here
```

---

## ⚙️ Configuration

### Adjust Settings

Edit `config/settings.py` to tune:

```python
# Chunk size (how much context per chunk)
chunking.chunk_size = 500  # Increase for more context

# Retrieval parameters
retrieval.initial_k = 60  # How many candidates to retrieve
retrieval.rerank_top_n = 10  # How many to use for generation

# LLM settings
llm.temperature = 1.0  # Creativity (0=deterministic, 2=creative)
```

### ServiceNow-Specific Settings

When running `servicenow_rag.py`, you can customize:

- `limit`: Max articles to fetch (default: 100)
- `query`: ServiceNow query filter (default: published articles only)
- `workflow_state`: Article state (default: `published`)

---

## 🐞 Troubleshooting

### "Connection refused" or "401 Unauthorized"

➡️ Check your ServiceNow credentials
- Verify username/password are correct
- Ensure API token is valid
- Confirm you have permission to access knowledge articles

### "No articles loaded"

➡️ Possible causes:
- Your account doesn't have access to any published articles
- The query filter is too restrictive
- Try removing the custom query filter

### "Proxy error"

➡️ The system automatically tries Walmart proxy settings:
- `http://sysproxy.wal-mart.com:8080`
- If this fails, it retries without proxy
- Ensure you're on VPN/Eagle WiFi

### "Element LLM Gateway error"

➡️ Check Element API key:
- Ensure `ELEMENT_API_KEY` is set in `.env`
- Verify the key is valid (contact #element-genai-support on Teams)
- Confirm you're on Walmart VPN

### "Out of memory" or slow performance

➡️ Reduce the number of articles:
- Start with `limit=50` instead of 100
- Filter by specific categories
- Reduce `chunk_size` in settings

---

## 📚 Advanced Usage

### List Available Knowledge Bases

Add this to test your connection:

```python
from src.loaders.servicenow_loader import ServiceNowKnowledgeLoader

loader = ServiceNowKnowledgeLoader(
    instance_url="https://walmart.service-now.com"
)

kbs = loader.list_knowledge_bases()
for kb in kbs:
    print(f"{kb['title']}: {kb['sys_id']}")
```

### Load Specific Knowledge Base

When running `servicenow_rag.py`, use the custom query:

```
Custom ServiceNow query filter: kb_knowledge_base=<sys_id_from_above>
```

### Incremental Updates

To add new articles without rebuilding:

1. Run with `force_rebuild=False` (default)
2. System will load existing vector store
3. To refresh: use `force_rebuild=True`

---

## 🛠️ Next Steps

### Phase 1: Test It Out (Now)
1. Get Element API key
2. Run `servicenow_rag.py`
3. Load 10-20 articles to test
4. Ask some questions!

### Phase 2: Scale It Up
1. Load all relevant KB articles for your team
2. Set up scheduled refreshes (cron job)
3. Fine-tune chunk sizes and retrieval params

### Phase 3: Make It a Web App
1. Add FastAPI backend (I can help!)
2. Build HTMX frontend with Walmart colors
3. Deploy for your team to use
4. Add authentication and multi-user support

---

## 💬 Support

**Need Help?**
- Teams: [Element GenAI Support](https://teams.microsoft.com/l/channel/19%3AGbP8DGJjrXq1sL3IlXErZc5U7hk-IEqsokmnImcKyP41%40thread.tacv2/General?groupId=51caa2b5-ff58-4dc0-9ee0-c20eea1de9f8&tenantId=3cbcc3d3-094d-4006-9849-0d11d61f484d)
- For Code Puppy help: https://puppy.walmart.com/doghouse

**ServiceNow API Docs**:
- [Knowledge Management API](https://docs.servicenow.com/bundle/tokyo-application-development/page/integrate/inbound-rest/concept/c_KnowledgeManagementAPI.html)
- [Table API](https://docs.servicenow.com/bundle/tokyo-application-development/page/integrate/inbound-rest/concept/c_TableAPI.html)

---

## 🎉 What You Just Built

Congrats! You now have:
✅ ServiceNow knowledge article integration
✅ RAG-powered Q&A over your KB
✅ Reusable, extensible codebase
✅ Foundation for a team knowledge assistant

This is WAY more useful than just scraping random websites! 🐶

---

**Happy querying!** 🚀
