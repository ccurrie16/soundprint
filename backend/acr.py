import hmac
import hashlib
import base64
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("ACRCLOUD_ACCESS_KEY")
ACCESS_SECRET = os.getenv("ACRCLOUD_ACCESS_SECRET")
HOST = os.getenv("ACRCLOUD_HOST")


def identify(audio_bytes: bytes) -> dict:
    timestamp = str(int(time.time()))
    string_to_sign = "\n".join(["POST", "/v1/identify", ACCESS_KEY, "audio", "1", timestamp])
    sign = base64.b64encode(
        hmac.new(ACCESS_SECRET.encode(), string_to_sign.encode(), hashlib.sha1).digest()
    ).decode()

    response = requests.post(
        f"https://{HOST}/v1/identify",
        files={"sample": ("audio", audio_bytes, "audio/mpeg")},
        data={
            "access_key": ACCESS_KEY,
            "sample_bytes": len(audio_bytes),
            "timestamp": timestamp,
            "signature": sign,
            "data_type": "audio",
            "signature_version": "1",
        },
    )
    return response.json()
