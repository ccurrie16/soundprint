import os
import requests
from dotenv import load_dotenv

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
        return [t["name"] for t in tags[:10]]
    except Exception:
        return []


def _get_genres_and_similar(artist_id: str, artist_name: str, track_id: str, headers: dict) -> tuple:
    artist_data = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers
    ).json()
    genres = artist_data.get("genres", [])

    if not genres:
        genres = _get_genres_from_musicbrainz(artist_name)

    similar = []
    if genres:
        genre_query = genres[0].replace(" ", "+")
        search = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": f"genre:{genre_query}", "type": "track", "limit": 10},
        ).json()
        for t in search.get("tracks", {}).get("items", []):
            if t["id"] != track_id and t["artists"][0]["id"] != artist_id:
                similar.append({
                    "title": t["name"],
                    "artist": t["artists"][0]["name"],
                    "spotify_url": t["external_urls"]["spotify"],
                })
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
    genres, similar = _get_genres_and_similar(artist_id, artist_name, track_id, headers)

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

    genres, similar = _get_genres_and_similar(artist_id, artist_name, track_id, headers)

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
