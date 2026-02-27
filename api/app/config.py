import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://localhost/raspberry")

# Extraer nombre de DB del URI (último segmento del path antes de '?')
_db_from_uri = MONGO_URI.split("?")[0].rsplit("/", 1)[-1]
MONGO_DB = _db_from_uri if _db_from_uri else "raspberry"

API_KEY = os.getenv("API_KEY", "mi-api-key-secreta-cambiar-en-produccion")
