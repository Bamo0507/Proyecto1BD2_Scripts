import os
import gridfs
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("MONGODB_DB")

RESTAURANTES_CSV = "restaurantes.csv"
USUARIOS_CSV = "usuarios.csv"
PRODUCTOS_CSV = "productos.csv"
IMAGES_DIR = "images"

COL_RESTAURANTES = "restaurantes"
COL_USUARIOS = "usuarios"
COL_PRODUCTOS = "productos"

# Mapeo nombre del producto -> nombre del archivo de imagen
IMAGEN_MAP = {
    "Pastel de Chocolate": "pastel_de_chocolate.jpg",
    "Cheesecake de Fresas": "cheesecake_de_fresa.jpg",
    "Tres Leches Tradicional": "tres_leches.jpg",
    "Pie de Limón": "pie_de_limon.jpg",
    "Tiramisú": "tiramisu.jpg",
    "Rollos de Canela": "rollos_de_canela.jpg",
    "Brownies con Nuez": "brownies_con_nuez.jpg",
    "Alfajores de Maicena": "alfajores_de_maicena.jpg",
    "Tarta de Manzana": "tarta_de_manzana.jpg",
    "Éclairs de Vainilla": "eclairs_de_vainilla.jpg",
}


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Falta la variable de entorno {name}.")
    return v


def upload_image(fs: gridfs.GridFS, product_name: str) -> object:
    filename = IMAGEN_MAP.get(product_name)
    if not filename:
        print(f"  No se encontró mapeo de imagen para: {product_name}")
        return None

    filepath = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  Archivo no encontrado: {filepath}")
        return None

    with open(filepath, "rb") as f:
        file_id = fs.put(f, filename=filename, content_type="image/jpeg")
        print(f"  Imagen subida a GridFS: {filename} -> {file_id}")
        return file_id


def parse_restaurantes(df: pd.DataFrame) -> list:
    records = []
    for _, row in df.iterrows():
        record = {
            "nombre_restaurante": row["nombre_restaurante"],
            "ubicacion": {
                "codigo_postal": row["codigo_postal"],
                "calle": row["calle"],
                "zona": row["zona"],
                "avenida": row["avenida"],
            },
            "telefono": row["telefonos"].split("|"),
            "horarios_de_atencion": {
                "entre_semana": row["horario_entre_semana"],
                "fines_de_semana": row["horario_fines_de_semana"],
                "asueto": row["horario_asueto"],
            },
        }
        records.append(record)
    return records


def parse_usuarios(df: pd.DataFrame) -> list:
    records = []
    for _, row in df.iterrows():
        record = {
            "nombre_usuario": row["nombre_usuario"],
            "contrasenia": row["contrasenia"],
            "tipo_usuario": row["tipo_usuario"],
            "direccion": row["direccion"],
        }
        records.append(record)
    return records


def parse_productos(df: pd.DataFrame, fs: gridfs.GridFS) -> list:
    records = []
    for _, row in df.iterrows():
        nombre = row["nombre"]
        print(f"Procesando producto: {nombre}")
        file_id = upload_image(fs, nombre)

        record = {
            "nombre": nombre,
            "descripcion": row["descripcion"],
            "tiempo_preparacion": int(row["tiempo_preparacion"]),
            "ingredientes": row["ingredientes"].split("|"),
            "imagen": file_id,
            "esActivo": row["esActivo"] == True or row["esActivo"] == "true",
            "precio": float(row["precio"]),
        }
        records.append(record)
    return records


def main():
    uri = require_env("MONGODB_URI")
    client = MongoClient(uri)
    db = client[DB_NAME]
    fs = gridfs.GridFS(db)

    # Leer CSVs
    df_rest = pd.read_csv(RESTAURANTES_CSV)
    df_users = pd.read_csv(USUARIOS_CSV)
    df_prod = pd.read_csv(PRODUCTOS_CSV)

    # Insertar restaurantes
    restaurantes_docs = parse_restaurantes(df_rest)
    rest_result = db[COL_RESTAURANTES].insert_many(restaurantes_docs)
    print(f"Restaurantes insertados: {len(rest_result.inserted_ids)}")

    # Insertar usuarios
    usuarios_docs = parse_usuarios(df_users)
    users_result = db[COL_USUARIOS].insert_many(usuarios_docs)
    print(f"Usuarios insertados: {len(users_result.inserted_ids)}")

    # Insertar productos (con imágenes en GridFS)
    productos_docs = parse_productos(df_prod, fs)
    prod_result = db[COL_PRODUCTOS].insert_many(productos_docs)
    print(f"Productos insertados: {len(prod_result.inserted_ids)}")

    client.close()
    print("Fin de carga")

main()