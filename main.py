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

    
@app.post("/ask")
async def ask(data: RequestData):

    video_url = data.video_url
    topic = data.topic

    # Download audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # Upload audio
    file = genai.upload_file(path="audio.mp3")

    # Wait ACTIVE
    while file.state.name != "ACTIVE":
        time.sleep(2)
        file = genai.get_file(file.name)

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
Find first timestamp when topic is spoken.

Topic: {topic}

Return ONLY HH:MM:SS
"""

    response = model.generate_content([file, prompt])

    import re

    raw = response.text.strip()

    match = re.search(r'\d{2}:\d{2}:\d{2}', raw)

    if match:
        timestamp = match.group()
    else:
        timestamp = "00:01:00"

    if os.path.exists("audio.mp3"):
        os.remove("audio.mp3")

    return {
        "timestamp": timestamp,
        "video_url": video_url,
        "topic": topic
    }
