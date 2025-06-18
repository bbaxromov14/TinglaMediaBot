import acoustid
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

def recognize_online(filename):
    try:
        duration, fingerprint = acoustid.fingerprint_file(filename)
        result = acoustid.lookup(API_KEY, fingerprint, duration)

        if result['status'] != 'ok' or not result.get('results'):
            return None

        best = result['results'][0]
        score = best.get('score', 0.0)
        recordings = best.get('recordings', [])
        if not recordings:
            return None

        recording = recordings[0]
        title = recording.get('title', 'Неизвестно')
        artists = recording.get('artists', [])
        artist = artists[0]['name'] if artists else 'Неизвестно'

        query = f"{artist} {title}"
        youtube_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        spotify_url = f"https://open.spotify.com/search/{requests.utils.quote(query)}"
        yandex_url = f"https://music.yandex.ru/search?text={requests.utils.quote(query)}"

        return {
            'title': title,
            'artist': artist,
            'score': score,
            'youtube': youtube_url,
            'spotify': spotify_url,
            'yandex': yandex_url
        }

    except Exception as e:
        return {'error': str(e)}
