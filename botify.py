import os
import azure.cognitiveservices.speech as speechsdk
import emoji
from openai import  OpenAI
import pandas as pd
from dotenv import load_dotenv
from autoplotlib.main import plot
from termcolor import colored, cprint
from rich import print
from rich.console import Console

console = Console()

# from langchain.agents.agent_types import AgentType
# from langchain_experimental.agents.agent_toolkits import create_csv_agent
# from langchain_openai import ChatOpenAI, OpenAI

# Load environment variables from .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = "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"
# Now you can access the variables as before
azure_endpoint=os.environ.get('OPEN_AI_ENDPOINT')
api_key=os.environ.get('OPEN_AI_KEY')
deployment_id=os.environ.get('OPEN_AI_DEPLOYMENT_NAME')
speech_key=os.environ.get('SPEECH_KEY')
speech_region=os.environ.get('SPEECH_REGION')

# This example requires environment variables named "OPEN_AI_KEY", "OPEN_AI_ENDPOINT" and "OPEN_AI_DEPLOYMENT_NAME"
# Your endpoint should look like the following https://YOUR_OPEN_AI_RESOURCE_NAME.openai.azure.com/
client = OpenAI(
    api_key=api_key,
)
df = pd.read_csv('data.csv', encoding='ISO-8859-1',nrows=45)
df_plot = pd.read_csv('data.csv', encoding='ISO-8859-1')
df = df.dropna()

df['combined']= 'Song: '+df['track_name']+', Artist: '+df['artist(s)_name']+', Streams: '+df['streams'].astype(str)+', Danceability: '+df['danceability_%'].astype(str)+', Released year: '+df['released_year'].astype(str)+', Artist count: '+df['artist_count'].astype(str)   

# client = AzureOpenAI(
# azure_endpoint=os.environ.get('OPEN_AI_ENDPOINT'),
# api_key=os.environ.get('OPEN_AI_KEY'),
# api_version="2023-05-15"
# )

# This will correspond to the custom name you chose for your deployment when you deployed a model.
# deployment_id=os.environ.get('OPEN_AI_DEPLOYMENT_NAME')

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"

context = df.to_json(orient='records')

speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language.
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)
# tts sentence end mark
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n" ]

# Prompts Azure OpenAI with a request and synthesizes the response.
def ask_openai(prompt):
    # Ask Azure OpenAI in streaming way
    # print(f"Sending to Azure OpenAI: {prompt}")
    if "plot" in prompt.lower() or "make a graph" in prompt.lower():
        plot(prompt, data=df_plot)
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=250, stream=True,
            temperature=0,

            messages=[{ "role":"system","content":"You are a helpful assistant and you are a music lover too, your name is Botify that answers the query by using given context in few words."},{ "role":"user","content":"Context: "+ context+"\n\n Query: "+prompt},]
        )
        collected_messages = []
        last_tts_request = None

        # iterate through the stream response stream
        for chunk in response:
            if len(chunk.choices) > 0:
                chunk_message = chunk.choices[0].delta.content  # extract the message
                if chunk_message is not None:
                    collected_messages.append(chunk_message)  # save the message
                    if chunk_message in tts_sentence_end: # sentence end found
                        text = ''.join(collected_messages).strip() # join the recieved message together to build a sentence
                        if text != '': # if sentence only have \n or space, we could skip
                            print(emoji.emojize("🤖"), end=" ")
                            console.print(f"Botify: {text}", style="bold green")
                            last_tts_request = speech_synthesizer.speak_text_async(text)
                            collected_messages.clear()

        # if there are still some messages left in the buffer, we should synthesize them
        text = ''.join(collected_messages).strip()

        if text != '':
            print(emoji.emojize(""), end=" ")
            console.print(f"Botify: {text}", style="bold green")
            last_tts_request = speech_synthesizer.speak_text_async(text)
            collected_messages.clear()
        if last_tts_request:
            last_tts_request.get()

# Continuously listens for speech input to recognize and send as text to Azure OpenAI
           
def botify():
    while True:
        print(emoji.emojize(":microphone:"), end=" ")
        print(emoji.emojize(":microphone:"), end=" ")
        print(emoji.emojize(":microphone:"),)
        cprint("Botify is listening. Say 'Stop' or press Ctrl-Z to end the conversation.", "blue", attrs=["bold"])
        try:
            # Get audio from the microphone and then send it to the TTS service.
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            # If speech is recognized, send it to Azure OpenAI and listen for the response.
            if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                if speech_recognition_result.text == "Stop.": 
                    print(emoji.emojize("👋"), end=" ")
                    console.print("Conversation ended.", style="bold green")
                    break
                print(emoji.emojize("🦻"), end=" ")
                cprint("Recognized speech: {}".format(speech_recognition_result.text),"green", attrs=["bold"])
                ask_openai(speech_recognition_result.text)
            elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
                print(emoji.emojize("😕"), end=" ")
                cprint("No speech could be recognized: {}".format(speech_recognition_result.no_match_details),"yellow", attrs=["bold"])
                break
            elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_recognition_result.cancellation_details
                print(emoji.emojize("👋"), end=" ")
                cprint("Speech Recognition canceled: {}".format(cancellation_details.reason),"yellow", attrs=["bold"])
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(emoji.emojize("❌"), end=" ")
                    cprint("Error details: {}".format(cancellation_details.error_details),"red", attrs=["bold"])
        except EOFError:
            break

# Main

try:
    botify()
except Exception as err:
    print("Encountered exception. {}".format(err))