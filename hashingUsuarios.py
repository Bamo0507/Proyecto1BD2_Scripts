import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("MONGODB_DB")

COL_USUARIOS = "usuarios"


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Falta la variable de entorno {name}.")
    return v


def main():
    uri = require_env("MONGODB_URI")
    client = MongoClient(uri)
    db = client[DB_NAME]

    usuarios = db[COL_USUARIOS].find()

    count = 0
    for usuario in usuarios:
        password_plano = usuario["contrasenia"]

        if password_plano.startswith("$2b$"):
            print(f"  {usuario['nombre_usuario']} ya está hasheada, se omite.")
            continue

        password_hash = bcrypt.hashpw(
            password_plano.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        db[COL_USUARIOS].update_one(
            {"_id": usuario["_id"]},
            {"$set": {"contrasenia": password_hash}}
        )

        print(f"  {usuario['nombre_usuario']}: {password_plano} -> hasheada")
        count += 1

    client.close()
    print(f"Contraseñas hasheadas: {count}")


main()