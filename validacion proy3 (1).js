use("ISIS2304I01202610");

// -------------------------------------------------------------
// Validación de la colección: reseñas
//
// Campos obligatorios:
//   - hotelID    → referencia a Oracle tabla hoteles (PK: hotelID)
//   - usuarioID  → referencia a Oracle tabla usuarios (PK: usuarioID)
//   - reservaID  → referencia a Oracle tabla reserva (PK: reservaID)
//   - calificacion → entero entre 1 y 5
//   - texto      → string no vacío (mínimo 10 caracteres)
//   - fecha_creacion → fecha de creación de la reseña
//   - estado     → solo puede ser "publicada" o "eliminada"
//   - destacada  → booleano, false por defecto
//
// Campos opcionales embebidos:
//   - respuesta_admin → subdocumento con datos de la respuesta
//   - votos_utiles   → array de usuarioID que votaron
//   - total_votos    → entero >= 0
// -------------------------------------------------------------
db.runCommand({
  collMod: "reseñas",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Esquema de validación — colección reseñas",
      required: [
        "hotelID",
        "usuarioID",
        "reservaID",
        "calificacion",
        "texto",
        "fecha_creacion",
        "estado",
        "destacada"
      ],
      properties: {

        // --- Referencias a Oracle ---
        hotelID: {
          bsonType: "int",
          description: "PK del hotel en Oracle (tabla hoteles). Obligatorio."
        },
        usuarioID: {
          bsonType: "int",
          description: "PK del usuario/cliente en Oracle (tabla usuarios). Obligatorio."
        },
        reservaID: {
          bsonType: "int",
          description: "PK de la reserva en Oracle (tabla reserva). Obligatorio. Único por índice."
        },

        // --- Datos propios de la reseña ---
        calificacion: {
          bsonType: "int",
          minimum: 1,
          maximum: 5,
          description: "Calificación del 1 al 5. Obligatorio."
        },
        texto: {
          bsonType: "string",
          minLength: 4,
          description: "Texto de la reseña. Mínimo 4 caracteres. Obligatorio."
        },
        fecha_creacion: {
          bsonType: "date",
          description: "Fecha y hora de creación de la reseña. Obligatorio."
        },
        estado: {
          bsonType: "string",
          enum: ["publicada", "eliminada"],
          description: "Estado de la reseña. Solo 'publicada' o 'eliminada'. Obligatorio."
        },
        destacada: {
          bsonType: "bool",
          description: "Indica si la reseña está destacada por el admin. Obligatorio."
        },

        // --- Subdocumento embebido: respuesta del administrador ---
        // Opcional: null si el admin no ha respondido aún
        respuesta_admin: {
          bsonType: ["object", "null"],
          description: "Respuesta oficial del administrador. Opcional (null si no existe).",
          required: ["usuarioID_admin", "texto_respuesta", "fecha_respuesta"],
          properties: {
            usuarioID_admin: {
              bsonType: "int",
              description: "ID del administrador que respondió (ref Oracle usuarios)."
            },
            texto_respuesta: {
              bsonType: "string",
              minLength: 5,
              description: "Texto de la respuesta del administrador."
            },
            fecha_respuesta: {
              bsonType: "date",
              description: "Fecha y hora en que se publicó la respuesta."
            }
          }
        },

        // --- Array embebido: votos de utilidad ---
        // Array de usuarioID que marcaron la reseña como útil
        votos_utiles: {
          bsonType: "array",
          description: "Array de usuarioID que votaron la reseña como útil.",
          items: {
            bsonType: "int",
            description: "usuarioID del votante (ref Oracle usuarios)."
          }
        },

        // --- Total de votos (derivado, se mantiene sincronizado) ---
        total_votos: {
          bsonType: "int",
          minimum: 0,
          description: "Cantidad total de votos útiles. Debe ser >= 0."
        }
      },

      // No se permiten campos adicionales no declarados
      additionalProperties: true
    }
  },

  // Cambiar a "error" en producción para rechazar documentos inválidos.
  validationLevel: "strict",
  validationAction: "error"
});

print("✔ Validación de 'reseñas' aplicada.");
print("✔ Script 02 completado exitosamente.");
