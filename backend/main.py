import os
import json
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import acr
import spotify

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://soundprint-psi.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MOOD_WORDS = {
    "melancholic", "dark", "energetic", "upbeat", "chill", "aggressive", "romantic",
    "sad", "happy", "intense", "dreamy", "smooth", "raw", "emotional", "introspective",
    "mellow", "atmospheric", "lo-fi", "ambient", "hype", "party", "conscious", "soulful",
}

ERA_PATTERNS = ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s",
                "50s", "60s", "70s", "80s", "90s"]


def _build_fallback(genres: list) -> dict:
    primary = genres[0] if genres else "Unknown"
    subgenre = genres[1] if len(genres) > 1 else ""
    mood = next((t for t in genres if t.lower() in MOOD_WORDS), "")
    era = next((t for t in genres if any(e in t.lower() for e in ERA_PATTERNS)), "")
    desc = f"{primary} music{' with ' + subgenre + ' elements' if subgenre else ''}."
    return {"primary_genre": primary, "subgenre": subgenre, "mood": mood, "era": era, "description": desc}


def get_genre_info(title: str, artist: str, genres: list) -> dict:
    tags_str = ", ".join(genres) if genres else "unknown"
    prompt = (
        f'The song "{title}" by {artist} has these genre tags: {tags_str}. '
        f'Return a JSON object with exactly these keys: '
        f'"primary_genre" (main genre), '
        f'"subgenre" (specific subgenre), '
        f'"mood" (2-3 mood words e.g. "Dark, Introspective"), '
        f'"era" (decade e.g. "2010s"), '
        f'"description" (2 sentences about the sonic characteristics of this genre for this artist). '
        f'Return only valid JSON with no markdown or extra text.'
    )
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
        )
        text = response.json()["choices"][0]["message"]["content"].strip()
        return json.loads(text)
    except Exception:
        return _build_fallback(genres)


def enrich(track_info: dict) -> dict:
    genre_info = get_genre_info(track_info["title"], track_info["artist"], track_info["genres"])
    track_info["genre_info"] = genre_info
    return track_info


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

    return enrich(track_info)


@app.get("/search")
def search(q: str):
    return spotify.search_tracks(q)


@app.get("/track/{track_id}")
def track(track_id: str):
    track_info = spotify.get_track_by_id(track_id)
    if not track_info:
        return {"error": "Track not found"}
    return enrich(track_info)
