import os
import base64
from googleapiclient.errors import HttpError
from config import LABEL_NAME, CREDENTIALS
from googleServiceManager import GoogleServiceManager
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText 
from email import encoders
from googleapiclient.errors import HttpError


CONFIG = {
    'label_name': 'United Logistique',
    'credentials_path': r'D:\InvoiceProj\GmailAuth.json',
}

class EmailProcessor:
    """Handles Gmail operations including finding and downloading attachments"""
    
    def __init__(self, service_manager, label_name):
        self.gmail_service = service_manager.get_service('gmail', 'v1')
        self.label_name = label_name
        
    def get_label_id(self):
        """Get Gmail label ID by name"""
        try:
            labels = self.gmail_service.users().labels().list(userId='me').execute().get('labels', [])
            for label in labels:
                if label['name'].lower() == self.label_name.lower():
                    return label['id']
            raise ValueError(f"Label '{self.label_name}' not found")
        except HttpError as error:
            raise RuntimeError(f'Gmail API error: {error}')
    
    def find_latest_attachment(self, label_id):
        """Find the most recent email with an attachment"""
        try:
            messages = self.gmail_service.users().messages().list(
                userId='me', 
                labelIds=[label_id], 
                maxResults=10
            ).execute().get('messages', [])
            
            for msg in messages:
                message = self.gmail_service.users().messages().get(
                    userId='me', 
                    id=msg['id']
                ).execute()
                
                for part in message['payload'].get('parts', []):
                    if part.get('filename'):
                        return msg['id']
            return None
            
        except HttpError as error:
            raise RuntimeError(f'Gmail API error: {error}')
    
    def download_attachment(self, message_id, download_dir='downloads'):
        """Download attachment from a specific email"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me', 
                id=message_id
            ).execute()
            
            os.makedirs(download_dir, exist_ok=True)
            
            for part in message['payload'].get('parts', []):
                if part.get('filename'):
                    attachment_id = part['body'].get('attachmentId')
                    attachment = self.gmail_service.users().messages().attachments().get(
                        userId='me',
                        messageId=message_id,
                        id=attachment_id
                    ).execute()
                    
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                    file_path = os.path.join(download_dir, part['filename'])
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
                    
                    return file_path
            
            return None
            
        except HttpError as error:
            raise RuntimeError(f'Gmail API error: {error}')
        


def GET_FILE():
    try:
        # Initialize services
        service_manager = GoogleServiceManager(CREDENTIALS)
        email_processor = EmailProcessor(service_manager, LABEL_NAME)
            
        # Process email attachment
        label_id = email_processor.get_label_id()
        message_id = email_processor.find_latest_attachment(label_id)
        
        if not message_id:
            raise ValueError("No email with attachment found")
        
        file_path = email_processor.download_attachment(message_id)
        
        if not file_path:
            raise ValueError("Failed to download attachment")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


def create_message_with_attachment(sender, to, subject, body, file_path):
    """Create a message for sending an email with an attachment"""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # Attach the body text
    msg = MIMEText(body)
    message.attach(msg)
    
    # Attach the file
    if file_path:
        attachment = open(file_path, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
        message.attach(part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return raw_message

def send_file_via_gmail(service, sender, to, subject, body, file_path):
    """Send a file via Gmail using the Gmail API"""
    try:
        raw_message = create_message_with_attachment(sender, to, subject, body, file_path)
        
        # Send the message
        send_message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print('Message Id: %s' % send_message['id'])
        return send_message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def SEND_FILE(send_to):
    try:
        service_manager = GoogleServiceManager(CREDENTIALS)
        email_processor = EmailProcessor(service_manager, LABEL_NAME)

        sender = "aryandhanawade2005@gmail.com"
        to = send_to
        subject = "Processed Invoice Data"
        body = "This Data is processed invoice data via gemini."
        file_path = "output.csv"

        send_file_via_gmail(service_manager.get_service('gmail', 'v1'), sender, to, subject, body, file_path)

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

