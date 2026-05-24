from flask import Flask, jsonify, request
from flask_cors import CORS 
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
CORS(app)

# -------------------------------------------------------------
# Conexión a MongoDB
# -------------------------------------------------------------
client = MongoClient("mongodb://ISIS2304I01202610:rCWDuzcLRkE6@157.253.236.88:8087/")
db = client["ISIS2304I01202610"]
resenas = db["reseñas"]


# -------------------------------------------------------------
# Helper: convierte ObjectId a string para poder enviar JSON
# -------------------------------------------------------------
def serializar(doc):
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


# =============================================================
# RF1 — Crear reseña
# POST /resenas
#
# Body JSON esperado:
# {
#   "hotelID": 1,
#   "usuarioID": 2,
#   "reservaID": 3,
#   "calificacion": 5,
#   "texto": "Excelente hotel"
# }
# =============================================================
@app.route("/resenas", methods=["POST"])
def rf1_crear_resena():
    data = request.get_json()

    # Validación básica de campos obligatorios
    campos = ["hotelID", "usuarioID", "reservaID", "calificacion", "texto"]
    for campo in campos:
        if campo not in data:
            return jsonify({"error": f"Falta el campo: {campo}"}), 400

    nuevo = {
        "hotelID":        str(data["hotelID"]),   # <-- CAMBIADO A str()
        "usuarioID":      str(data["usuarioID"]), # <-- CAMBIADO A str()
        "reservaID":      str(data["reservaID"]), # <-- CAMBIADO A str()
        "calificacion":   str(data["calificacion"]),
        "texto":          data["texto"],
        "fecha_creacion": datetime.now(),         # PyMongo lo convierte a Date automático
        "estado":         "publicada",
        "destacada":      False,
        "respuesta_admin": None,
        "votos_utiles":   [],
        "total_votos":    0
    }

    try:
        resultado = resenas.insert_one(nuevo)
        return jsonify({
            "mensaje":  "Reseña creada exitosamente",
            "_id":      str(resultado.inserted_id)
        }), 201
    except Exception as e:
        print("Error en Mongo:", str(e))
        return jsonify({"error": "Falló la validación de MongoDB", "detalle": str(e)}), 400

@app.route("/resenas", methods=["GET"])
def get_todas_resenas():
    cursor = resenas.find({}, {"_id": 0})
    resultado = list(cursor)
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
    return jsonify(resultado)
    


