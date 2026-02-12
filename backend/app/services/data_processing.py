
from langchain_core.documents import Document

def process_slack_data(data, channel_id):
    """Converts Slack messages into documents with metadata."""
    documents = []
    for msg in data:
        # Skip messages without text (e.g. join events)
        if "text" not in msg:
            continue
            
        # Create "Meta-Chunk": Prepend Date and Author
        content = f"Date: {msg.get('ts')} | Author: {msg.get('user')} | Channel: {channel_id}\nMessage: {msg.get('text')}"
        meta = {
            "source": "slack",
            "user": msg.get('user'),
            "channel": channel_id,
            "timestamp": msg.get('ts'),
            "url": f"https://slack.com/archives/{channel_id}/p{msg.get('ts').replace('.', '')}" if msg.get('ts') else None
        }
        documents.append(Document(page_content=content, metadata=meta))
    return documents

def process_jira_data(data):
    """Converts Jira tickets into documents with metadata."""
    documents = []
    for ticket in data:
        # Create "Meta-Chunk"
        content = f"Ticket: {ticket['key']} | Title: {ticket['summary']}\nDescription: {ticket['description'] or 'No description'}"
        meta = {
            "source": "jira",
            "id": ticket['key'],
            "title": ticket['summary'],
            "status": ticket['status'],
            "creator": ticket['creator']
        }
        documents.append(Document(page_content=content, metadata=meta))
    return documents
