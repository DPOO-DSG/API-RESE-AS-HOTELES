// RF1 — Crear reseña
db.reseñas.insertOne({
  // refs.
  hotelID:Number(P1_HOTEL_ID),
  usuarioID:Number(P1_USUARIO_ID),
  reservaID:Number(P1_RESERVA_ID),

  // Datos usuario
  calificacion: Number(P1_CALIFICACION),
  texto:P1_TEXTO,
  // 

  fecha_creacion:  new Date(),
  estado:          "publicada",
  destacada:       false,
  respuesta_admin: null,
  votos_utiles:    [],
  total_votos:     0
})
// RF2 — Editar reseña
db.reseñas.updateOne(
  { _id: ObjectId(id), usuarioID: usuarioID },
  { $set: { calificacion, texto } })

// RF3/RF8 — Eliminar reseña 
db.reseñas.updateOne(
  { _id: ObjectId(id) },
  { $set: { estado: "eliminada" } })
  
// RF4 — Consultar reseñas de un hotel (paginada)
db.reseñas.find({ hotelID, estado: "publicada" })
  .sort({ destacada: -1, fecha_creacion: -1 })
  .skip(pagina * 10).limit(10)

// RF5 — Marcar como útil
db.reseñas.updateOne(
  { _id: ObjectId(id) },
  { $addToSet: { votos_utiles: usuarioID },
    $inc: { total_votos: 1 } })

// RF6 — Historial propio
db.reseñas.find({ usuarioID, })
  .sort({ fecha_creacion: -1 })

  // RF7 — Responder reseña (admin agrega o edita respuesta)
db.reseñas.updateOne(
  { _id: ObjectId(id) },
  { $set: { 
      respuesta_admin: {
        usuarioID_admin:  usuarioID,
        texto_respuesta:  texto,
        fecha_respuesta:  new Date()
      }
  }}
)

// RF8 — Eliminar reseña (admin)  igual a RF3 pero sin verificar que el usuarioID coincida porq es del admin
db.reseñas.updateOne(
  { _id: ObjectId(id) },
  { $set: { estado: "eliminada" } }
)

// RF9 — Destacar reseña
// quita la destacada actual del hotel (si existe)
db.reseñas.updateOne(
  { hotelID: hotelID, destacada: true },
  { $set: { destacada: false } }
)
// marcar nueva como destacada
db.reseñas.updateOne(
  { _id: ObjectId(id) },
  { $set: { destacada: true } }
)

