
use("");


// RFC1: PARAMETROS 
const rfc1_fechaInicio = new Date(P1_FECHA_INICIO);
const rfc1_fechaFin = new Date(P1_FECHA_FIN);

const rfc1 = db.reseñas.aggregate([

  // Paso 1: filtrar solo reseñas publicadas en el período
  {
    $match: {
      estado: "publicada",
      fecha_creacion: {
        $gte: rfc1_fechaInicio,
        $lte: rfc1_fechaFin
      }
    }
  },

  // Paso 2: agrupar por hotel y calcular
  {$group:{
      _id: "$hotelID", calificacion_promedio: { $avg: "$calificacion" }, total_reseñas:{ $sum: 1 }
    }
  },
// Paso 3: redondear el promedio a 2 decimales
  {
    $addFields: {
      calificacion_promedio: {$round: ["$calificacion_promedio", 2]}
    }
  },
  // Paso 4: ordenar de mayor a menor calificación
  {$sort: { calificacion_promedio: -1 }},
  // Paso 5: tomar solo los 10 primeros
  {$limit: 10},
// Paso 6: dar formato limpio al resultado
  {
    $project: {
      _id: 0,
      hotelID:              "$_id",
      calificacion_promedio: 1,
      total_reseñas:        1
    }
  }
]);


// Parámetros — ajustar según la consulta
const hotel = Number(P2_HOTEL_ID); 
const año = Number(P2_AÑO); //REVISAR

const rfc2 = db.reseñas.aggregate([

  // Paso 1: filtrar por hotel, año y estado publicada
  {
    $match: {
      hotelID: hotel,
      estado:  "publicada",
      $expr: {$eq: [{ $year: "$fecha_creacion" }, año]}
    }},

  // Paso 2: agrupar por mes y calcular promedio
  {
    $group: {
      _id: {mes: { $dateToString: { format: "%Y-%m", date: "$fecha_creacion" } }},
      calificacion_promedio: { $avg: "$calificacion" },total_reseñas:{ $sum: 1 }
    }},

  // Paso 3: redondear el promedio
  {
    $addFields: {
      calificacion_promedio: {$round: ["$calificacion_promedio", 2]}
    }},
  // Paso 4: ordenar cronológicamente
  {$sort: { "_id.mes": 1 }},
  // Paso 5: dar formato limpio al resultado
  {
    $project: {
      _id: 0,
      mes:                   "$_id.mes",
      calificacion_promedio:  1,
      total_reseñas:         1
    }}]);




//REQ 3 

const rfc3_hotelIDs = [] // ajustar con IDs reales

const rfc3 = db.reseñas.aggregate([

  // Paso 1: filtrar solo reseñas publicadas de los hoteles de la ciudad
  {
    $match: {
      hotelID: { $in: rfc3_hotelIDs },
      estado:  "publicada"
    }
  },

  // Paso 2: agrupar por hotel y calcular todas las métricas
  {
    $group: {
      _id:"$hotelID",
      calificacion_promedio:{ $avg: "$calificacion" },
      total_reseñas:{ $sum: 1 },
      // Contar reseñas con respuesta del administrador
      con_respuesta: {
        $sum: {
          $cond: [{ $ne: ["$respuesta_admin", null] }, 1, 0]
        }
      },

      // Contar reseñas destacadas
      destacadas: {
        $sum: { $cond: ["$destacada", 1, 0]}
      }
    }
  },

  // Paso 3: calcular porcentajes y redondear promedio
  {
    $addFields: {
      calificacion_promedio: {$round: ["$calificacion_promedio", 2]},
      porcentaje_con_respuesta: {$round: [{ $multiply: [{ $divide: ["$con_respuesta", "$total_reseñas"] },100]},1]},
      porcentaje_destacadas: {$round: [{ $multiply: [{ $divide: ["$destacadas", "$total_reseñas"] },100]},1]}
    }
  },

  // Paso 4: calcular el promedio global de la ciudad
  // usando $setWindowFields para tenerlo disponible por fila
  {
    $setWindowFields: {
      sortBy: { calificacion_promedio: -1 },
      output: {
        promedio_ciudad: {
          $avg: "$calificacion_promedio",
          window: { documents: ["unbounded", "unbounded"] }
        }
      }
    }
  },

  // Paso 5: marcar hoteles por debajo del promedio de la ciudad
  {
    $addFields: {
      promedio_ciudad: { $round: ["$promedio_ciudad", 2] },
      bajo_promedio_ciudad: {
        $lt: ["$calificacion_promedio", "$promedio_ciudad"]
      }
    }
  },
  // Paso 6: ordenar
  {
    $sort: { calificacion_promedio: -1 }
  },

  // Paso 7: proj 
  {
    $project: {
      _id: 0,
      hotelID:                  "$_id",
      calificacion_promedio:     1,
      total_reseñas:            1,
      porcentaje_con_respuesta:  1,
      porcentaje_destacadas:     1,
      promedio_ciudad:           1,
      bajo_promedio_ciudad:      1 }}]);
