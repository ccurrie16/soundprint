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


def get_track_info(title: str, artist: str) -> dict:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    search = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": f"track:{title} artist:{artist}", "type": "track", "limit": 1},
    ).json()

    tracks = search.get("tracks", {}).get("items", [])
    if not tracks:
        return {}

    track = tracks[0]
    artist_id = track["artists"][0]["id"]
    track_id = track["id"]

    artist_data = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers
    ).json()

    genres = artist_data.get("genres", [])

    related = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
        headers=headers,
    ).json()

    similar = []
    for related_artist in related.get("artists", [])[:3]:
        top = requests.get(
            f"https://api.spotify.com/v1/artists/{related_artist['id']}/top-tracks",
            headers=headers,
            params={"market": "US"},
        ).json()
        tracks = top.get("tracks", [])
        if tracks:
            t = tracks[0]
            similar.append({
                "title": t["name"],
                "artist": t["artists"][0]["name"],
                "spotify_url": t["external_urls"]["spotify"],
            })


    images = track["album"].get("images", [])
    album_art = images[0]["url"] if images else None

    return {
        "title": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "release_date": track["album"]["release_date"],
        "genres": genres,
        "spotify_url": track["external_urls"]["spotify"],
        "album_art": album_art,
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

    artist_data = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers
    ).json()

    genres = artist_data.get("genres", [])

    related = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
        headers=headers,
    ).json()

    similar = []
    for related_artist in related.get("artists", [])[:3]:
        top = requests.get(
            f"https://api.spotify.com/v1/artists/{related_artist['id']}/top-tracks",
            headers=headers,
            params={"market": "US"},
        ).json()
        tracks = top.get("tracks", [])
        if tracks:
            t = tracks[0]
            similar.append({
                "title": t["name"],
                "artist": t["artists"][0]["name"],
                "spotify_url": t["external_urls"]["spotify"],
            })

    images = track["album"].get("images", [])

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
