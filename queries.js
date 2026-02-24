// Índices para consultas
// Simples
db.usuarios.createIndex({ nombre_usuario: 1 });
db.productos.createIndex({ esActivo: 1 });
db.productos.createIndex({ nombre: 1 });
db.restaurantes.createIndex({ nombre_restaurante: 1 });

// Compuestos
db.resenias.createIndex({ puntuacion: 1, fecha: 1 });
db.resenias.createIndex({ id_usuario: 1, fecha: 1 });
db.pedidos.createIndex({ fecha_pedido: 1, estado: 1 });
db.pedidos.createIndex({ id_usuario: 1, fecha_pedido: 1 });

// Texto
db.resenias.createIndex({ titulo: "text", descripcion: "text" });

// Multikey
db.productos.createIndex({ ingredientes: 1 });

// LOGIN
// POST /auth/login - getUser
db.usuarios.find(
  { nombre_usuario: "cliente_maria" },
  { nombre_usuario: 1, contrasenia: 1, tipo_usuario: 1 }
).explain("executionStats");


// ADMIN - Reseñas
// GET /admin/resenias - getReviewsAdmin
db.resenias.find(
  {
    puntuacion: 5,
    fecha: {
      $gte: ISODate("2025-06-01T00:00:00Z"),
      $lte: ISODate("2025-12-31T23:59:59Z")
    }
  },
  {
    titulo: 1,
    descripcion: 1,
    puntuacion: 1,
    fecha: 1
  }
).sort({ fecha: -1 }).skip(0).limit(10).explain("executionStats");

// GET /admin/resenias/buscar?q= - getReviewsAdminBySearch
db.resenias.find(
  { $text: { $search: "chocolate delicioso" } },
  {
    titulo: 1,
    descripcion: 1,
    puntuacion: 1,
    fecha: 1,
    score: { $meta: "textScore" }
  }
).sort({ score: { $meta: "textScore" } }).skip(0).limit(10).explain("executionStats");

// GET /admin/resenias/:id - getReviewsAdminById
db.resenias.aggregate([
  { $match: { _id: ObjectId("699c9778b10742d08167ad35") } },
  { $lookup: { from: "usuarios", localField: "id_usuario", foreignField: "_id", as: "usuario" } },
  { $unwind: "$usuario" },
  { $lookup: { from: "restaurantes", localField: "id_restaurante", foreignField: "_id", as: "restaurante" } },
  { $unwind: "$restaurante" },
  { $lookup: { from: "pedidos", localField: "id_pedido", foreignField: "_id", as: "pedido" } },
  { $unwind: "$pedido" },
  { $unwind: "$pedido.productos" },
  { $lookup: { from: "productos", localField: "pedido.productos.producto_id", foreignField: "_id", as: "producto_info" } },
  { $unwind: "$producto_info" },
  {
    $group: {
      _id: "$_id",
      titulo: { $first: "$titulo" },
      descripcion: { $first: "$descripcion" },
      puntuacion: { $first: "$puntuacion" },
      fecha: { $first: "$fecha" },
      nombre_usuario: { $first: "$usuario.nombre_usuario" },
      nombre_restaurante: { $first: "$restaurante.nombre_restaurante" },
      total: { $first: "$pedido.total" },
      productos: {
        $push: {
          nombre: "$producto_info.nombre",
          cantidad: "$pedido.productos.cantidad",
          precio_unitario: "$pedido.productos.precio_unitario"
        }
      }
    }
  }
]).explain("executionStats");


// ADMIN - Pedidos
// GET /admin/pedidos - getOrders
db.pedidos.aggregate([
  {
    $match: {
      fecha_pedido: {
        $gte: ISODate("2025-06-01T00:00:00Z"),
        $lte: ISODate("2025-12-31T23:59:59Z")
      }
    }
  },
  {
    $lookup: {
      from: "usuarios",
      localField: "id_usuario",
      foreignField: "_id",
      as: "usuario"
    }
  },
  { $unwind: "$usuario" },
  {
    $lookup: {
      from: "restaurantes",
      localField: "id_restaurante",
      foreignField: "_id",
      as: "restaurante"
    }
  },
  { $unwind: "$restaurante" },
  {
    $project: {
      fecha_pedido: 1,
      "usuario.nombre_usuario": 1,
      "restaurante.nombre_restaurante": 1,
      total: 1,
      estado: 1
    }
  },
  { $sort: { fecha_pedido: -1 } },
  { $skip: 0 },
  { $limit: 10 }
]).explain("executionStats");

