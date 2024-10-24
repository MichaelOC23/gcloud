from flask import Flask, request, jsonify
import json
import os
import setproctitle
from datetime import datetime, time
from openai import OpenAI
from _class_deepgram_final import deepgram_audio_transcription
from _class_office365 import office365_tools
import markdown

DEFAULT_INPUT_DEVICE_CODE = 'InCaMi'
dg = deepgram_audio_transcription()
o365 = office365_tools()

# Set your API key as an environment variable

API_KEY = os.environ.get('HORIZON_API_KEY', 'super_secret_api_key_4815162342')

def check_api_key():
    """
    Simple function to validate the API key from the request headers.
    """
    api_key = request.headers.get('x-api-key', '')
    if api_key is None:
        return False
    if api_key == API_KEY or api_key == 'super_secret_api_key_4815162342':
        return True
    return False
        
app = Flask(__name__)

@app.before_request
def validate_api_key():
    """
    Flask middleware to check the API key before processing any request.
    """
    if not check_api_key():
        return jsonify({'error': 'Unauthorized: Invalid API key'}), 401

# Example route
@app.route('/transcribeaudiofile', methods=['POST'])
def transcribeaudiofile():
    
    
    try:
        uploaded_file = request.files.get('audiofile')
        file_to_transcribe = uploaded_file.read()
    except Exception as e:
        return jsonify({'status': 'failed', 'error': f'No file bad file {e}'}), 400
    
    try:     
        response_format = request.form.get('response-format')
    except:
        response_format = 'html'

    
    
    if file_to_transcribe == None:
        return jsonify({'status': 'failed', 'error': f'No file bad file {e}'}), 400
    else:
        from _class_deepgram_final import deepgram_prerecorded_audio_transcription
        prerec = deepgram_prerecorded_audio_transcription()
        transcription_dict = prerec.transcribe_prerecorded_audio(file_to_transcribe)
        if isinstance(transcription_dict, dict):
            transcription_dict['ai_summary'] = prerec.summarize_transcription_with_gemini(transcription_dict)
            markdown_text = f"""___\n Created On: {datetime.now()}\nOriginal File: {uploaded_file}\n\n___\n### MEETING SUMMARY\n___   \n{transcription_dict.get('ai_summary', '')}\n\n\n___\n### ORIGINAL TRANSCRIPTION\n___   \n{transcription_dict.get('by_speaker', '')}"""
            html_text = markdown.markdown(markdown_text)
    
    if response_format == 'by_speaker': return transcription_dict['by_speaker']
    if response_format == 'by_paragraph': return transcription_dict['by_paragraph']
    if response_format == 'by_speaker_list_of_dicts': return transcription_dict['by_speaker_list_of_dicts']
    if response_format == 'html': return html_text
    if response_format == 'markdown': return markdown
    if response_format == 'summary_only': return transcription_dict['ai_summary']
    
    return html_text

@app.route('/')
def call_openai_api(prompt=None):
    """
    Call OpenAI API with the given prompt and return the response.
    """
    if not validate_api_key(): exit()
    
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

@app.route('/startlog')
def start_log_default():
    val = start_meeting_log()
    return "Starting default meeting"

@app.route('/startlogmic')
def start_log_mic():
    val = start_meeting_log('InCaMic')
    return "Starting mic meeting"
    
@app.route('/startlogap')
def start_log_airpods():
    val = start_meeting_log('InCaAp')
    return "Starting AirPod meeting"
    
@app.route('/startlogcustom')
def start_log_custom():
    val = start_meeting_log('InCaCustom')
    return "Starting custom meeting"

def start_meeting_log(input_device=DEFAULT_INPUT_DEVICE_CODE):
    print(f"Starting Meeting Log with Input Device {input_device}")
    try:
        result = dg.start_transcription(input_device)
        config = list_devices()
        return jsonify({'status': 'started', 'transcription': result, 'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/listdevices')
def list_devices():
    config = dg.get_audio_config_dict()
    list = dg.get_audio_device_list()
    return jsonify({'devices': [config, list]})

@app.route('/stoplog')
def stop_meeting_log():
    """
    Stop the transcription process.
    """
    try:
        dg.stop_transcription()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def parse_response(response_text):
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

#########################################
####      OFFICE 365  FUNCTIONS      ####
#########################################

@app.route('/setglobalaccesstoken', methods=['POST'])
def setglobalaccesstoken():
    return o365.set_value(request)
 
@app.route('/exporttoken')
def exporttoken():
    return o365.export_token(request)

@app.route('/redirect')
def redirect():
    return o365.auth_redirect(request)
 
@app.route('/create_task_auth', methods=['POST'])
def createtask():
    return o365.create_task(request)
 
@app.route('/create_task_no_auth', methods=['POST'])
def createtasknoauth():
    return o365.create_task_no_auth(request)
 
if __name__ == "__main__":
    setproctitle.setproctitle("horizonbackground")
    port_number = os.environ.get('OFFICE365_BACKGROUND_PORT', '8080')
    app.run(host="0.0.0.0", port=int(port_number), debug=False)
    print("horizonbackground server started successfully.")

print("Loaded Custom Flask App")
