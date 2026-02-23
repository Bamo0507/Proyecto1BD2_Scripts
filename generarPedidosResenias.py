import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("MONGODB_DB")

COL_RESTAURANTES = "restaurantes"
COL_USUARIOS = "usuarios"
COL_PRODUCTOS = "productos"
COL_PEDIDOS = "pedidos"
COL_RESENIAS = "resenias"

NUM_PEDIDOS = 50000
NUM_RESENIAS = 10000
BATCH_SIZE = 5000

FECHA_INICIO = datetime(2025, 2, 1)
FECHA_FIN = datetime(2026, 3, 31)

ESTADOS = ["En cocina", "En camino", "Recibido"]

# Pesos para estados: la mayoría ya están recibidos
ESTADO_PESOS = [0.05, 0.10, 0.85]

# Plantillas para títulos de reseñas
TITULOS_POSITIVOS = [
    "Excelente experiencia",
    "Muy recomendado",
    "Delicioso todo",
    "Superó mis expectativas",
    "Volveré sin duda",
    "El mejor postre que he probado",
    "Increíble sabor",
    "Perfecto para compartir",
    "Calidad excepcional",
    "Mi lugar favorito",
]

TITULOS_NEUTRALES = [
    "Estuvo bien",
    "Cumple con lo esperado",
    "Normal, nada especial",
    "Aceptable",
    "Regular",
]

TITULOS_NEGATIVOS = [
    "No me gustó mucho",
    "Podría mejorar",
    "Esperaba más",
    "Decepcionante",
    "No lo recomiendo",
]

DESCRIPCIONES_POSITIVAS = [
    "Todo estuvo delicioso, el sabor es increíble y la presentación impecable.",
    "Me encantó la frescura de los ingredientes, se nota la calidad.",
    "El pedido llegó en perfectas condiciones y el sabor estaba espectacular.",
    "Siempre pido aquí y nunca me han fallado. La consistencia es admirable.",
    "Los postres tienen un sabor casero que me recuerda a la cocina de mi abuela.",
    "Excelente relación calidad-precio, porciones generosas y sabor único.",
    "La textura y el balance de sabores están perfectamente logrados.",
    "Pedí para una reunión familiar y todos quedaron encantados.",
    "Sin duda el mejor cheesecake que he probado en Guatemala.",
    "La atención fue muy buena y el producto llegó antes de lo esperado.",
]

DESCRIPCIONES_NEUTRALES = [
    "El producto estaba bien, pero no es nada fuera de lo común.",
    "Cumplió con lo que esperaba, ni más ni menos.",
    "Estuvo aceptable, aunque el empaque podría mejorar.",
    "El sabor es decente pero he probado mejores en otros lugares.",
    "Está bien para el precio, pero no repetiría necesariamente.",
]

DESCRIPCIONES_NEGATIVAS = [
    "El postre llegó un poco seco y no tenía el sabor que esperaba.",
    "La porción era muy pequeña para el precio que se paga.",
    "No me convenció el sabor, sentí que le faltaba dulce.",
    "El pedido tardó demasiado y cuando llegó ya estaba tibio.",
    "La presentación no se parecía en nada a la foto del producto.",
]


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Falta la variable de entorno {name}.")
    return v


def random_date(inicio: datetime, fin: datetime) -> datetime:
    delta = fin - inicio
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return inicio + timedelta(seconds=random_seconds)


def build_weighted_lists(usuarios, restaurantes, productos):
    """
    Crea listas con pesos/sesgo para que ciertos clientes, restaurantes
    y productos aparezcan más frecuentemente.
    """
    clientes = [u for u in usuarios if u["tipo_usuario"] == "cliente"]

    # Top 3 clientes más activos (piden 4x más que el resto)
    top_clientes = clientes[:3]
    resto_clientes = clientes[3:]
    clientes_pool = top_clientes * 4 + resto_clientes

    # Top 3 restaurantes más populares (aparecen 3x más)
    top_restaurantes = restaurantes[:3]
    resto_restaurantes = restaurantes[3:]
    restaurantes_pool = top_restaurantes * 3 + resto_restaurantes

    # Top 3 productos más vendidos (aparecen 5x más)
    top_productos = productos[:3]
    resto_productos = productos[3:]
    productos_pool = top_productos * 5 + resto_productos

    return clientes_pool, restaurantes_pool, productos_pool


