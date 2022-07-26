import requests
import os
from dotenv import load_dotenv

load_dotenv()

lastfm_token = os.getenv("lastfm_token")


class LastFM():
    def getRecentSong(self, user):
        self.params = {
            'method': 'user.getrecenttracks',
            'user': user,
            'api_key': lastfm_token,
            'extended': 1,
            'limit': 1,
            'format': 'json',
        }
        response = requests.get(
            'http://ws.audioscrobbler.com/2.0/', params=self.params)
        response = response.json()
        return response
