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

from youtube_transcript_api import YouTubeTranscriptApi

@app.post("/ask")
async def ask(data: RequestData):

    video_url = data.video_url
    topic = data.topic

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
Find the FIRST timestamp when this topic is spoken.

Topic:
{topic}

Return ONLY timestamp in HH:MM:SS format.
Example:
00:05:47
"""

    response = model.generate_content(
        f"{video_url}\n{prompt}"
    )

    import re

    text = response.text

    match = re.search(r"\d{2}:\d{2}:\d{2}", text)

    if match:
        timestamp = match.group()
    else:
        timestamp = "00:01:00"

    return {
        "timestamp": timestamp,
        "video_url": video_url,
        "topic": topic
    }