# =============================================================
# RF2 — Editar reseña (solo el autor puede editar)
# PUT /resenas/<id>
#
# Body JSON esperado:
# {
#   "usuarioID": 2,
#   "calificacion": 4,
#   "texto": "Muy buen hotel"
# }
# =============================================================
@app.route("/resenas/<id>", methods=["PUT"])
def rf2_editar_resena(id):
    data = request.get_json()

    if "usuarioID" not in data:
        return jsonify({"error": "Falta el campo usuarioID"}), 400

    resultado = resenas.update_one(
        {
            "_id":       ObjectId(id),
            "usuarioID": int(data["usuarioID"])   # solo el autor
        },
        {
            "$set": {
                "calificacion": int(data["calificacion"]),
                "texto":        data["texto"]
            }
        }
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Reseña no encontrada o no eres el autor"}), 404

    return jsonify({"mensaje": "Reseña actualizada"})


# =============================================================
# RF3 — Eliminar reseña (el autor la marca como eliminada)
# RF8 — Eliminar reseña (admin, sin verificar usuarioID)
#
# DELETE /resenas/<id>              → usuario normal (RF3)
# DELETE /resenas/<id>?admin=true   → admin (RF8)
#
# Body JSON para RF3:
# { "usuarioID": 2 }
# =============================================================
@app.route("/resenas/<id>", methods=["DELETE"])
def rf3_rf8_eliminar_resena(id):
    es_admin = request.args.get("admin") == "true"

    if es_admin:
        # RF8 — admin no necesita verificar usuarioID
        filtro = {"_id": ObjectId(id)}
    else:
        # RF3 — usuario solo puede eliminar la suya
        data = request.get_json()
        if not data or "usuarioID" not in data:
            return jsonify({"error": "Falta el campo usuarioID"}), 400
        filtro = {
            "_id":       ObjectId(id),
            "usuarioID": int(data["usuarioID"])
        }

    resultado = resenas.update_one(
        filtro,
        {"$set": {"estado": "eliminada"}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Reseña no encontrada o no tienes permiso"}), 404

    return jsonify({"mensaje": "Reseña eliminada"})


# =============================================================
# RF4 — Consultar reseñas de un hotel (paginada)
# GET /resenas/hotel/<hotelID>?pagina=0
#
# Devuelve 10 reseñas por página.
# Las destacadas aparecen primero, luego las más recientes.
# =============================================================
@app.route("/resenas/hotel/<int:hotel_id>", methods=["GET"])
def rf4_resenas_hotel(hotel_id):
    pagina = int(request.args.get("pagina", 0))

    cursor = (
        resenas
        .find(
            {"hotelID": hotel_id, "estado": "publicada"},
            {"_id": 0}   # oculta el _id para simplificar el JSON
        )
        .sort([("destacada", -1), ("fecha_creacion", -1)])
        .skip(pagina * 10)
        .limit(10)
    )

    resultado = list(cursor)

    # Convierte fechas a string para que JSON las pueda serializar
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()

    return jsonify({
        "pagina":   pagina,
        "total":    len(resultado),
        "resenas":  resultado
    })


# =============================================================
# RF5 — Marcar reseña como útil
# POST /resenas/<id>/util
#
# Body JSON:
# { "usuarioID": 5 }
#
# Usa $addToSet para evitar votos duplicados del mismo usuario.
# =============================================================
@app.route("/resenas/<id>/util", methods=["POST"])
def rf5_marcar_util(id):
    data = request.get_json()

    if "usuarioID" not in data:
        return jsonify({"error": "Falta el campo usuarioID"}), 400

    usuario_id = int(data["usuarioID"])

    resultado = resenas.update_one(
        {"_id": ObjectId(id)},
        {
            "$addToSet": {"votos_utiles": usuario_id},  # evita duplicados
            "$inc":      {"total_votos": 1}              # suma 1 al contador
        }
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Reseña no encontrada"}), 404

    return jsonify({"mensaje": "Voto registrado"})


# =============================================================
# RF6 — Historial de reseñas propias
# GET /resenas/usuario/<usuarioID>
#
# Devuelve todas las reseñas del usuario, ordenadas por fecha.
# =============================================================
# =============================================================
# RF6 — Historial de reseñas propias
# =============================================================
@app.route("/resenas/usuario/<usuario_id>", methods=["GET"]) # <-- QUITAR EL int:
def rf6_historial_usuario(usuario_id):
    cursor = (
        resenas
        .find({"usuarioID": str(usuario_id)}, {"_id": 0}) # <-- BUSCAR COMO STRING
        .sort("fecha_creacion", -1)
    )

    resultado = list(cursor)
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()

    return jsonify({
        "usuarioID": usuario_id,
        "total":     len(resultado),
        "resenas":   resultado
    })


# =============================================================
# RF7 — Responder reseña (admin agrega o edita su respuesta)
# POST /resenas/<id>/respuesta
#
# Body JSON:
# {
#   "usuarioID_admin": 99,
#   "texto_respuesta": "Gracias por su comentario"
# }
# =============================================================
@app.route("/resenas/<id>/respuesta", methods=["POST"])
def rf7_responder_resena(id):
    data = request.get_json()

    campos = ["usuarioID_admin", "texto_respuesta"]
    for campo in campos:
        if campo not in data:
            return jsonify({"error": f"Falta el campo: {campo}"}), 400

    resultado = resenas.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "respuesta_admin": {
                    "usuarioID_admin":  int(data["usuarioID_admin"]),
                    "texto_respuesta":  data["texto_respuesta"],
                    "fecha_respuesta":  datetime.now()
                }
            }
        }
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Reseña no encontrada"}), 404

    return jsonify({"mensaje": "Respuesta registrada"})


# =============================================================
# RF9 — Destacar reseña (admin)
# POST /resenas/<id>/destacar
#
# Body JSON:
# { "hotelID": 1 }
#
# Primero quita la destacada actual del hotel,
# luego marca la nueva como destacada.
# =============================================================
@app.route("/resenas/<id>/destacar", methods=["POST"])
def rf9_destacar_resena(id):
    data = request.get_json()

    if "hotelID" not in data:
        return jsonify({"error": "Falta el campo hotelID"}), 400

    hotel_id = int(data["hotelID"])

    # Paso 1: quitar destacada actual del hotel
    resenas.update_one(
        {"hotelID": hotel_id, "destacada": True},
        {"$set": {"destacada": False}}
    )

    # Paso 2: marcar la nueva como destacada
    resultado = resenas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"destacada": True}}
    )

    if resultado.matched_count == 0:
        return jsonify({"error": "Reseña no encontrada"}), 404

    return jsonify({"mensaje": "Reseña destacada exitosamente"})


# =============================================================
# RFC1 — Top 10 hoteles mejor calificados en un período
# GET /reportes/top-hoteles?fecha_inicio=2024-01-01&fecha_fin=2024-12-31
# =============================================================
@app.route("/reportes/top-hoteles", methods=["GET"])
def rfc1_top_hoteles():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin    = request.args.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Se requieren fecha_inicio y fecha_fin (YYYY-MM-DD)"}), 400

    pipeline = [
        {
            "$match": {
                "estado": "publicada",
                "fecha_creacion": {
                    "$gte": datetime.fromisoformat(fecha_inicio),
                    "$lte": datetime.fromisoformat(fecha_fin)
                }
            }
        },
        {
            "$group": {
                "_id":                  "$hotelID",
                "calificacion_promedio": {"$avg": "$calificacion"},
                "total_resenas":         {"$sum": 1}
            }
        },
        {
            "$addFields": {
                "calificacion_promedio": {"$round": ["$calificacion_promedio", 2]}
            }
        },
        {"$sort": {"calificacion_promedio": -1}},
        {"$limit": 10},
        {
            "$project": {
                "_id":                   0,
                "hotelID":               "$_id",
                "calificacion_promedio":  1,
                "total_resenas":          1
            }
        }
    ]

    resultado = list(resenas.aggregate(pipeline))
    return jsonify(resultado)


