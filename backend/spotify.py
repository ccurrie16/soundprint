import os
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import lastfm

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_token() -> str:
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    return response.json()["access_token"]


def _get_genres_from_musicbrainz(artist_name: str) -> list:
    try:
        r = requests.get(
            "https://musicbrainz.org/ws/2/artist/",
            params={"query": f"artist:{artist_name}", "fmt": "json", "limit": 1},
            headers={"User-Agent": "Soundprint/1.0 (contact@soundprint.app)"},
            timeout=5,
        )
        artists = r.json().get("artists", [])
        if not artists:
            return []
        tags = sorted(artists[0].get("tags", []), key=lambda x: x.get("count", 0), reverse=True)
        name_words = set(artist_name.lower().split())
        filtered = [
            t["name"] for t in tags
            if not all(w in name_words for w in t["name"].lower().split())
            and len(t["name"]) > 2
        ]
        return filtered[:10]
    except Exception:
        return []


def _resolve_on_spotify(title, artist: str, headers: dict) -> dict:
    q = f"track:{title} artist:{artist}" if title else f"artist:{artist}"
    try:
        search = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": q, "type": "track", "limit": 1},
            timeout=5,
        ).json()
        items = search.get("tracks", {}).get("items", [])
    except Exception:
        return None
    if not items:
        return None
    t = items[0]
    return {
        "title": t["name"],
        "artist": t["artists"][0]["name"],
        "spotify_url": t["external_urls"]["spotify"],
        "artist_id": t["artists"][0]["id"],
        "track_id": t["id"],
    }


def _similar_from_lastfm(title: str, artist_name: str, headers: dict) -> list:
    pairs = lastfm.get_similar_tracks(title, artist_name, limit=8)
    if not pairs:
        return []
    with ThreadPoolExecutor(max_workers=8) as pool:
        resolved = pool.map(lambda p: _resolve_on_spotify(p[0], p[1], headers), pairs)
        return [r for r in resolved if r]


def _similar_from_genre(genres: list, headers: dict) -> list:
    if not genres:
        return []
    subgenre = genres[1] if len(genres) > 1 else genres[0]
    genre_query = subgenre.replace(" ", "+")
    search = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": f"genre:{genre_query}", "type": "track", "limit": 20},
        timeout=5,
    ).json()
    return [
        {
            "title": t["name"],
            "artist": t["artists"][0]["name"],
            "spotify_url": t["external_urls"]["spotify"],
            "artist_id": t["artists"][0]["id"],
            "track_id": t["id"],
        }
        for t in search.get("tracks", {}).get("items", [])
    ]


def _get_genres_and_similar(artist_id: str, artist_name: str, title: str, track_id: str, headers: dict) -> tuple:
    artist_data = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers
    ).json()
    genres = artist_data.get("genres", [])

    if not genres:
        genres = _get_genres_from_musicbrainz(artist_name)

    candidates = _similar_from_lastfm(title, artist_name, headers)
    if len(candidates) < 5:
        candidates += _similar_from_genre(genres, headers)

    similar = []
    seen_artists = {artist_id}
    for c in candidates:
        if c["track_id"] != track_id and c["artist_id"] not in seen_artists:
            seen_artists.add(c["artist_id"])
            similar.append({k: c[k] for k in ("title", "artist", "spotify_url")})
        if len(similar) >= 5:
            break

    return genres, similar


def get_track_info(title: str, artist: str) -> dict:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    search = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": f"track:{title} artist:{artist}", "type": "track", "limit": 1},
    ).json()

    items = search.get("tracks", {}).get("items", [])
    if not items:
        return {}

    track = items[0]
    artist_id = track["artists"][0]["id"]
    track_id = track["id"]
    images = track["album"].get("images", [])

    artist_name = track["artists"][0]["name"]
    genres, similar = _get_genres_and_similar(artist_id, artist_name, track["name"], track_id, headers)

    return {
        "title": track["name"],
        "artist": artist_name,
        "album": track["album"]["name"],
        "release_date": track["album"]["release_date"],
        "genres": genres,
        "spotify_url": track["external_urls"]["spotify"],
        "album_art": images[0]["url"] if images else None,
        "similar_songs": similar,
    }


def search_tracks(query: str) -> list:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    search = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": query, "type": "track", "limit": 6},
    ).json()

    results = []
    for t in search.get("tracks", {}).get("items", []):
        images = t["album"].get("images", [])
        results.append({
            "track_id": t["id"],
            "title": t["name"],
            "artist": t["artists"][0]["name"],
            "album": t["album"]["name"],
            "album_art": images[0]["url"] if images else None,
        })
    return results


def get_track_by_id(track_id: str) -> dict:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    track = requests.get(
        f"https://api.spotify.com/v1/tracks/{track_id}", headers=headers
    ).json()

    artist_id = track["artists"][0]["id"]
    artist_name = track["artists"][0]["name"]
    images = track["album"].get("images", [])

    genres, similar = _get_genres_and_similar(artist_id, artist_name, track["name"], track_id, headers)

    return {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "release_date": track["album"]["release_date"],
        "genres": genres,
        "spotify_url": track["external_urls"]["spotify"],
        "album_art": images[0]["url"] if images else None,
        "similar_songs": similar,
    }
