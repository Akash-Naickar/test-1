
from app.services.integrations import IntegrationService
from dotenv import load_dotenv

load_dotenv()

def list_channels():
    print("Initializing Integration Service...")
    service = IntegrationService()
    
    print("\nFetching Slack Channels...")
    channels = service.list_channels()
    
    if not channels:
        print("No channels found or error occurred. Check your API Token.")
    else:
        print(f"Found {len(channels)} channels:")
        for c in channels:
            print(f"ID: {c['id']} | Name: #{c['name']}")

if __name__ == "__main__":
    list_channels()
