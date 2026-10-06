import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")
API_URL = "https://ws.audioscrobbler.com/2.0/"


def _call(method: str, **params) -> dict:
    r = requests.get(
        API_URL,
        params={"method": method, "api_key": API_KEY, "format": "json", "autocorrect": 1, **params},
        headers={"User-Agent": "Soundprint/1.0"},
        timeout=5,
    )
    return r.json()


def get_similar_tracks(title: str, artist: str, limit: int = 5) -> list:
    """Return up to `limit` (title, artist) pairs, at most one per artist."""
    if not API_KEY:
        return []

    results = []
    seen_artists = {artist.lower()}

    try:
        data = _call("track.getsimilar", track=title, artist=artist, limit=50)
        for t in data.get("similartracks", {}).get("track", []):
            name = t["artist"]["name"]
            if name.lower() not in seen_artists:
                seen_artists.add(name.lower())
                results.append((t["name"], name))
            if len(results) >= limit:
                return results
    except Exception:
        pass

    # Obscure tracks often have no similar-track data, so fill in with similar artists
    try:
        data = _call("artist.getsimilar", artist=artist, limit=20)
        for a in data.get("similarartists", {}).get("artist", []):
            name = a["name"]
            if name.lower() not in seen_artists:
                seen_artists.add(name.lower())
                results.append((None, name))
            if len(results) >= limit:
                break
    except Exception:
        pass

    return results
