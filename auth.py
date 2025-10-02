"""
Google OAuth Setup Script
Generates token.json for MCP server and ensures automatic refresh.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import redis

# If modifying these scopes, delete token.json
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

CREDENTIALS_PATH = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
TOKEN_PATH = os.environ.get('GOOGLE_TOKEN_PATH', 'token.json')

REDIS_HOST = os.environ.get("REDIS_HOST", "mcp-redis-prod")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_KEY = os.environ.get("GOOGLE_TOKEN_KEY", "gmail_oauth_token")

def main():
    creds = None
    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If no valid creds, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES,
                redirect_uri="https://mcp.orionac.in/oauth2callback"
            )
            creds = flow.run_local_server()
        # Save the credentials for next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        print(f"[INFO] Saved token to {TOKEN_PATH}")
        # Save token into Redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.set(REDIS_KEY, creds.to_json())
        print(f"[INFO] Saved token to Redis key {REDIS_KEY}")
    else:
        print(f"[INFO] Valid token already exists at {TOKEN_PATH}")
    # Test token refresh
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        print("[INFO] Token refreshed and saved.")
        # Save refreshed token into Redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.set(REDIS_KEY, creds.to_json())
        print(f"[INFO] Refreshed token saved to Redis key {REDIS_KEY}")
    print("[INFO] Google OAuth setup complete.")

if __name__ == '__main__':
    main()