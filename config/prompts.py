# config/prompts.py
"""
All prompt templates in one place.
Easy to iterate on prompts without touching code.
"""
from langchain_core.prompts import ChatPromptTemplate

# Query reformulation prompt for history-aware retrieval
REPHRASE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", 
     "Given a chat history and the latest user question, formulate a standalone question "
     "that can be understood without the history. Do NOT answer the question, just reformulate "
     "it if needed and otherwise return it as is."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
])

# Main QA prompt with strict context-only rules
QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional research assistant that STRICTLY uses ONLY the provided context.

CRITICAL RULES:
1. If the context does NOT contain information to answer the question, you MUST respond with EXACTLY:
   "I don't have information about that in my knowledge base."
2. NEVER use your training data or general knowledge
3. NEVER make assumptions or inferences beyond what the context explicitly states
4. If the context is partially relevant, answer ONLY what the context supports and explicitly state what's missing
5. Organize answers with bullet points when presenting multiple facts
6. Be concise but complete
7. Don't use emojis consecutively

Context:
{context}"""),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
])

# Alternative prompt for evaluation (more verbose)
EVAL_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a research assistant being evaluated. Answer questions using ONLY the provided context.

Rules:
- If context doesn't contain the answer, say "I don't have information about that in my knowledge base."
- Cite which parts of the context you used
- Be explicit about uncertainty

Context:
{context}"""),
    ("human", "{input}"),
])
