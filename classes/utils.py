import re
import requests
import unicodedata
import os

from models.models import SearchResult, db
from flask import g
from typing import List
from dotenv import load_dotenv
from config.config import Config

load_dotenv()

def is_numeric(id: str) -> bool:
    pattern = r"^-?\d+(\.\d+)?$" 
    if re.fullmatch(pattern, id):
        return True
    return False
    

def get_linkedin_members(identifiers: List[int]) -> List[SearchResult] | None:
    members = []
    try:
        for identifier in identifiers:
            members.append(
                SearchResult.query.filter_by(id=identifier).first() 
            )
    except Exception as e:
        print(e)
        return None
    return members


def normalize_text(text):
    """
    Normaliza un texto eliminando tildes, signos diacríticos, y convierte a minúsculas.
    """
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c)).lower()


def get_coordinates_from_location(location_name: str):
    url = Config.OPEN_CAGE_BASE_URL
    params = {
        "q": location_name,
        "key": os.getenv("OPEN_CAGE_API_KEY"),
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # lanza excepción si status != 200

        data = response.json()
        first_result = data.get("results", [])[0]

        lat = first_result["geometry"]["lat"]
        lng = first_result["geometry"]["lng"]

        return {
            "error": False,
            "coordinates": {"lat": lat, "lng": lng},
            "status": response.status_code
        }

    except (requests.RequestException, IndexError, KeyError) as e:
        print(f"Error al obtener coordenadas: {e}")
        return {
            "error": True,
            "coordinates": {"lat": 0, "lng": 0},
            "status": 400
        }