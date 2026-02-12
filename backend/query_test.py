import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

def test_query():
    print("Initializing Vector Store for testing...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database path {DB_PATH} does not exist. Run ingest.py first.")
        return

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
        
        query = "billing"
        print(f"\nQuerying for: '{query}'")
        
        results = vectorstore.similarity_search(query, k=2)
        
        if not results:
            print("No results found.")
        else:
            print(f"Found {len(results)} results:\n")
            for i, doc in enumerate(results):
                print(f"--- Result {i+1} ---")
                print(f"Content: {doc.page_content[:200]}...")
                print(f"Metadata: {doc.metadata}")
                print("------------------\n")
                
    except Exception as e:
        print(f"Error during query: {e}")

if __name__ == "__main__":
    test_query()
