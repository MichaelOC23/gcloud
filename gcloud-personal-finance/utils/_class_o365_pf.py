import msal
import requests
import os
import streamlit as st
from datetime import datetime, timedelta, timezone
from google.cloud import secretmanager

class MS_GraphAPI:
    def __init__(self):
        # Constants - Replace with your values
        
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        secrets = ['AZURE_COMMUNIFY_TENANT_ID', 'AZURE_COMMUNIFY_CLIENT_ID', 'AZURE_COMMUNIFY_CLIENT_SECRET', 'AZURE_COMMUNIFY_USER_ID']
        for secret in secrets:
            if secret not in st.session_state:
                self.access_secret_version(secret) 
                
        self.AZURE_COMMUNIFY_TENANT_ID          = self.access_secret_version('AZURE_COMMUNIFY_TENANT_ID') 
        self.AZURE_COMMUNIFY_CLIENT_ID          = self.access_secret_version('AZURE_COMMUNIFY_CLIENT_ID') 
        self.AZURE_COMMUNIFY_CLIENT_SECRET      = self.access_secret_version('AZURE_COMMUNIFY_CLIENT_SECRET') 
        self.AZURE_COMMUNIFY_USER_ID            = self.access_secret_version('AZURE_COMMUNIFY_USER_ID') 
        self.USER_EMAIL                         = self.AZURE_COMMUNIFY_USER_ID
        
        self.EMAILS_TO_SEARCH=100 # Max emails to pull back
        self.INTERNAL_DOMAINS = ['communify.com', 'justbuildit.com', 'spglobal'] # Replace with the actual user's internal domains
        self.TIME_RANGES = [[0,2], [2,5], [5,10]]
        # Graph API endpoints
        self.SCOPE = ['https://graph.microsoft.com/.default']  # For app permissions
        self.AUTHORITY       = f'https://login.microsoftonline.com/{self.AZURE_COMMUNIFY_TENANT_ID}'
        self.GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
        self.log = []
        
    def logit(self, log_mession):
        self.log.append(log_mession)
        
    def authenticate(self,):
        app = msal.ConfidentialClientApplication(
            self.AZURE_COMMUNIFY_CLIENT_ID,
            authority=self.AUTHORITY,
            client_credential=self.AZURE_COMMUNIFY_CLIENT_SECRET
        )
        token_response = app.acquire_token_for_client(scopes=self.SCOPE)
        
        if 'access_token' in token_response:
            return token_response['access_token']
        else:
            raise Exception("Authentication failed.")

    def access_secret_version(self, secret_id, project_id='toolsexplorationfirebase',  version_id="latest"):
            

            secret_payload = os.environ.get(secret_id, None)
            
            if not secret_payload:
                secret_payload = st.session_state.get(secret_id, None)
            
            if not secret_payload:
                try:


                    # Build the resource name of the secret version
                    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

                    # Access the secret version
                    response = self.secret_client.access_secret_version(request={"name": name})

                    # Decode the secret payload and return it
                    secret_payload = response.payload.data.decode("UTF-8")
                    
                    st.session_state[secret_id] = secret_payload
                
                except:
                    pass
                
            return secret_payload

    def get_recent_emails_from_inbox(self,access_token, AZURE_COMMUNIFY_USER_ID, days_ago_start=0, days_ago_end=30):
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Calculate dates for the specified range
        end_date = datetime.now(timezone.utc) - timedelta(days=days_ago_start)
        start_date = datetime.now(timezone.utc) - timedelta(days=days_ago_end)

        # Format dates in the ISO 8601 format used by Microsoft Graph
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query_params = {
            '$top': self.EMAILS_TO_SEARCH,  # Retrieve the most recent emails in the inbox
            '$orderby': 'receivedDateTime desc',
            '$filter': f"receivedDateTime ge {start_date_str} and receivedDateTime le {end_date_str}"

            # '$select': 'id,subject,from,sentDateTime,receivedDateTime,meetingMessageType' #,hasAttachments' email['meetingMessageType']
        }
        # Update the endpoint to specify the inbox folder
        endpoint = f"{self.GRAPH_API_ENDPOINT}/users/{AZURE_COMMUNIFY_USER_ID}/mailFolders/inbox/messages" 
        # ?$filter=meetingMessageType eq 'meetingRequest'"
        response = requests.get(endpoint, headers=headers, params=query_params)
        
        # Check for HTTP errors
        if response.status_code != 200:
            self.logit(f"Error fetching inbox emails: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response.json().get('value', [])

    # Check if the email is a meeting invite based on meetingMessageType
    def is_meeting_invite(self,email):
        meeting_message_type = email.get('meetingMessageType', 'No Meeting Message Type')
        self.logit(f"Meeting Message Type: {meeting_message_type}")
        if meeting_message_type and meeting_message_type == 'meetingRequest':
            return True
        return False

    # Extract event ID from the message
    def get_event_id_from_meeting_message(self,access_token, AZURE_COMMUNIFY_USER_ID, message_id):
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Retrieve the message details (this can include event information)
        response = requests.get(f'{self.GRAPH_API_ENDPOINT}/users/{AZURE_COMMUNIFY_USER_ID}/messages/{message_id}', headers=headers)
        
        if response.status_code == 200:
            message_data = response.json()
            
            # Check if the message contains an event
            event_data = message_data.get('event')
            if event_data:
                return event_data['id']  # This is the event ID we need
            else:
                self.logit("No event data found in the message.")
                return None
        else:
            self.logit(f"Error fetching message details: {response.status_code} - {response.text}")
            return None

    def get_event_id_from_calendar(self,access_token, AZURE_COMMUNIFY_USER_ID, message_id, subject, start_datetime):
        """
        Gets the event ID from the user's calendar based on the meeting subject 
        and start datetime.

        Args:
            access_token (str): The access token for the Microsoft Graph API.
            AZURE_COMMUNIFY_USER_ID (str): The user's email address.
            message_id (str): The ID of the meeting invitation message.
            subject (str): The subject of the meeting invitation.
            start_datetime (datetime): The start datetime of the meeting invitation.

        Returns:
            str: The event ID if found, otherwise None.
        """
        headers = {'Authorization': f'Bearer {access_token}'}

        # Format the start and end times for the calendar view
        start_datetime_str = start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') 
        end_datetime_str = (start_datetime + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ') 

        # Construct the query parameters for the calendar view
        query_params = {
            'startDateTime': start_datetime_str,
            'endDateTime': end_datetime_str
        }

        # Make the request to get calendar events within the specified time range
        response = requests.get(f'{self.GRAPH_API_ENDPOINT}/users/{AZURE_COMMUNIFY_USER_ID}/calendar/calendarView', 
                                headers=headers, params=query_params)

        if response.status_code == 200:
            calendar_data = response.json()
            events = calendar_data.get('value', [])

            # Search for the event with a matching subject
            for event in events:
                if event.get('subject') == subject:
                    self.logit(f"Found matching event in calendar: {event.get('id')}")
                    return event['id']
            else:
                self.logit(f"No calendar event found with subject: {subject}")
                return None
        else:
            self.logit(f"Error fetching calendar view: {response.status_code} - {response.text}")
            return None

    # Accept the meeting invite using the event ID
    def accept_meeting(self,access_token, AZURE_COMMUNIFY_USER_ID, event_id):
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Send accept request for the message
        accept_url = f'{self.GRAPH_API_ENDPOINT}/users/{AZURE_COMMUNIFY_USER_ID}/events/{event_id}/accept'
        
        # The request body, you can include options such as whether to send a response
        data = {
            'sendResponse': True  # Set to True to send a response to the organizer
        }
        
        response = requests.post(accept_url, headers=headers, json=data)
        if response.status_code != 202:  # 202 Accepted is the expected response
            self.logit(f"Error accepting meeting: {response.status_code} - {response.text}")
            response.raise_for_status()
        else:
            self.logit(f"Successfully accepted the meeting invite with Message ID: {event_id}")

    def archive_invite_email(self,access_token, AZURE_COMMUNIFY_USER_ID, message_id, target_folder_id='archive'):
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Construct the API URL
        move_url = f'https://graph.microsoft.com/v1.0/users/{AZURE_COMMUNIFY_USER_ID}/messages/{message_id}/move'
        
        # Request body specifying the target folder
        data = {
            'destinationId': target_folder_id  # E.g., 'archive' or another folder ID
        }
        
        # Send POST request to move the message
        response = requests.post(move_url, headers=headers, json=data)
        
        if response.status_code != 201:  # 201 Created indicates success for move operations
            self.logit(f"Error moving email: {response.status_code} - {response.text}")
        else:
            self.logit("Successfully archived the invite email.")

    # Main logic to process meeting invites
    def process_meeting_invites(self):
        access_token = self.authenticate()
        ranges = self.TIME_RANGES
        
        for range in ranges:
            emails = self.get_recent_emails_from_inbox(access_token, self.AZURE_COMMUNIFY_USER_ID,range[0],range[1])
            
            for email in emails:
                from_address = email.get('from', {}).get('emailAddress', {}).get('address', 'Not A Valid From Address')
                # if any of the string in the self.INTERNAL_DOMAINS list are in the from address, then it's an internal email
                if not any([i in from_address for i in self.INTERNAL_DOMAINS]):
                    self.logit(f"Ignoring email from {from_address} as it's not an internal email.")
                    continue

                subject = email.get('subject')
                message_id = email.get('id')
                
                
                # Check if the email is a meeting invite
                if email.get('meetingMessageType', None):
                    self.logit(f"{email.get('meetingMessageType', '')}")
                    if email.get('meetingMessageType', '')  == 'meetingRequest':
                        start_datetime = email.get('startDateTime').get('dateTime')
                        self.logit(start_datetime)
                        if start_datetime and isinstance(start_datetime, str):  # Check for valid string
                            if '.' in start_datetime:
                                date_part, microsecond_part = start_datetime.split('.')
                                microsecond_part = microsecond_part[:6]  # Take only up to 6 digits
                                start_datetime = f"{date_part}.{microsecond_part}"

                            # Parse the string with the adjusted format
                            parsed_datetime = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S.%f')
                            event_id = self.get_event_id_from_calendar(access_token, self.AZURE_COMMUNIFY_USER_ID, message_id, subject, parsed_datetime)

                    
                        try:
                            # Accept the meeting invite using the message ID
                            self.accept_meeting(access_token, self.AZURE_COMMUNIFY_USER_ID, event_id)
                        except Exception as e:
                            self.logit(f"Error ACCEPTING meeting invite: {e}")
                        try:
                            self.archive_invite_email(access_token, self.AZURE_COMMUNIFY_USER_ID, message_id)
                        except Exception as e:
                            self.logit(f"Error ARCHIVING meeting invite: {e}")
                        
                else:
                    self.logit(f"Skipping non-meeting email: {subject}")
        return self.log

if __name__ == '__main__':
        pass
    # MSGraph = MS_GraphAPI()
    # MSGraph.process_meeting_invites()