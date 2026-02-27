from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URI, MONGO_DB

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    """Conectar a MongoDB al iniciar la app."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"Conectado a MongoDB: {MONGO_DB}")


async def close_mongo_connection():
    """Cerrar conexión a MongoDB."""
    global client
    if client:
        client.close()
        print("Conexión a MongoDB cerrada")


def get_database():
    """Obtener referencia a la base de datos."""
    return db
