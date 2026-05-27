

use(); // #TODO 


db.createCollection("reseñas");

// Índices de la colección reseñas

// 1. (hotelID + fecha_creacion)RF4: consultar reseñas de un
//    hotel ordenadas por fecha. 

// 2. (usuarioID)  RF6: historial de reseñas propias
//
// 3. (reservaID) únicoRF1: garantiza que una reserva
//    completada solo pueda generar UNA reseña

// 4. (hotelID + calificacion)  RFC1 RFC2,RFC3: agregaciones
//    por hotel

// 5. (hotelID + destacada) → RF9: una sola reseña destacada
//    por hotel 
// -------------------------------------------------------------
db.reseñas.createIndex(
  { hotelID: 1, fecha_creacion: -1 },
  { name: "idx_hotel_fecha" }
);

db.reseñas.createIndex(
  { usuarioID: 1 },
  { name: "idx_usuario" }
);

db.reseñas.createIndex(
  { reservaID: 1 },
  { unique: true, name: "idx_reserva_unico" }
);

db.reseñas.createIndex(
  { hotelID: 1, calificacion: 1 },
  { name: "idx_hotel_calificacion" }
);

db.reseñas.createIndex(
  { hotelID: 1, destacada: 1 },
  { name: "idx_hotel_destacada" }
);

