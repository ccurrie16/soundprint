import os
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import acr
import spotify

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_subgenre(title: str, artist: str, genres: list) -> str:
    prompt = (
        f'The song "{title}" by {artist} has these Spotify genres: {", ".join(genres)}. '
        f"Give me one specific subgenre label for this song. Reply with only the subgenre, nothing else."
    )
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return genres[0] if genres else ""


@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    acr_result = acr.identify(audio_bytes)
    metadata = acr_result.get("metadata", {})
    music = metadata.get("music", [])

    if not music:
        return {"error": "Song not recognized"}

    match = music[0]
    title = match["title"]
    artist = match["artists"][0]["name"]

    track_info = spotify.get_track_info(title, artist)
    if not track_info:
        return {"error": "Could not find song on Spotify"}

    subgenre = get_subgenre(title, artist, track_info["genres"])
    track_info["subgenre"] = subgenre

    return track_info
