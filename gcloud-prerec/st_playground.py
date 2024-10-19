# Imports
import os
import threading
import traceback

import httpx
import streamlit as st
from _class_streamlit import streamlit_mytech
from _class_firebase import FirestoreStorage
from _class_aggrid import AggridUtils
import asyncio

stm = streamlit_mytech(theme='cfdark')
fire = FirestoreStorage()
agu = AggridUtils()

stm.set_up_page(page_title_text="Meeting Log",
                session_state_variables=[{"TransStatus": False}]) 

from deepgram import (
    DeepgramClient,
    FileSource,
    LiveOptions,
    LiveTranscriptionEvents,
    PrerecordedOptions,
)
from pytube import YouTube
from st_audiorec import st_audiorec


# from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# Configs
__version__ = "1.0.3"

MODELS = {
    "Nova-2": "nova-2-ea",
    "Nova": "nova",
    "Whisper Cloud": "whisper-medium",
    "Enhanced": "enhanced",
    "Base": "base",
}

LANGUAGES = {
    "Automatic Language Detection": None,
    "English": "en",
    "French": "fr",
    "Hindi": "hi",
}


def _read_from_youtube(url: str) -> str:
    yt = YouTube(url)

    video = yt.streams.filter(only_audio=True).first()

    out_file = video.download()
    base, ext = os.path.splitext(out_file)
    audio_file = f"{base}.mp3"

    if os.path.isfile(audio_file):
        os.remove(audio_file)
    os.rename(out_file, audio_file)

    return audio_file

def streaming(url: str, options: LiveOptions):
    try:
        # Create a websocket connection to Deepgram
        dg_connection = deepgram.listen.live.v("1")
        ctx = get_script_run_ctx()

        def on_open(self, open, **kwargs):
            st.info(
                "Use the 'Stop' button at the top right to stop transcription",
            )
            st.info("Starting transcription...")

        def on_message(self, result, **kwargs):
            add_script_run_ctx(threading.current_thread(), ctx)
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0:
                st.text(sentence)

        def on_close(self, close, **kwargs):
            st.warning("Stopping stream...")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        if dg_connection.start(options) is False:
            st.error("Failed to start connection")
            return

        lock_exit = threading.Lock()
        exit = False

        # define a worker thread
        def myThread():
            with httpx.stream("GET", url) as r:
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit:
                        break
                    lock_exit.release()

                    dg_connection.send(data)

        # start the worker thread
        myHttp = threading.Thread(target=myThread)
        myHttp.start()

        # signal finished
        input("")
        lock_exit.acquire()
        exit = True
        lock_exit.release()

        # Wait for the HTTP thread to close and join
        myHttp.join()

        # Indicate that we've finished
        dg_connection.finish()

        st.success("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


def prerecorded(source, options: PrerecordedOptions) -> None:
    if audio_yt != "Audio URL":
        payload: FileSource = {"buffer": source["buffer"]}
        response = (
            deepgram.listen.prerecorded.v("1")
            .transcribe_file(
                payload,
                options,
            )
            .to_dict()
        )

    else:
        response = (
            deepgram.listen.prerecorded.v("1")
            .transcribe_url(
                source,
                options,
            )
            .to_dict()
        )

    # Write the response to the console
    if detected_language := response["results"]["channels"][0].get("detected_language", None):
        st.write(
            f"__Detected language:__ {detected_language} ({list(LANGUAGES.keys())[list(LANGUAGES.values()).index(detected_language)]})"
        )

    # FIXME: Parse multichannel response
    if summarize:
        tab1, tab2, tab3 = st.tabs(["Response", "🗒️Transcript", "🤏Summary"])
        try:
            tab3.write(
                response["results"]["channels"][0]["alternatives"][0]["summaries"][0]["summary"]
            )
        except Exception as e:
            st.error(e)
    else:
        tab1, tab2 = st.tabs(["Response", "Transcript"])
    try:
        tab1.write(response)
    except Exception as e:
        st.error(e)
    try:
        if paragraphs or smart_format:
            tab2.write(
                response["results"]["channels"][0]["alternatives"][0]["paragraphs"]["transcript"]
            )
        else:
            tab2.write(response["results"]["channels"][0]["alternatives"][0]["transcript"])
    except Exception as e:
        st.error(e)

lcol, mcol, rcol = st.columns(3)
audio_format = st.radio("Format",
    options=[
        "Prerecorded",
        "Streaming",
    ], horizontal=True,label_visibility="collapsed"
)

if audio_format == "Streaming":
    del LANGUAGES["Automatic Language Detection"]

language = st.sidebar.selectbox(
    "Language",
    options=list(LANGUAGES.keys()),
    help="Some features are [only accessible in certain languages](https://developers.deepgram.com/documentation/features/)",
)

lang_options = {
    "detect_language"
    if language == "Automatic Language Detection"
    else "language": (True if language == "Automatic Language Detection" else LANGUAGES[language])
}

model = st.sidebar.selectbox(
    "Model",
    options=list(MODELS.keys()),
    help="[Models overview](https://developers.deepgram.com/docs/models-overview)",
)
deepgram = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])

