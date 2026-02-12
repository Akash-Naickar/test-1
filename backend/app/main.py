import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from app.models import ExplainRequest, ExplainResponse, ContextObject
from typing import List
from app.services.rag import RAGService
from app.services.integrations import IntegrationService
from app.services.data_processing import process_slack_data, process_jira_data
from dotenv import load_dotenv

load_dotenv()

rag_service = None
integration_service = None

# Config from .env or hardcoded for now (should move to env)
SLACK_CHANNEL_ID = "C0AECA17DM0"
JIRA_JQL = "resolution = Unresolved ORDER BY created DESC"

async def sync_data():
    """Fetches and ingests real-time data."""
    try:
        print("Syncing real-time data...")
        if not integration_service or not rag_service:
            print("Services not ready, skipping sync.")
            return {"status": "skipped", "message": "Services not ready"}

        # Fetch Data
        slack_msgs = integration_service.fetch_channel_history(SLACK_CHANNEL_ID, limit=10)
        jira_tickets = integration_service.search_jira_tickets(JIRA_JQL, limit=10)
        
        # Process & Ingest
        new_docs = []
        if slack_msgs:
            new_docs.extend(process_slack_data(slack_msgs, SLACK_CHANNEL_ID))
        if jira_tickets:
            new_docs.extend(process_jira_data(jira_tickets))
        
        if new_docs:
            rag_service.add_documents(new_docs)
            print(f"Synced {len(new_docs)} items.")
            return {"status": "success", "items_synced": len(new_docs)}
        
        return {"status": "success", "items_synced": 0}
        
    except Exception as e:
        print(f"Error in sync: {e}")
        return {"status": "error", "message": str(e)}

async def background_sync():
    """Polls Slack and Jira for new data every 60 seconds."""
    print("Starting background sync loop...")
    while True:
        await sync_data()
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_service, integration_service
    rag_service = RAGService()
    integration_service = IntegrationService()
    
    # Start background task
    task = asyncio.create_task(background_sync())
    
    yield
    
    # Clean up
    task.cancel()

app = FastAPI(title="ContextSync Backend", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "ContextSync Context Engine is Running"}

@app.post("/explain", response_model=ExplainResponse)
async def explain_code(request: ExplainRequest):
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not initialized")
        
    markdown_response = await rag_service.explain_code(
        request.code_snippet, 
        request.file_path, 
        request.line_numbers
    )
    
    return ExplainResponse(markdown=markdown_response)

@app.post("/context/retrieve", response_model=List[ContextObject])
async def retrieve_context(request: ExplainRequest):
    """Returns structured context objects for the IDE."""
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not initialized")
    
    return await rag_service.get_context_objects(request.code_snippet)

@app.post("/context/ingest")
async def ingest_webhook(request: Request):
    """Mock webhook receiver for Slack/Jira events."""
    data = await request.json()
    print(f"Received webhook event: {data}")
    # In a real app, this would trigger the ingestion pipeline
    return {"status": "received"}

@app.post("/context/sync")
async def manual_sync():
    """Manually triggers the data sync logic."""
    return await sync_data()
    return {"status": "accepted"}