def generar_pedidos(db, usuarios, restaurantes, productos):
    print(f"Generando {NUM_PEDIDOS} pedidos...")

    clientes_pool, restaurantes_pool, productos_pool = build_weighted_lists(
        usuarios, restaurantes, productos
    )

    pedidos_batch = []
    all_pedido_ids = []

    for i in range(NUM_PEDIDOS):
        cliente = random.choice(clientes_pool)
        restaurante = random.choice(restaurantes_pool)
        fecha = random_date(FECHA_INICIO, FECHA_FIN)
        estado = random.choices(ESTADOS, weights=ESTADO_PESOS, k=1)[0]

        # Entre 1 y 5 productos por pedido
        num_productos = random.randint(1, 5)
        productos_seleccionados = random.sample(
            productos, min(num_productos, len(productos))
        )

        # Sesgo: 40% de probabilidad de incluir un producto top
        if random.random() < 0.4 and productos_pool[:3]:
            producto_top = random.choice(productos_pool[:3])
            if producto_top not in productos_seleccionados:
                productos_seleccionados.append(producto_top)

        productos_pedido = []
        total = 0.0
        for prod in productos_seleccionados:
            cantidad = random.randint(1, 4)
            precio_unitario = prod["precio"]
            productos_pedido.append({
                "producto_id": prod["_id"],
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
            })
            total += cantidad * precio_unitario

        pedido = {
            "fecha_pedido": fecha,
            "id_usuario": cliente["_id"],
            "id_restaurante": restaurante["_id"],
            "productos": productos_pedido,
            "estado": estado,
            "total": round(total, 2),
        }
        pedidos_batch.append(pedido)

        # Insertar en lotes
        if len(pedidos_batch) >= BATCH_SIZE:
            result = db[COL_PEDIDOS].insert_many(pedidos_batch)
            all_pedido_ids.extend(result.inserted_ids)
            print(f"  Insertados {len(all_pedido_ids)} pedidos...")
            pedidos_batch = []

    # Insertar remanentes
    if pedidos_batch:
        result = db[COL_PEDIDOS].insert_many(pedidos_batch)
        all_pedido_ids.extend(result.inserted_ids)

    print(f"Total pedidos insertados: {len(all_pedido_ids)}")
    return all_pedido_ids


def generar_resenias(db, pedidos_collection, usuarios, restaurantes):
    print(f"Generando {NUM_RESENIAS} reseñas...")

    # Obtener pedidos con estado "Recibido" para que tenga sentido dejar reseña
    pedidos_recibidos = list(
        pedidos_collection.find(
            {"estado": "Recibido"},
            {"_id": 1, "id_usuario": 1, "id_restaurante": 1, "fecha_pedido": 1},
        )
    )

    if len(pedidos_recibidos) < NUM_RESENIAS:
        print(f"  Advertencia: solo hay {len(pedidos_recibidos)} pedidos recibidos, se generarán esa cantidad de reseñas.")

    pedidos_a_reseniar = random.sample(
        pedidos_recibidos, min(NUM_RESENIAS, len(pedidos_recibidos))
    )

    resenias_batch = []
    count = 0

    for pedido in pedidos_a_reseniar:
        # Distribución sesgada de puntuación: mayoría positivas
        # 50% -> 5, 25% -> 4, 10% -> 3, 10% -> 2, 5% -> 1
        puntuacion = random.choices([5, 4, 3, 2, 1], weights=[50, 25, 10, 10, 5], k=1)[0]

        if puntuacion >= 4:
            titulo = random.choice(TITULOS_POSITIVOS)
            descripcion = random.choice(DESCRIPCIONES_POSITIVAS)
        elif puntuacion == 3:
            titulo = random.choice(TITULOS_NEUTRALES)
            descripcion = random.choice(DESCRIPCIONES_NEUTRALES)
        else:
            titulo = random.choice(TITULOS_NEGATIVOS)
            descripcion = random.choice(DESCRIPCIONES_NEGATIVAS)

        # Fecha de reseña: entre 1 y 30 días después del pedido
        fecha_pedido = pedido["fecha_pedido"]
        dias_despues = random.randint(1, 30)
        fecha_resenia = fecha_pedido + timedelta(days=dias_despues)

        # No pasar de la fecha fin
        if fecha_resenia > FECHA_FIN:
            fecha_resenia = FECHA_FIN

        resenia = {
            "titulo": titulo,
            "id_usuario": pedido["id_usuario"],
            "id_restaurante": pedido["id_restaurante"],
            "id_pedido": pedido["_id"],
            "descripcion": descripcion,
            "puntuacion": puntuacion,
            "fecha": fecha_resenia,
        }
        resenias_batch.append(resenia)
        count += 1

        # Insertar en lotes
        if len(resenias_batch) >= BATCH_SIZE:
            db[COL_RESENIAS].insert_many(resenias_batch)
            print(f"  Insertadas {count} reseñas...")
            resenias_batch = []

    # Insertar remanentes
    if resenias_batch:
        db[COL_RESENIAS].insert_many(resenias_batch)

    print(f"Total reseñas insertadas: {count}")


def main():
    uri = require_env("MONGODB_URI")
    client = MongoClient(uri)
    db = client[DB_NAME]

    # Leer datos existentes
    usuarios = list(db[COL_USUARIOS].find())
    restaurantes = list(db[COL_RESTAURANTES].find())
    productos = list(db[COL_PRODUCTOS].find())

    if not usuarios or not restaurantes or not productos:
        print("Error: Primero ejecuta seed_base.py para insertar restaurantes, usuarios y productos.")
        client.close()
        return

    print(f"Datos encontrados: {len(usuarios)} usuarios, {len(restaurantes)} restaurantes, {len(productos)} productos")

    # Generar pedidos
    generar_pedidos(db, usuarios, restaurantes, productos)

    # Generar reseñas (basadas en pedidos recibidos)
    generar_resenias(db, db[COL_PEDIDOS], usuarios, restaurantes)

    client.close()
    print("Pedidos y Reseñas completos")


main()