with st.sidebar:

    # TODO: Add WebVTT/SRT captions (https://developers.deepgram.com/docs/automatically-generating-webvtt-and-srt-captions)
    # TODO: Add find&replace, keywords, sample rate
    # TODO: Better handling of disabled features (don't turn on by default)
    
    # FIXME: Handle case when language is changed after unsupported feature is selected
    with st.expander("Features", expanded=True):
        if channels := st.checkbox(
            "Channels",
            help="Specify the number of independent audio channels your submitted streaming audio contains",
            value=audio_format == "Streaming",
            disabled=audio_format != "Streaming",
        ):
            num_channels = st.number_input("Number of channels", min_value=1)
        else:
            num_channels = 1

        detect_topics = st.checkbox(
            "Topic Detection",
            help="Indicates whether Deepgram will identify and extract key topics for sections of content",
            value=audio_format == "Prerecorded",
            disabled=audio_format != "Prerecorded",
        )

        diarize = st.checkbox(
            "Diarization",
            help="Indicates whether to recognize speaker changes",
            value=True,
        )

        detect_entities = st.checkbox(
            "Entity Detection",
            help="Indicates whether Deepgram will identify and extract key entities for sections of content",
            value=audio_format == "Prerecorded",
            disabled=audio_format != "Prerecorded",
        )

        encoding = st.selectbox(
            "Encoding",
            options=["linear16", "flac", "mulaw", "amr-nb", "amr-nb", "opus", "speex"],
            help="Specify the expected encoding of the submitted streaming audio",
            disabled=audio_format != "Streaming",
        )

        endpointing = st.checkbox(
            "Endpointing",
            help="Returns transcripts when pauses in speech are detected",
            value=audio_format == "Streaming",
            disabled=audio_format != "Streaming",
        )

        interim_results = st.checkbox(
            "Interim results",
            help="""Provides preliminary results for streaming audio to solve the need for immediate 
            results combined with high levels of accuracy""",
            value=False,
            disabled=audio_format != "Streaming",
        )

        multichannel = st.checkbox(
            "Multichannel",
            help="Recognizes multiple audio channels and transcribes each channel independently",
        )

        paragraphs = st.checkbox(
            "Paragraphs",
            help="""Indicates whether Deepgram will split audio into paragraphs to improve transcript readability. 
            When paragraphs is set to true, punctuate will also be set to true""",
            value=audio_format == "Prerecorded",
            disabled=audio_format != "Prerecorded",
        )

        profanity_filter = st.checkbox(
            "Profanity filter",
            help="Indicates whether to remove profanity from the transcript",
        )

        punctuate = st.checkbox(
            "Punctuation",
            help="Indicates whether to add punctuation and capitalization to the transcript",
        )

        if redact := st.checkbox(
            "Redaction",
            help="Indicates whether to redact sensitive information, replacing redacted content with asterisks (*)",
        ):
            lcol, rcol = st.columns([1, 14])
            numbers = rcol.checkbox("Numbers", help="Aggressively redacts strings of numerals")
            pci = rcol.checkbox(
                "PCI",
                help="Redacts sensitive credit card information, including credit card number, expiration date, and CVV",
            )
            ssn = rcol.checkbox("SSN", help="Redacts social security numbers")
        else:
            pci = ssn = numbers = None
        redact_options = [
            "pci" if pci else None,
            "ssn" if ssn else None,
            "numbers" if numbers else None,
        ]

        if search := st.checkbox(
            "Search",
            help="""
            Terms or phrases to search for in the submitted audio. 
            Deepgram searches for acoustic patterns in audio rather than text patterns in transcripts 
            because we have noticed that acoustic pattern matching is more performant.
            """,
        ):
            search_terms = st.text_input(
                "Search terms",
                placeholder="TERM_1, TERM_2",
                help="Enter terms as comma-separated values",
            )
        else:
            search_terms = ""

        smart_format = st.checkbox(
            "Smart Format",
            help="""Smart Format improves readability by applying additional formatting. 
            When enabled, the following features will be automatically applied: 
            Punctuation, Numerals, Paragraphs, Dates, Times, and Alphanumerics""",
            value=True,
        )

        summarize = st.checkbox(
            "Summarization",
            help="""Indicates whether Deepgram will provide summaries for sections of content. 
            When Summarization is enabled, Punctuation will also be enabled by default""",
            value=audio_format == "Prerecorded",
            disabled=audio_format != "Prerecorded",
        )

        if utterances := st.checkbox(
            "Utterences",
            help="""Segments speech into meaningful semantic units. 
                By default, when utterances is enabled, it starts a new utterance after 0.8s of silence. 
                You can customize the length of time used to determine where to split utterances with the utt_split parameter""",
            value=audio_format == "Prerecorded",
            disabled=audio_format != "Prerecorded",
        ):
            utt_split = st.number_input(
                "Utterance split",
                min_value=0.0,
                step=0.1,
                value=0.8,
                help="""Length of time in seconds of silence between words that Deepgram will use 
                when determining where to split utterances. Default is 0.8""",
            )
        else:
            utt_split = 0.8

    







