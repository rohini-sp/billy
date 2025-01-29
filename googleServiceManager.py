from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os

class GoogleServiceManager:
    """Unified authentication and service management for Google APIs"""
    
    SCOPES = {
        'gmail': ['https://www.googleapis.com/auth/gmail.readonly',
                  'https://www.googleapis.com/auth/gmail.send']
        ,
    }
    
    def __init__(self, credentials_path, token_path='token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = None
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Google services"""
        # Check if token.json exists and load it if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as token:
                self.credentials = Credentials.from_authorized_user_file(self.token_path, scopes=[scope for scopes in self.SCOPES.values() for scope in scopes])
        
        # If no valid credentials, authenticate using OAuth flow
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, [scope for scopes in self.SCOPES.values() for scope in scopes])
                self.credentials = flow.run_local_server(port=0)
            
            # Save the credentials to token.json
            with open(self.token_path, 'w') as token:
                token.write(self.credentials.to_json())
    
    def get_service(self, service_name, version):
        """Get a specific Google service client"""
        return build(service_name, version, credentials=self.credentials)
