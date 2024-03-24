import json
import os
import pandas as pd
from openai import  OpenAI

from dotenv import load_dotenv

load_dotenv()
# Now you can access the variables as before
azure_endpoint=os.environ.get('OPEN_AI_ENDPOINT')
api_key=os.environ.get('OPEN_AI_KEY')
deployment_id=os.environ.get('OPEN_AI_DEPLOYMENT_NAME')
speech_key=os.environ.get('SPEECH_KEY')
speech_region=os.environ.get('SPEECH_REGION')

df = pd.read_csv('data.csv', encoding='ISO-8859-1',nrows=40)
df = df.dropna()


df['combined']= 'Song: '+df['track_name']+' Artist: '+df['artist(s)_name']+' Streams: '+df['streams'].astype(str)+' Danceability: '+df['danceability_%'].astype(str)+' Speechiness: '+df['speechiness_%'].astype(str)+' Released year: '+df['released_year'].astype(str)+' Artist count: '+df['artist_count'].astype(str)   

# print(df.head())

client = OpenAI(
    api_key=api_key,
)

query = "Which song has lowest streams?"
context = df.to_json(orient='records')
response = client.chat.completions.create(
  model="gpt-4",
  messages=[
   { "role":"system","content":"You are a helpful assistant who only answers from the given context."},
   { "role":"user","content":"Context: "+ context+"\n\n Query: "+query},
  ]
)
print(response.choices[0].message.content)
# rawdata = open('data.csv', 'rb').read()
# result = chardet.detect(rawdata)
# print(result)