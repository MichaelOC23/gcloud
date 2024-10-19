

# print("Beginning Load of Deepgram Standard Libraries")
from signal import SIGINT, SIGTERM
import asyncio
import socket
import os
import sys
import pyaudio
import whisper
import json
import httpx
import markdown
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# from _class_firebase import FirestoreStorage
# notelog = FirestoreStorage()
from _class_postgres_note_log import NoteLog
# print("Loaded Deepgram Standard Libraries")
notelog =  NoteLog()
from deepgram import (
    # Deepgram,
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    PrerecordedOptions,
    FileSource,
    Microphone,
)
# print("Completed Load of DeepGram Library")


# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []
is_final_speaker_words = []
is_final_speaker_statements = []
# from _class_postgres_note_log import NoteLog

# print("Beginning Load of Deepgram Custom Class")


class deepgram_prerecorded_audio_transcription():
    def __init__(self):
        # Audio Transcription
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.model = whisper.load_model("base")
        self.models = {
            "Nova-2": "nova-2-ea",
            "Nova": "nova",
            "Whisper Cloud": "whisper-medium",
            "Enhanced": "enhanced",
            "Base": "base",}
        self.languages = {
            "Automatic Language Detection": None,
            "English": "en",
            "French": "fr",
            "Hindi": "hi",}
        self.AUDIOINFO_GLOBAL = {}
        self.current_transcription_id = None

    def get_transcription_by_speaker(self, transcription):
        # Conversation Tab
        words = transcription.get('results', {}).get('channels', [])[0].get('alternatives', [])[0].get('words', [])
        prior_speaker = -1
        statements = []
        statement = ''
        for word in words:
            if prior_speaker == -1:
                prior_speaker = word.get('speaker', '')
                statement = f"{word.get('punctuated_word', '')}"
                continue
            
            if word.get('speaker', '') == prior_speaker:
                statement += f" {word.get('punctuated_word', '')}"
                continue
            
            if word.get('speaker', '') != prior_speaker:
                statements.append([f"Speaker {prior_speaker}", statement.strip()])
                prior_speaker = word.get('speaker', '')
                statement = f"{word.get('punctuated_word', '')}"
                continue
        statements.append([f"Speaker {prior_speaker}", statement.strip()])
        
        return statements

    def transcribe_prerecorded_audio(self, AUDIO_FILE):
        try:
            # STEP 1 Create a Deepgram client using the API key in the environment variables
            deepgram: DeepgramClient = DeepgramClient(self.deepgram_api_key)

            payload: FileSource = {
                "buffer": AUDIO_FILE,}
            options: PrerecordedOptions = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                utterances=True,
                punctuate=True,
                diarize=True,)
            
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options, timeout=httpx.Timeout(300.0, connect=10.0))
            
            by_speaker_text=''
            by_paragraph_text=''
            speaker_list = []
            by_speaker_list_of_lists = self.get_transcription_by_speaker(response.to_dict())
            for sentence in by_speaker_list_of_lists:
                speaker_list.append(f"Speaker {sentence[0]}")
                by_paragraph_text = f"{by_paragraph_text}\n\n{sentence[1]}"
                by_speaker_text = f"{by_speaker_text}  \n- **{sentence[0]}**: {sentence[1]}"
            
            speaker_list = list(set(speaker_list))
            response_dict = response.to_dict()
            response_dict["by_speaker"] = by_speaker_text
            response_dict["by_paragraph"] = by_paragraph_text
            response_dict["by_speaker_list_of_dicts"] = by_speaker_list_of_lists
            response_dict['speaker_list']= speaker_list
            
            return response_dict

        except Exception as e:
            response_dict = {"error": str(e)}
            response_dict = {"by_speaker": str(e)}   
            return response_dict
        

    def transcribe_prerecorded_audio_local(self, AUDIO_FILE):
        try:
            # STEP 1: Transcribe audio using Whisper
            result = self.model.transcribe(AUDIO_FILE)
            
            # STEP 2: Extract text and segments from the result
            transcription_text = result["text"]
            segments = result["segments"]  # Whisper segments the audio

            # Initialize empty strings and lists for speaker handling
            by_speaker_text = ''
            by_paragraph_text = ''
            speaker_list = []
            by_speaker_list_of_lists = []

            # Whisper doesn't handle speaker diarization, but you can mock it or segment the text
            # For simplicity, we'll just split segments into paragraphs by timing
            for segment in segments:
                # For Whisper, we don't have speaker labels, so we'll mock them as "Speaker 1"
                speaker = "Speaker 1"
                text = segment['text'].strip()

                # Append to speaker list (even though Whisper doesn't provide speaker IDs, we'll simulate it)
                speaker_list.append(f"Speaker {speaker}")
                
                # Build paragraph and speaker text (whisper doesn't provide diarization by default)
                by_paragraph_text += f"{text}\n\n"
                by_speaker_text += f"- **{speaker}**: {text}\n"
                
                # For consistency with your structure, we'll append each sentence to the list
                by_speaker_list_of_lists.append([speaker, text])

            # Create a unique speaker list (though Whisper doesn't detect multiple speakers without diarization)
            speaker_list = list(set(speaker_list))

            # Construct response similar to the structure in the Deepgram output
            response_dict = {
                "text": transcription_text,
                "segments": segments,
                "by_speaker": by_speaker_text,
                "by_paragraph": by_paragraph_text,
                "by_speaker_list_of_dicts": by_speaker_list_of_lists,
                "speaker_list": speaker_list
            }

            return response_dict

        except Exception as e:
            # Error handling
            response_dict = {
                "error": str(e),
                "by_speaker": str(e)
            }
            return response_dict
    
    
        
    def extract_json_dict_from_llm_response(self, content):
        def try_to_json(input_value):
            try:
                first_dict_attempt = json.loads(input_value)
                return first_dict_attempt
            except:
                return input_value
        
        try:
            json_dict = try_to_json(content)
            if isinstance(json_dict, dict) or isinstance(json_dict, list):
                return json_dict
        except Exception as e:
            pass
            print(f"Initial attempt to convert to JSON failed: {e}")
            print(f"The content is: {content}")
            print(f"Trying to extract JSON from the content without attempting to isolate it the json string did not succedd.")
            print(f"We will now attempt to extract the JSON string from the content.")
                    
        # Find the first '{' and the last '}'
        start_idx = content.find('{')
        end_idx = content.rfind('}')

        if start_idx == -1 or end_idx == -1:
            return content

        try:
            # Extract the JSON string
            json_string = content[start_idx:end_idx + 1]
            
            json_dict = try_to_json(json_string)
            if  isinstance(json_dict, dict) or isinstance(json_dict, list):
                return json_dict
            else:
                print(f"After 2 attempts to obtain a dictionary from the response, both failed. Returning the content.")
                return content
        except Exception as e:
            print(f"After 2 attempts to obtain a dictionary from the response, both failed. Returning the content and providng the Error: {e}")
            return content
            
    def summarize_transcription_with_gemini(self, transcript_dict):
        if not isinstance(transcript_dict, dict):
            return ''
        
        transcript_text = transcript_dict.get('by_speaker', '')    
        
        json_response_format={ 
                            "summary": "<Place the markdown summary here>", 
                            "commentary": "<Include your commentary about the summary process here>"
                            }
        
        instructions = f"""
        Please summarize the following meeting transcription, extracting key topics by type:
            * Action items
            * Follow-up items
            * Decisions
            * Factual statements
            * Opinions
            * Speculations
            * Objectives (short, medium, long-term)
            * Sales approaches
            * Product functions
            * Names, tiles, companies, roles and/or backgrounds of participants who provide said information

            Organize the summary by topic type using a markdown format with headers (e.g., "#### Factual Statements").

            Once you have summarized the transcription, please provide the summary and any commentary about the process in a JSON object with the following structure:

            ```json
            {json.dumps(json_response_format, indent=4)}
            ```
            
            Transcrioption Text:
            {transcript_text}
            """ 

        try:
            response = self.fetch_gemini_json_response(instructions)
            hopefully_a_dict = self.extract_json_dict_from_llm_response(response.text)
            if not response or not isinstance(hopefully_a_dict, dict):
                response = self.fetch_gemini_json_response(instructions)
                hopefully_a_dict = self.extract_json_dict_from_llm_response(response.text)
                if not response or not isinstance(hopefully_a_dict, dict):
                    print("Error: Bad response from Gemini (on 2nd attempt)")
                    return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""
        
        summary = f"{hopefully_a_dict.get('summary', hopefully_a_dict)} \n\n___  \n\n{hopefully_a_dict.get('commentary', '')} "
        
        return summary

    def fetch_gemini_json_response(self, prompt):
            model = genai.GenerativeModel(model_name='gemini-1.5-flash')
            generation_config = {
                        "temperature": .5,
                        "top_p": 0.95,
                        "top_k": 34,
                        "max_output_tokens": 32000,
                        "response_mime_type": "application/json",
                        }
            response = model.generate_content(prompt, generation_config=generation_config,
                                            safety_settings={
                                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
                                                }
                                            )
            return response
                



