import requests


class ChatStats():
    def getStats(self):

        url = "https://api.streamelements.com/kappa/v2/chatstats/btmc/stats"

        querystring = {"limit": "100"}

        payload = ""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Authorization": "Bearer null",
            "Origin": "https://stats.streamelements.com",
            "Connection": "keep-alive",
            "Referer": "https://stats.streamelements.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "If-None-Match": "W/6c38-VYB+NyXghmTHIoMr2uXGSLwcGMA",
            "TE": "trailers"
        }

        response = requests.request(
            "GET", url, data=payload, headers=headers, params=querystring)
        response = response.json()
        return response