if audio_format == "Streaming":
    url = st.text_input(
        "Streaming audio URL",
        key="url",
        value="http://stream.live.vc.bbcmedia.co.uk/bbc_world_service",
    )

    options = LiveOptions(
        model=MODELS[model],
        channels=num_channels,
        diarize=diarize,
        encoding=encoding,
        endpointing=endpointing,
        interim_results=interim_results,
        multichannel=multichannel,
        profanity_filter=profanity_filter,
        punctuate=punctuate,
        redact=[option for option in redact_options if option],
        search=f"""[{search_terms or ""}]""",
        smart_format=smart_format,
    )

elif audio_format == "Prerecorded":
    # TODO: Extract audio from video for all modes
    audio_source = st.radio(
        "Choose audio source",
        options=[
            "Pick a sample file",
            "️Record audio️",
            "Upload audio file",
            "Load from URL",
        ],
        horizontal=True,
    )

    audio_yt = None

    if audio_source == "Upload audio file":
        st.session_state["audio"] = st.file_uploader(
            label="Upload audio file",
            label_visibility="collapsed",
        )
        st.session_state["mimetype"] = (
            st.session_state["audio"].type if st.session_state["audio"] else None
        )

    elif audio_source == "Load from URL":
        audio_yt = st.radio(
            "Source type",
            options=["Audio URL", "Youtube link"],
            horizontal=True,
            label_visibility="collapsed",
        )
        url = st.text_input(
            "URL",
            key="url",
            value=(
                "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
                if audio_yt == "Audio URL"
                else "https://www.youtube.com/watch?v=qHrN5Mf5sgo"
            ),
        )

        if url != "":
            try:
                if audio_yt == "Audio URL":
                    st.session_state["audio"] = url
                else:
                    st.session_state["audio"] = _read_from_youtube(url)
            except Exception as e:
                st.error(e)

    elif audio_source == "️Record audio️":
        st.session_state["audio"] = st_audiorec()

    else:
        st.session_state["audio"] = "assets/sample_file.wav"

    if st.session_state["audio"] and audio_source != "️🗣 Record audio️":
        if audio_source == "Load from URL" and audio_yt == "Youtube link":
            st.video(url)
        else:
            st.audio(st.session_state["audio"])

    options = PrerecordedOptions(
        model=MODELS[model],
        channels=num_channels,
        detect_topics=detect_topics,
        diarize=diarize,
        detect_entities=detect_entities,
        encoding=encoding,
        multichannel=multichannel,
        paragraphs=paragraphs,
        profanity_filter=profanity_filter,
        punctuate=punctuate,
        redact=[option for option in redact_options if option],
        smart_format=smart_format,
        summarize=summarize,
        search=f"""[{search_terms or ""}]""",
        utterances=utterances,
        utt_split=utt_split,
    )

if audio_format == "Prerecorded":
    # Check whether requested file is local, uploaded or remote, and prepare source
    if audio_source == "Load from URL":
        # file is remote
        if audio_yt == "Audio URL":
            source = {"url": url}
        else:
            source = {"buffer": open(st.session_state["audio"], "rb")}
    elif audio_source in (["⬆️ Upload audio file", "️🗣 Record audio️"]):
        # file is uploaded/recorded
        source = {
            "buffer": st.session_state["audio"],
        }
    else:
        # file is local
        source = {"buffer": open(st.session_state["audio"], "rb").read()}

if st.button("Transcribe",
    use_container_width=True,
    type="primary"
    ):
    try:
        if audio_format == "Streaming":
            streaming(url, options)
        else:
            prerecorded(source, options)
    except Exception as e:
        if str(e).endswith("timed out"):
            st.error(
                f"""{e}  
                Please try after some time, or try with a smaller source if the issue persists.""",
                icon="⌚",
            )
        else:
            st.error(
                f"""The app has encountered an error:  
                `{e}`  
                Please create an issue [here](https://github.com/SiddhantSadangi/st_deepgram_playground/issues/new) 
                with the below traceback""",
                icon="🥺",
            )
            st.code(traceback.format_exc())



if not 'transcription_records' in st.session_state:
    st.session_state["transcription_records"] = fire.get_transcription_records_sync()

agu.display_grid(st.session_state["transcription_records"])

# st.dataframe(transcriptions, height=(len(transcriptions)+1)*30)

