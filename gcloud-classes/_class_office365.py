
from quart import request, jsonify, redirect, url_for, session  # Changed from Flask to Quart
import json
import os
from urllib.parse import urlencode
import requests
import base64
import hashlib
from openai import OpenAI
from datetime import datetime, timedelta


class office365_tools():
    def __init__(self):
        self.client = None
        self.token = None
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.expires_at = datetime.utcnow()
        # self.appkey = os.environ['AZURE_APPKEY']
        # self.CLIENT_ID = os.environ.get('AZURE_APP_CLIENT_ID', 'No Key or Connection String found')
        # self.TENANT_ID = os.environ.get('AZURE_APP_TENANT_ID', 'No Key or Connection String found') 
        self.CLIENT_ID = "677433d4-b486-43a5-a8d6-26653ae69bb7"
        self.TENANT_ID = "050376de-b1f5-4dbc-8c0f-8929b6e68a08"
        self.redirecturi = 'http://localhost:4008/office365/auth'
        self.authority = f"https://login.microsoftonline.com/{self.TENANT_ID}"
        self.GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
        
        self.MSFT_TOKEN_JSON = os.environ.get('MSFT_TOKEN_JSON', '')
        self.OFFICE365_BACKGROUND_PORT = os.environ.get('MYTECH_QUART_PORT', 4008)
        
        # OAuth Endpoints
        self.AUTH_ENDPOINT = f'https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/authorize'
        self.TOKEN_ENDPOINT = f'https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0/token'
        
        # self.app.secret_key = os.urandom(24)

    def calculate_expiration(self, expires_in_seconds):
        expiration_time = datetime.now() + timedelta(seconds=expires_in_seconds)
        expiration_time_str = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
        return expiration_time_str

    async def export_token(self):
        with open('token.json', 'w') as f:
            f.write(self.MSFT_TOKEN_JSON)
    
    async def set_value(self):
        global access_token
        data = await request.get_json()
        access_token = data.get('access_token', '')
        return jsonify({"status": "Access token set"}), 200
    
    async def homepage(self):
        def generate_code_verifier():
            return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')

        def generate_code_challenge(code_verifier):
            code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
            return base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode('utf-8')
        
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        session['code_verifier'] = code_verifier
        
        # print(url_for('auth_redirect', _external=True))
        auth_params = {
            'client_id': self.CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': url_for('auth_redirect', _external=True),
            'scope': 'openid profile User.Read Mail.Read',
            'response_mode': 'query',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        auth_url = f'{self.AUTH_ENDPOINT}?{urlencode(auth_params)}'
        print(auth_url)
        return redirect(auth_url)

    async def auth_redirect(self):
        global access_token

        code = request.args.get('code')
        if not code:
            return "No code provided in request:\n Request: {request}"
        
        code_verifier = session.pop('code_verifier', None)
        if not code_verifier:
            return "Missing code verifier: Session: {session}"
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': url_for('auth_redirect', _external=True),
            'client_id': self.CLIENT_ID,
            'code_verifier': code_verifier
            }

        response = requests.post(self.TOKEN_ENDPOINT, data=token_data)
        if response.status_code == 200:    
            token_json = response.json()
            
            # Example usage:
            expiration_time_str=""
            if token_json.get('expires_in', 0) > 2700:
                expiration_time_str = self.calculate_expiration(2700)
            else:
                expiration_time_str = self.calculate_expiration(token_json['expires_in'])
            token_json['expiration_time'] = expiration_time_str
            print(f"Token expires at: {expiration_time_str}")
            
            os.environ["MSFT_TOKEN_JSON"] = json.dumps(token_json)
            MSFT_TOKEN_JSON = json.dumps(token_json)
            
            # Get the home path of the current user
            home_path = os.path.expanduser("~")
            if not os.path.exists(os.path.join(home_path, '.setup')):
                os.makedirs(os.path.join(home_path, '.setup'))
            token_path = os.path.join(home_path, '.setup', 'token.json')
            with open(token_path, 'w') as f:
                f.write(MSFT_TOKEN_JSON)
            
        else:
            return f"""Failed to obtain access token for request: {json.dumps(token_data, indent=4)} 
                    Response Code/Text:{response.status_code}\n{response.text}""" 

        if 'access_token' in token_json:
            access_token = token_json['access_token']
        else:
            access_token = ''

        return jsonify({"status": "Access token obtained"}), 200

    async def call_openai_api(prompt=None):        
        """
        Call OpenAI API with the given prompt and return the response.
        """
        try:
            if not prompt:
                prompt = "Write me a haiku about Star Wars."

            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            reply = completion.choices[0].message.content
            return jsonify({'response': reply})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    async def create_task(self,task_request=None):
        global access_token
        data = await request.get_json()
        user_request = data.get('user_request')

        if not access_token or not user_request:
            return jsonify({"error": "Missing access token or user request"}), 400

        task_details = self.create_todo_task_with_user_request(user_request, access_token)

        if task_details:
            url = "https://graph.microsoft.com/v1.0/me/todo/tasks"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=task_details)

            if response.status_code == 201:
                return jsonify(response.json()), 201
            else:
                return jsonify({"error": response.text}), response.status_code
        else:
            return jsonify({"error": "Invalid task details generated"}), 500

    async def create_task_no_auth(self):
        data = await request.get_json()
        user_request = data.get('user_request')

        # Assume that the global access_token variable is set with the access token.
        task_details = self.create_todo_task_with_user_request(user_request, access_token)
    
    async def parse_response(self, response_text):
        """
        Parse the response text to extract a JSON object.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            try:
                start_index = response_text.find('{')
                end_index = response_text.rfind('}') + 1
                if start_index != -1 and end_index != -1:
                    json_str = response_text[start_index:end_index]
                    return json.loads(json_str)
                else:
                    print("Error: No JSON object found in the response.")
                    return None
            except json.JSONDecodeError:
                print("Error: Failed to parse JSON from the cleaned response.")
                return None
    
    def create_todo_task_with_user_request(self, user_request, access_token):
        """
        Create a new task in Microsoft To Do using Microsoft Graph API based on a user request.
        The function replaces [USERREQUEST] in the template, calls the API, and handles the response defensively.

        :param user_request: String containing the user's task request.
        :param access_token: String containing the OAuth2 access token.
        :return: Parsed JSON response from the API or None if parsing fails.
        """
        # Prompt template with placeholder
        prompt_template = """
        User request: 

        ```text
        [USERREQUEST]
        ```

        Generate a task_details dictionary for a Microsoft To Do task based on the above user request.
        The dictionary should include the following fields, if applicable:

        1. **Title**:
        - Extract the main action or task from the request. Use a concise and descriptive title.

        2. **Body**:
        - Include all the details provided in the user request.

        3. **Importance**:
        - Default to "normal".
        - If the request indicates urgency, set to "high".

        4. **Due Date**:
        - If the task has a specific time frame, set the dueDateTime accordingly.
        - For tasks like "by Friday end of day," calculate the date for the current week's Friday.

        5. **Recurrence**:
        - If the task needs to be repeated, set recurrence with a "noEnd" date.
        - Use weekly for tasks mentioned with specific days.

        6. **Checklist Items**:
        - Parse any subtasks or steps and include them as checklist items.

        7. **Linked Resources**:
        - Include any links provided in the request as linked resources.

        8. **Categories**:
        - Default to either "JBI" (for work-related tasks) or "Personal".
        - Use best judgment based on the content of the request.

        ```json
        {
        "title": "Example Task Title",
        "body": {
            "content": "Detailed description of the task.",
            "contentType": "text"
        },
        "importance": "normal",
        "dueDateTime": {
            "dateTime": "YYYY-MM-DDTHH:MM:SS",
            "timeZone": "UTC"
        },
        "recurrence": {
            "pattern": {
            "type": "weekly",
            "interval": 1,
            "daysOfWeek": ["thursday"]
            },
            "range": {
            "type": "noEnd"
            }
        },
        "checklistItems": [
            {"title": "Subtask 1"},
            {"title": "Subtask 2"}
        ],
        "linkedResources": [
            {
            "webUrl": "http://example.com",
            "applicationName": "Custom",
            "displayName": "Example Link"
            }
        ],
        "categories": ["JBI"]
        }
        ```

        Ensure that:

        - Importance should be set based on the sentiment of the request as either 'normal' or 'high' (never 'low').
        - Categories should be assigned as either "JBI" or "Personal" based on the context. 
        - All professional tasks should be categorized as "JBI". Default to "JBI" if not specified.
        - Recurrence should always be set to "noEnd" if applicable.

        Critically Important: 
        - The response should only contain the JSON object for the `task_details` dictionary. 
        - No other text should be included in the response. 
        - This is because the response is being systematically integrated, and non-compliant format responses will fail. 

        **Please ensure that your response strictly follows the above format and includes no additional text.**
        """

        # Replace the placeholder with the actual user request
        prompt = prompt_template.replace("[USERREQUEST]", user_request)

        # Call OpenAI API with the prompt
        ai_response = self.call_openai_api(prompt)

        return self.parse_response(ai_response)

