import chromadb
import pydantic
print(f"ChromaDB Version: {chromadb.__version__}")
print(f"Pydantic Version: {pydantic.VERSION}")
try:
    client = chromadb.Client()
    print("ChromaDB Client initialized successfully.")
except Exception as e:
    print(f"ChromaDB Client Initialization Failed: {e}")