# =============================================================
# RFC2 — Evolución mensual de calificaciones de un hotel
# GET /reportes/evolucion/<hotelID>?año=2024
# =============================================================
@app.route("/reportes/evolucion/<int:hotel_id>", methods=["GET"])
def rfc2_evolucion_mensual(hotel_id):
    año = request.args.get("año")

    if not año:
        return jsonify({"error": "Se requiere el parámetro año"}), 400

    pipeline = [
        {
            "$match": {
                "hotelID": hotel_id,
                "estado":  "publicada",
                "$expr":   {"$eq": [{"$year": "$fecha_creacion"}, int(año)]}
            }
        },
        {
            "$group": {
                "_id": {
                    "mes": {
                        "$dateToString": {
                            "format": "%Y-%m",
                            "date":   "$fecha_creacion"
                        }
                    }
                },
                "calificacion_promedio": {"$avg": "$calificacion"},
                "total_resenas":         {"$sum": 1}
            }
        },
        {
            "$addFields": {
                "calificacion_promedio": {"$round": ["$calificacion_promedio", 2]}
            }
        },
        {"$sort": {"_id.mes": 1}},
        {
            "$project": {
                "_id":                   0,
                "mes":                   "$_id.mes",
                "calificacion_promedio":  1,
                "total_resenas":          1
            }
        }
    ]

    resultado = list(resenas.aggregate(pipeline))
    return jsonify({
        "hotelID": hotel_id,
        "año":     año,
        "meses":   resultado
    })


# =============================================================
# RFC3 — Comparativa de hoteles de una ciudad
# GET /reportes/ciudad?hoteles=1,2,3,4
#
# Los IDs de los hoteles de la ciudad vienen desde Oracle APEX.
# =============================================================
@app.route("/reportes/ciudad", methods=["GET"])
def rfc3_comparativa_ciudad():
    hoteles_param = request.args.get("hoteles")

    if not hoteles_param:
        return jsonify({"error": "Se requiere el parámetro hoteles (ej: ?hoteles=1,2,3)"}), 400

    # Convierte "1,2,3" → [1, 2, 3]
    hotel_ids = [int(h) for h in hoteles_param.split(",")]

    pipeline = [
        {
            "$match": {
                "hotelID": {"$in": hotel_ids},
                "estado":  "publicada"
            }
        },
        {
            "$group": {
                "_id":                   "$hotelID",
                "calificacion_promedio":  {"$avg": "$calificacion"},
                "total_resenas":          {"$sum": 1},
                "con_respuesta": {
                    "$sum": {
                        "$cond": [{"$ne": ["$respuesta_admin", None]}, 1, 0]
                    }
                },
                "destacadas": {
                    "$sum": {"$cond": ["$destacada", 1, 0]}
                }
            }
        },
        {
            "$addFields": {
                "calificacion_promedio": {"$round": ["$calificacion_promedio", 2]},
                "porcentaje_con_respuesta": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$con_respuesta", "$total_resenas"]}, 100]},
                        1
                    ]
                },
                "porcentaje_destacadas": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$destacadas", "$total_resenas"]}, 100]},
                        1
                    ]
                }
            }
        },
        {
            "$setWindowFields": {
                "sortBy": {"calificacion_promedio": -1},
                "output": {
                    "promedio_ciudad": {
                        "$avg":   "$calificacion_promedio",
                        "window": {"documents": ["unbounded", "unbounded"]}
                    }
                }
            }
        },
        {
            "$addFields": {
                "promedio_ciudad":    {"$round": ["$promedio_ciudad", 2]},
                "bajo_promedio_ciudad": {"$lt": ["$calificacion_promedio", "$promedio_ciudad"]}
            }
        },
        {"$sort": {"calificacion_promedio": -1}},
        {
            "$project": {
                "_id":                      0,
                "hotelID":                  "$_id",
                "calificacion_promedio":     1,
                "total_resenas":             1,
                "porcentaje_con_respuesta":  1,
                "porcentaje_destacadas":     1,
                "promedio_ciudad":           1,
                "bajo_promedio_ciudad":      1
            }
        }
    ]

    resultado = list(resenas.aggregate(pipeline))
    return jsonify({
        "hoteles_consultados": hotel_ids,
        "resultados":          resultado
    })


# =============================================================
# Inicio del servidor
# =============================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