// GET /shared/pedidos/:id - getOrdersById
db.pedidos.aggregate([
  { $match: { _id: ObjectId("699c973fb10742d08166e9e5") } },
  { $lookup: { from: "usuarios", localField: "id_usuario", foreignField: "_id", as: "usuario" } },
  { $unwind: "$usuario" },
  { $lookup: { from: "restaurantes", localField: "id_restaurante", foreignField: "_id", as: "restaurante" } },
  { $unwind: "$restaurante" },
  { $unwind: "$productos" },
  { $lookup: { from: "productos", localField: "productos.producto_id", foreignField: "_id", as: "producto_info" } },
  { $unwind: "$producto_info" },
  {
    $group: {
      _id: "$_id",
      fecha_pedido: { $first: "$fecha_pedido" },
      nombre_usuario: { $first: "$usuario.nombre_usuario" },
      nombre_restaurante: { $first: "$restaurante.nombre_restaurante" },
      total: { $first: "$total" },
      estado: { $first: "$estado" },
      productos: {
        $push: {
          nombre: "$producto_info.nombre",
          cantidad: "$productos.cantidad",
          precio_unitario: "$productos.precio_unitario"
        }
      }
    }
  }
]).explain("executionStats");

// PUT /admin/pedidos/:id/estado - updateOrderStatus
db.pedidos.updateOne(
  { _id: ObjectId("699c973fb10742d08166e9e5") },
  { $set: { estado: "En camino" } }
);

// ADMIN - Productos
// GET /admin/productos - getProductsAdmin
db.productos.find(
  {},
  {
    nombre: 1,
    imagen: 1,
    precio: 1
  }
).sort({ nombre: 1 }).explain("executionStats");

// GET /admin/productos/:id - getProductsAdminById
db.productos.find(
  { _id: ObjectId("699c957051574deec4cefaaf") },
  {
    nombre: 1,
    descripcion: 1,
    tiempo_preparacion: 1,
    ingredientes: 1,
    imagen: 1,
    precio: 1,
    esActivo: 1
  }
).explain("executionStats");

// POST /admin/productos - createProduct
db.productos.insertOne({
  nombre: "Pastel Blando",
  descripcion: "Pastel Simple solo para prueba.",
  tiempo_preparacion: 30,
  ingredientes: ["harina", "azúcar", "huevos"],
  imagen: null,
  esActivo: true,
  precio: 120.00
});

// GET /admin/productos/ingredientes - getIngredients
db.productos.aggregate([
  { $match: { ingredientes: { $exists: true } } },
  { $unwind: "$ingredientes" },
  {
    $group: {
      _id: null,
      ingredientes_unicos: { $addToSet: "$ingredientes" }
    }
  },
  {
    $project: {
      _id: 0,
      ingredientes_unicos: 1
    }
  }
]).explain("executionStats");

// PUT /admin/productos/:id - updateProduct
db.productos.updateOne(
  { _id: ObjectId("699ca1c9640b67d76be5b67f") },
  {
    $set: {
      nombre: "Pastel Blando Actualizado",
      descripcion: "pastel blando pt2",
      tiempo_preparacion: 35,
      precio: 130.00
    }
  }
);

// PUT /admin/productos/estado - updateProductsState
db.productos.updateMany(
  {
    _id: {
      $in: [
        ObjectId("699ca1c9640b67d76be5b67f"),
        ObjectId("699c957051574deec4cefab8"),
      ]
    }
  },
  { $set: { esActivo: false } }
);


// ADMIN - Restaurantes
// GET /admin/restaurantes - getRestaurantsAdmin
db.restaurantes.find(
  {},
  {
    nombre_restaurante: 1,
    ubicacion: 1,
    telefono: 1
  }
).sort({ nombre_restaurante: 1 }).explain("executionStats");

// GET /admin/restaurantes/:id/horario - getRestaurantSchedule
db.restaurantes.find(
  { _id: ObjectId("699c956551574deec4cefa7b") },
  {
    nombre_restaurante: 1,
    horarios_de_atencion: 1
  }
).explain("executionStats");

// GET /admin/restaurantes/:id - getRestaurantById
db.restaurantes.find(
  { _id: ObjectId("699c956551574deec4cefa7b") }
).explain("executionStats");

// POST /admin/restaurantes - createRestaurant
db.restaurantes.insertOne({
  nombre_restaurante: "Dulce Tentación Nueva Sede",
  ubicacion: {
    codigo_postal: "01015",
    calle: "10 Calle",
    zona: "15",
    avenida: "2a Avenida"
  },
  telefono: ["2345-6789"],
  horarios_de_atencion: {
    entre_semana: "8:00 - 20:00",
    fines_de_semana: "9:00 - 21:00",
    asueto: "10:00 - 17:00"
  },
  esActivo: true
});

// PUT /admin/restaurantes/:id - updateRestaurant
db.restaurantes.updateOne(
  { _id: ObjectId("699ca2b8640b67d76be5b680") },
  {
    $set: {
      nombre_restaurante: "Dulce Tentación Zona 15 Actualizado",
      "ubicacion.calle": "11 Calle",
      "ubicacion.zona": "15",
      "horarios_de_atencion.entre_semana": "7:30 - 21:30"
    }
  }
);

