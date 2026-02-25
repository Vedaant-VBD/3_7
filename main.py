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

@app.post("/ask")
def ask(data: RequestData):

    video_url = data.video_url
    topic = data.topic

    audio_file = "audio.mp3"

    # Step 1 — Download Audio Only
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': audio_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])


    # Step 2 — Upload to Gemini Files API
    file = genai.upload_file(audio_file)

    # Step 3 — Wait Until ACTIVE
    while file.state.name != "ACTIVE":
        time.sleep(2)
        file = genai.get_file(file.name)


    # Step 4 — Ask Gemini
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    Find the FIRST timestamp when this topic is spoken:

    Topic:
    {topic}

    Return ONLY timestamp in HH:MM:SS format.
    Example:
    00:05:47
    """

    response = model.generate_content(
        [file, prompt]
    )

    timestamp = response.text.strip()


    # Step 5 — Cleanup File
    if os.path.exists(audio_file):
        os.remove(audio_file)


    # Step 6 — Return Response
    return {
        "timestamp": timestamp,
        "video_url": video_url,
        "topic": topic
    }
