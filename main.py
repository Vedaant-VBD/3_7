from fastapi import FastAPI
from pydantic import BaseModel
import yt_dlp
import google.generativeai as genai
import time
import os
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# Request Schema
class RequestData(BaseModel):
    video_url: str
    topic: str


# Convert seconds → HH:MM:SS
def format_time(seconds):
    seconds = int(seconds)
    return str(timedelta(seconds=seconds))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "running"}

@app.head("/")
async def head():
    return {}

    
from youtube_transcript_api import YouTubeTranscriptApi
import re

@app.post("/ask")
async def ask(data: RequestData):

    video_url = data.video_url
    topic = data.topic

    # Extract video ID
    video_id = video_url.split("v=")[-1].split("&")[0]

    if "youtu.be" in video_url:
        video_id = video_url.split("/")[-1]

    # Get transcript
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    timestamp_seconds = 60  # default

    for line in transcript:
        if topic.lower() in line['text'].lower():
            timestamp_seconds = int(line['start'])
            break

    # Convert to HH:MM:SS
    hours = timestamp_seconds // 3600
    minutes = (timestamp_seconds % 3600) // 60
    seconds = timestamp_seconds % 60

    timestamp = f"{hours:02}:{minutes:02}:{seconds:02}"

    return {
        "timestamp": timestamp,
        "video_url": video_url,
        "topic": topic
    }
