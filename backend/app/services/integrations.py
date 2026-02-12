
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from jira import JIRA

class IntegrationService:
    def __init__(self):
        # Slack Initialization
        self.slack_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_client = WebClient(token=self.slack_token)
        
        # Jira Initialization
        jira_domain = os.environ.get("JIRA_DOMAIN")
        jira_email = os.environ.get("JIRA_EMAIL")
        jira_token = os.environ.get("JIRA_API_TOKEN")
        
        if jira_domain and jira_email and jira_token:
            # Ensure domain has protocol
            if not jira_domain.startswith("http"):
                jira_server = f"https://{jira_domain}"
            else:
                jira_server = jira_domain
                
            self.jira = JIRA(
                server=jira_server,
                basic_auth=(jira_email, jira_token)
            )
        else:
            self.jira = None
            print("Warning: Jira credentials missing.")

    def get_slack_thread(self, channel_id: str, thread_ts: str):
        """Fetches the last 5 messages from a Slack thread."""
        try:
            result = self.slack_client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=5
            )
            return result.get("messages", [])
        except SlackApiError as e:
            print(f"Slack API Error: {e}")
            return []

    def get_jira_ticket(self, issue_key: str):
        """Fetches issue details from Jira."""
        if not self.jira:
            return None
            
        try:
            issue = self.jira.issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "creator": issue.fields.creator.displayName
            }
        except Exception as e:
            print(f"Jira API Error: {e}")
            return None
    def list_channels(self, limit=20):
        """Lists public channels to help user find IDs."""
        try:
            result = self.slack_client.conversations_list(limit=limit)
            channels = result.get("channels", [])
            return [{"id": c["id"], "name": c["name"]} for c in channels]
        except SlackApiError as e:
            print(f"Slack API Error: {e}")
            return []

    def fetch_channel_history(self, channel_id: str, limit=50):
        """Fetches recent messages from a channel."""
        try:
            result = self.slack_client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            return result.get("messages", [])
        except SlackApiError as e:
            print(f"Slack API Error: {e}")
            return []

    def search_jira_tickets(self, jql: str, limit=50):
        """Searches for Jira tickets using JQL."""
        if not self.jira:
            return []
        try:
            # fields='summary,description,status,creator,created'
            issues = self.jira.search_issues(jql, maxResults=limit)
            return [{
                "key": i.key,
                "summary": i.fields.summary,
                "description": i.fields.description,
                "status": i.fields.status.name,
                "creator": i.fields.creator.displayName
            } for i in issues]
        except Exception as e:
            print(f"Jira API Error: {e}")
            return []
