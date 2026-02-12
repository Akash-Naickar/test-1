# app/services/rag.py

import os
import re
from functools import lru_cache
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from app.models import ContextObject
from typing import List

class RAGService:
    def __init__(self):
        self._init_resources()
    
    @lru_cache(maxsize=1)
    def _get_embeddings(self):
        return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    def _init_resources(self):
        """Initialize ChromaDB and LLM."""
        # Calculate absolute path to backend root
        current_dir = os.path.dirname(os.path.abspath(__file__)) # app/services
        backend_root = os.path.dirname(os.path.dirname(current_dir)) # backend
        db_path = os.path.join(backend_root, "chroma_db")
        
        try:
            self.db = Chroma(
                persist_directory=db_path, 
                embedding_function=self._get_embeddings()
            )
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview",
                temperature=0.2,
                convert_system_message_to_human=True
            )
            print("RAG Service Initialized.")
        except Exception as e:
            print(f"Failed to initialize RAG Service: {e}")
            self.db = None
            self.llm = None

    def _extract_keywords(self, code_snippet: str) -> str:
        """Extracts potential keywords (function names, variables) from code."""
        # Simple regex to find words that look like identifiers
        identifiers = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code_snippet)
        # Filter out common keywords could be added here, but for now just unique them
        unique_identifiers = list(set(identifiers))
        return " ".join(unique_identifiers[:10]) # Limit to top 10 to avoid noise

    def retrieve(self, query: str, k: int = 5):
        """Hybrid-ish retrieval: simply uses the vector store for now."""
        # In a real hybrid setup, we might combine BM25 with Vector search.
        # For this MVP, we rely on the semantic power of the embedding model,
        # but we augment the query with extracted code keywords to ensure specificity.
        if not self.db:
            return []
        return self.db.similarity_search(query, k=k)

    async def explain_code(self, code_snippet: str, file_path: str, line_numbers: str) -> str:
        if not self.db or not self.llm:
            return "### Error\nContext Engine is not initialized. Please check server logs."

        # 1. Augment Query
        keywords = self._extract_keywords(code_snippet)
        search_query = f"{code_snippet}\nKeywords: {keywords}"
        
        # 2. Retrieve Context
        print(f"Retrieving context for: {search_query[:50]}...")
        docs = self.retrieve(search_query)
        
        context_str = "\n\n".join([
            f"--- SOURCE: {doc.metadata.get('source', 'unknown')} ---\n"
            f"{doc.page_content}" 
            for doc in docs
        ])

        # 3. Construct Prompt
        system_prompt = """You are ContextSync, an AI assistant that bridges the gap between Code and Context (Slack/Jira).

        ### 🧠 Reasoning Loop
        Before answering, analyze the provided CONTEXT against the CODE SNIPPET.
        1.  **Analyze Intent**: What is the code trying to do?
        2.  **Verify Match**: Does the Slack thread or Jira ticket explicitly mention this feature, variable, or bug?
        3.  **Filter Noise**: Ignore context that is about a different part of the system, even if keywords match.

        ### 📝 Output Format (Markdown)
        
        ## ⚡ Context Analysis
        * **Relevance**: [High/Medium/Low] - [One sentence explanation]
        
        ## 💡 Intent & Backstory
        [Explain *why* this code exists based on the filtered context]

        ### 🔍 Decision Trail
        - **[Source: Date/Author]**: [Key insight directly related to this code]
        
        ### 🔗 References
        - [Link/ID] - [Title]
        
        If NO relevant context is found, state: "No direct Slack/Jira context found for this logic." and provide a technical explanation only.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", f"Context:\n{context_str}\n\nCode ({file_path}:{line_numbers}):\n```python\n{code_snippet}\n```")
        ])

        # 4. Generate
        chain = prompt | self.llm | StrOutputParser()
        response = await chain.ainvoke({})
        return response

    async def _summarize_doc(self, content: str) -> str:
        """Summarizes a single document using the LLM."""
        prompt_text = f"Summarize this context in one concise sentence for a developer:\n\n{content}"
        summary = await self.llm.ainvoke(prompt_text)
        return f"**Summary**: {summary.content}\n\n**Raw Source**:\n{content}"

    async def get_context_objects(self, code_snippet: str) -> List[ContextObject]:
        """Retrieves structured context objects with LLM summaries."""
        keywords = self._extract_keywords(code_snippet)
        search_query = f"{code_snippet}\nKeywords: {keywords}"
        docs = self.retrieve(search_query)
        
        import asyncio
        
        # Summarize in parallel
        summary_tasks = [self._summarize_doc(doc.page_content) for doc in docs]
        summaries = await asyncio.gather(*summary_tasks)
        
        objects = []
        for doc, summary in zip(docs, summaries):
            # Map Chroma metadata to ContextObject
            source = doc.metadata.get("source", "unknown")
            title_or_user = doc.metadata.get("user") or doc.metadata.get("title") or doc.metadata.get("id") or "Unknown"
            
            obj = ContextObject(
                source=source,
                title_or_user=title_or_user,
                url=doc.metadata.get("url"), 
                content_summary=summary,
                relevance_score=0.0, # Placeholder, would need vector score
                related_code_files=[]
            )
            objects.append(obj)
        return objects

    def add_documents(self, documents: List[Document]):
        """Adds new documents to the vector store."""
        if not self.db:
            return
        
        # Split text (reuse same splitter logic)
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)
        
        if splits:
            import hashlib
            # Generate deterministic IDs based on content hash to prevent duplicates
            ids = [hashlib.md5(doc.page_content.encode()).hexdigest() for doc in splits]
            
            print(f"Adding/Updating {len(splits)} chunks in Vector Store...")
            self.db.add_documents(splits, ids=ids)

