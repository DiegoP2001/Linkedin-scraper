from dotenv import load_dotenv, find_dotenv
import random
import requests
import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '..', '.env'))

DOWNLOAD_TOKEN = os.getenv("WEBSHARE_DONWLOAD_TOKEN")
LIST_TOKEN = os.getenv("WEBSHARE_LIST_TOKEN")

def get_random_proxy () -> str:
    response = requests.get(
    f"https://proxy.webshare.io/api/v2/proxy/list/download/{DOWNLOAD_TOKEN}/ES/any/username/backbone/"
    )
    proxies = [ line for line in response.text.splitlines() if line.strip() ]
    return random.choice(proxies)

def get_random_proxy_by_city(city_name: str) -> str:
 
    response = requests.get(
        "https://proxy.webshare.io/api/v2/proxy/list/?mode=backbone&page=15&page_size=25&country_code__in=ES",
        headers={"Authorization": f"Token {LIST_TOKEN}"}
    )
    
    proxies_json = response.json()
    proxies_filtered = []

    for proxy in proxies_json["results"]:
        if proxy["city_name"]:
            if proxy["city_name"].lower() == city_name.lower():
                proxies_filtered.append(proxy)

    rnd_proxy = random.choice(proxies_filtered)
    proxy = f"p.webshare.io:{rnd_proxy['port']}:{rnd_proxy['username']}:{rnd_proxy['password']}"
    return proxy
