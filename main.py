import os

import niquests
import tmdbsimple as tmdb
from dotenv import load_dotenv

import moneypatches  # noqa: F401 we just need to import it to apply the monkeypatch

load_dotenv()

tmdb.API_KEY = os.getenv("TMDB_API_KEY")
# This call now uses HTTP/2 or HTTP/3 via Niquests!
search = tmdb.Search()
response = search.movie(query="The Matrix")
print(response)


def main():
    print("Hello from mirarr!")

    session = niquests.Session()

    burp0_base_url = "https://rivestream.org:443/api/backendfetch"
    burp0_params = {
        "requestID": "tvVideoProvider",
        "id": "1418",  # TMDB ID
        "season": "1",  # Season Number
        "episode": "1",  # Episode Number
        "service": "flowcast",  # Service Name
        "secretKey": "NGFmNjhjZDg=",
        "proxyMode": "noProxy",
    }
    # burp0_cookies = {"_ga": "GA1.1.753096691.1769890818", "_ga_TY1B74WN3B": "GS2.1.s1769890818$o1$g0$t1769890855$j23$l0$h0"}
    # burp0_headers = {"Sec-Ch-Ua-Platform": "\"Linux\"", "Accept-Language": "en-GB,en;q=0.9", "Accept": "application/json", "Sec-Ch-Ua": "\"Not_A Brand\";v=\"99\", \"Chromium\";v=\"142\"", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36", "Sec-Ch-Ua-Mobile": "?0", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://rivestream.org/watch?type=tv&id=1418&season=1&episode=1", "Accept-Encoding": "gzip, deflate, br", "Priority": "u=1, i"}
    r = session.get(burp0_base_url, params=burp0_params)
    print(r.json())


if __name__ == "__main__":
    main()
