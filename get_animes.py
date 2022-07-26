from dotenv import load_dotenv
import requests
import os

load_dotenv()

MAL_TOKEN = os.getenv("MAL_TOKEN")


class GetAnime():
    def collect_animes(self):
        self.headers = {
            'X-MAL-CLIENT-ID': MAL_TOKEN,
        }
        self.params = {
            'ranking_type': 'bypopularity',
            'limit': '500',
            'fields': "title,alternative_titles{en}"
        }
        self.animes = []
        self.animes_lower = []

        self.response = requests.get(
            'https://api.myanimelist.net/v2/anime/ranking', params=self.params, headers=self.headers)
        self.response = self.response.json()
        self.animes = [anime['node']['alternative_titles']['en'] if anime['node']['alternative_titles']['en']
                       is not None and anime['node']['alternative_titles']['en'] != "" else anime['node']["title"] for anime in self.response["data"]]

        self.response2 = requests.get(
            self.response['paging']['next'], headers=self.headers)
        self.response2 = self.response2.json()
        self.animes += [anime['node']['alternative_titles']['en'] if anime['node']['alternative_titles']['en']
                        is not None and anime['node']['alternative_titles']['en'] != "" else anime['node']["title"] for anime in self.response2["data"]]
        for anime in self.animes:
            anime_encoded = anime.encode("ascii", "ignore")
            anime = anime_encoded.decode()
            anime = anime.lower()
            self.animes_lower.append(anime)

        return self.animes, self.animes_lower

    def get_anime_list(self, user):
        self.headers = {
            'X-MAL-CLIENT-ID': MAL_TOKEN,
        }
        self.params = {
            'sort': 'list_updated_at',
            'fields': "title,alternative_titles{en},list_status"
        }
        self.response = requests.get(
            'https://api.myanimelist.net/v2/users/' + user + '/animelist', params=self.params, headers=self.headers)
        self.response = self.response.json()
        return self.response