class deepgram_audio_transcription():
    def __init__(self):
        # Audio Transcription
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.models = {
            "Nova-2": "nova-2-ea",
            "Nova": "nova",
            "Whisper Cloud": "whisper-medium",
            "Enhanced": "enhanced",
            "Base": "base",
        }
        self.languages = {
            "Automatic Language Detection": None,
            "English": "en",
            "French": "fr",
            "Hindi": "hi",
        }
        self.download_directory = os.path.expanduser('~/Downloads')
        if not os.path.exists(self.download_directory):
            os.mkdir(self.download_directory)
        self.AUDIOINFO_GLOBAL = {}
        self.current_transcription_id = None

    async def get_audio_config_dict(self):
        p = pyaudio.PyAudio()

        self.AUDIOINFO_GLOBAL["default_input_device_info"]= p.get_default_input_device_info()['index']
        self.AUDIOINFO_GLOBAL["default_output_device_info"]= p.get_default_output_device_info()['index']
        self.AUDIOINFO_GLOBAL['device_count'] = p.get_device_count()

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            self.AUDIOINFO_GLOBAL[f"#{i}-{dev['name']}"] = dev
        p.terminate()
                
        return self.AUDIOINFO_GLOBAL

    async def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("0.0.0.0", port)) == 0

    async def get_device_by_input_code(self, input_code='InCaMic'):
        pass
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            if input_code in p.get_device_info_by_index(i)['name']:
                print (f"index:{i}: {p.get_device_info_by_index(i)['name']}")
                return i
        
    async def get_audio_device_list(self):
        import pyaudio

        # Create an instance of PyAudio
        p = pyaudio.PyAudio()

        # Get the number of audio devices
        num_devices = p.get_device_count()

        # Get the info for each audio device
        device_list = []
        for i in range(0, num_devices):
            info = p.get_device_info_by_index(i)
            device_list.append(f"-  Device {i}: {info['name']} - Max Input Channels: {info['maxInputChannels']}  \n")
        return device_list

    async def start_transcription(self, input_code):
        transcription = []
        microphone = None
        try:
            loop = asyncio.get_event_loop()
            for signal in (SIGTERM, SIGINT):
                loop.add_signal_handler(
                    signal,
                    lambda: asyncio.create_task(
                        self.shutdown(signal, loop, dg_connection, microphone)
                    ),
                )

            config: DeepgramClientOptions = DeepgramClientOptions(
                options={"keepalive": "true"}
            )
            # Initialize the DeepgramClient with the API key
            deepgram: DeepgramClient = DeepgramClient(self.deepgram_api_key, config)

            dg_connection = deepgram.listen.asyncwebsocket.v("1")

            async def on_open(self, open, **kwargs):
                try:
                    print("Connection Open")
                except Exception as e:
                        (f"Error in on_open: {e}")

            async def on_message(self, result, **kwargs):
                try:
                    global is_finals
                    global is_final_speaker_words
                    global is_final_speaker_statements
                    sentence = result.channel.alternatives[0].transcript
                    if len(sentence) == 0:
                        return
                    if result.is_final:
                        is_finals.append(sentence)
                        is_final_speaker_words.extend([{Word.speaker: Word.word} for Word in result.channel.alternatives[0].words])
                        if result.speech_final:
                            utterance = " ".join(is_finals)
                            print(f"Speech Final: {utterance}")
                            transcription.append(utterance)
                            speaker = result.channel.alternatives[0].words[0].speaker
                            is_final_speaker_statements.append({speaker: utterance} )
                            self.current_transcription_id = result.metadata.request_id
                            notelog.insert_utterance(result.metadata.request_id, speaker=speaker, utterance=utterance)
                            is_finals = []
                        else:
                            pass
                            print(f"Is Final: {sentence}")
                    else:
                        pass
                        print(f"Interim Results: {sentence}")
                except Exception as e:
                    print(f"Error in on_message: {e}")

            async def on_metadata(self, metadata, **kwargs):
                try:
                    print(f"Metadata: {metadata}")
                except Exception as e:
                    print(f"Error in on_metadata: {e}")

            async def on_close(self, close, **kwargs):
                try:
                    notelog.insert_note(self.current_transcription_id)
                    print("Connection Closed")
                except Exception as e:
                    print(f"Error in on_close: {e}")

            # Assign event handlers
            dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
            dg_connection.on(LiveTranscriptionEvents.Close, on_close)

            # Connect to WebSocket
            options: LiveOptions = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
                endpointing=300,
                diarize=True,
            )

            addons = {
                "no_delay": "true"
            }

            print("\n\nStart talking! Press Ctrl+C to stop...\n")
            if await dg_connection.start(options, addons=addons) is False:
                print("Failed to connect to Deepgram")
                return

            input_device_index = await self.get_device_by_input_code(input_code=input_code)
            
            microphone = Microphone(dg_connection.send, input_device_index=input_device_index)
            microphone.start()


            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                microphone.finish()
                await dg_connection.finish()
                print("Finished")
                return transcription

        except Exception as e:
            print(f"Could not open socket: {e}")
            return transcription

    async def stop_transcription(self):
        try:
            # Implement the logic to stop the transcription
            # This might involve setting a flag or removing 'logrunning.txt'
            if os.path.isfile('logrunning.txt'):
                os.remove('logrunning.txt')
                print("Transcription stopped successfully.")
            else:
                print("No transcription is currently running.")
        except Exception as e:
            print(f"Error in stop_transcription: {e}")

    async def shutdown(self, signal, loop, dg_connection, microphone):
        print(f"Received exit signal {signal.name}...")
        microphone.finish()
        await dg_connection.finish()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        print(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
        print("Shutdown complete.")
    
    # print("Loaded Deepgram Custom Class")
    
if __name__ == "__main__":
    # print(sys.argv)
    file_to_transcribe=''
    if len(sys.argv) >= 2 and sys.argv[1] != '':
        # print(f"{sys.argv}")
        file_to_transcribe = sys.argv[1] 
    if file_to_transcribe == None or not os.path.isfile(file_to_transcribe):
        print(f"Either no file or an invalid file was provided. Provided Path: {file_to_transcribe}")
    if file_to_transcribe is not None:
        prerec = deepgram_prerecorded_audio_transcription()
        transcription_dict = prerec.transcribe_prerecorded_audio(file_to_transcribe)
        if isinstance(transcription_dict, dict):
            transcription_dict['ai_summary'] = prerec.summarize_transcription_with_gemini(transcription_dict)
            markdown_text = f"___\n Created On: {datetime.now()}\nOriginal File: {sys.argv[1]}\n\n___\n### MEETING SUMMARY     ___\n{transcription_dict.get('ai_summary', '')}\n\n\n___\n### ORIGINAL TRANSCRIPTION     ___\n{transcription_dict.get('by_speaker', '')}"
            html_text = markdown.markdown(markdown_text)
            print(html_text)

