from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://ISIS2304I01202610:rCWDuzcLRkE6@157.253.236.88:8087/")
db = client["ISIS2304I01202610"]
resenas = db["resenas"]

def serializar(doc):
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({"estado": "API funcionando correctamente"})

@app.route("/resenas", methods=["GET"])
def get_todas_resenas():
    cursor = resenas.find({}, {"_id": 0})
    resultado = list(cursor)
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
    return jsonify(resultado)

@app.route("/resenas", methods=["POST"])
def rf1_crear_resena():
    data = request.get_json()
    print("DEBUG datos recibidos:", data)
    try:
        nuevo = {
            "hotelID": int(data["hotelID"]),
            "usuarioID": int(data["usuarioID"]),
            "reservaID": int(''.join(filter(str.isdigit, str(data["reservaID"]))) or 0),
            "calificacion": int(data["calificacion"]),
            "texto": str(data["texto"]),
            "fecha_creacion": datetime.now(),
            "estado": "publicada",
            "destacada": False,
            "respuesta_admin": None,
            "votos_utiles": [],
            "total_votos": 0
        }
        resultado = resenas.insert_one(nuevo)
        return jsonify({"mensaje": "Exito", "_id": str(resultado.inserted_id)}), 201
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Fallo validacion", "detalle": str(e)}), 400

@app.route("/resenas/<id>", methods=["PUT"])
def rf2_editar_resena(id):
    data = request.get_json()
    if "usuarioID" not in data:
        return jsonify({"error": "Falta el campo usuarioID"}), 400
    resultado = resenas.update_one(
        {"_id": ObjectId(id), "usuarioID": int(data["usuarioID"])},
        {"$set": {"calificacion": int(data["calificacion"]), "texto": data["texto"]}}
    )
    if resultado.matched_count == 0:
        return jsonify({"error": "Resena no encontrada o no eres el autor"}), 404
    return jsonify({"mensaje": "Resena actualizada"})

@app.route("/resenas/<id>", methods=["DELETE"])
def rf3_rf8_eliminar_resena(id):
    es_admin = request.args.get("admin") == "true"
    if es_admin:
        filtro = {"_id": ObjectId(id)}
    else:
        data = request.get_json()
        if not data or "usuarioID" not in data:
            return jsonify({"error": "Falta el campo usuarioID"}), 400
        filtro = {"_id": ObjectId(id), "usuarioID": int(data["usuarioID"])}
    resultado = resenas.update_one(filtro, {"$set": {"estado": "eliminada"}})
    if resultado.matched_count == 0:
        return jsonify({"error": "Resena no encontrada o no tienes permiso"}), 404
    return jsonify({"mensaje": "Resena eliminada"})

@app.route("/resenas/hotel/<int:hotel_id>", methods=["GET"])
def rf4_resenas_hotel(hotel_id):
    pagina = int(request.args.get("pagina", 0))
    cursor = (
        resenas
        .find({"hotelID": hotel_id, "estado": "publicada"}, {"_id": 0})
        .sort([("destacada", -1), ("fecha_creacion", -1)])
        .skip(pagina * 10)
        .limit(10)
    )
    resultado = list(cursor)
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
    return jsonify({"pagina": pagina, "total": len(resultado), "resenas": resultado})

@app.route("/resenas/<id>/util", methods=["POST"])
def rf5_marcar_util(id):
    data = request.get_json()
    if "usuarioID" not in data:
        return jsonify({"error": "Falta el campo usuarioID"}), 400
    resultado = resenas.update_one(
        {"_id": ObjectId(id)},
        {"$addToSet": {"votos_utiles": int(data["usuarioID"])}, "$inc": {"total_votos": 1}}
    )
    if resultado.matched_count == 0:
        return jsonify({"error": "Resena no encontrada"}), 404
    return jsonify({"mensaje": "Voto registrado"})

@app.route("/resenas/usuario/<usuario_id>", methods=["GET"])
def rf6_historial_usuario(usuario_id):
    cursor = (
        resenas
        .find({"usuarioID": str(usuario_id)}, {"_id": 0})
        .sort("fecha_creacion", -1)
    )
    resultado = list(cursor)
    for r in resultado:
        if "fecha_creacion" in r:
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
    return jsonify({"usuarioID": usuario_id, "total": len(resultado), "resenas": resultado})

@app.route("/resenas/<id>/respuesta", methods=["POST"])
def rf7_responder_resena(id):
    data = request.get_json()
    for campo in ["usuarioID_admin", "texto_respuesta"]:
        if campo not in data:
            return jsonify({"error": f"Falta el campo: {campo}"}), 400
    resultado = resenas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"respuesta_admin": {
            "usuarioID_admin": int(data["usuarioID_admin"]),
            "texto_respuesta": data["texto_respuesta"],
            "fecha_respuesta": datetime.now()
        }}}
    )
    if resultado.matched_count == 0:
        return jsonify({"error": "Resena no encontrada"}), 404
    return jsonify({"mensaje": "Respuesta registrada"})

@app.route("/resenas/<id>/destacar", methods=["POST"])
def rf9_destacar_resena(id):
    data = request.get_json()
    if "hotelID" not in data:
        return jsonify({"error": "Falta el campo hotelID"}), 400
    hotel_id = int(data["hotelID"])
    resenas.update_one({"hotelID": hotel_id, "destacada": True}, {"$set": {"destacada": False}})
    resultado = resenas.update_one({"_id": ObjectId(id)}, {"$set": {"destacada": True}})
    if resultado.matched_count == 0:
        return jsonify({"error": "Resena no encontrada"}), 404
    return jsonify({"mensaje": "Resena destacada exitosamente"})

@app.route("/reportes/top-hoteles", methods=["GET"])
def rfc1_top_hoteles():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Se requieren fecha_inicio y fecha_fin (YYYY-MM-DD)"}), 400
    pipeline = [
        {"$match": {"estado": "publicada", "fecha_creacion": {"$gte": datetime.fromisoformat(fecha_inicio), "$lte": datetime.fromisoformat(fecha_fin)}}},
        {"$group": {"_id": "$hotelID", "calificacion_promedio": {"$avg": "$calificacion"}, "total_resenas": {"$sum": 1}}},
        {"$addFields": {"calificacion_promedio": {"$round": ["$calificacion_promedio", 2]}}},
        {"$sort": {"calificacion_promedio": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "hotelID": "$_id", "calificacion_promedio": 1, "total_resenas": 1}}
    ]
    return jsonify(list(resenas.aggregate(pipeline)))

@app.route("/reportes/evolucion/<int:hotel_id>", methods=["GET"])
def rfc2_evolucion_mensual(hotel_id):
    anio = request.args.get("anio")
    if not anio:
        return jsonify({"error": "Se requiere el parametro anio"}), 400
    pipeline = [
        {"$match": {"hotelID": hotel_id, "estado": "publicada", "$expr": {"$eq": [{"$year": "$fecha_creacion"}, int(anio)]}}},
        {"$group": {"_id": {"mes": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_creacion"}}}, "calificacion_promedio": {"$avg": "$calificacion"}, "total_resenas": {"$sum": 1}}},
        {"$addFields": {"calificacion_promedio": {"$round": ["$calificacion_promedio", 2]}}},
        {"$sort": {"_id.mes": 1}},
        {"$project": {"_id": 0, "mes": "$_id.mes", "calificacion_promedio": 1, "total_resenas": 1}}
    ]
    return jsonify({"hotelID": hotel_id, "anio": anio, "meses": list(resenas.aggregate(pipeline))})

@app.route("/reportes/ciudad", methods=["GET"])
def rfc3_comparativa_ciudad():
    hoteles_param = request.args.get("hoteles")
    if not hoteles_param:
        return jsonify({"error": "Se requiere el parametro hoteles (ej: ?hoteles=1,2,3)"}), 400
    hotel_ids = [int(h) for h in hoteles_param.split(",")]
    pipeline = [
        {"$match": {"hotelID": {"$in": hotel_ids}, "estado": "publicada"}},
        {"$group": {"_id": "$hotelID", "calificacion_promedio": {"$avg": "$calificacion"}, "total_resenas": {"$sum": 1}, "con_respuesta": {"$sum": {"$cond": [{"$ne": ["$respuesta_admin", None]}, 1, 0]}}, "destacadas": {"$sum": {"$cond": ["$destacada", 1, 0]}}}},
        {"$addFields": {"calificacion_promedio": {"$round": ["$calificacion_promedio", 2]}, "porcentaje_con_respuesta": {"$round": [{"$multiply": [{"$divide": ["$con_respuesta", "$total_resenas"]}, 100]}, 1]}, "porcentaje_destacadas": {"$round": [{"$multiply": [{"$divide": ["$destacadas", "$total_resenas"]}, 100]}, 1]}}},
        {"$setWindowFields": {"sortBy": {"calificacion_promedio": -1}, "output": {"promedio_ciudad": {"$avg": "$calificacion_promedio", "window": {"documents": ["unbounded", "unbounded"]}}}}},
        {"$addFields": {"promedio_ciudad": {"$round": ["$promedio_ciudad", 2]}, "bajo_promedio_ciudad": {"$lt": ["$calificacion_promedio", "$promedio_ciudad"]}}},
        {"$sort": {"calificacion_promedio": -1}},
        {"$project": {"_id": 0, "hotelID": "$_id", "calificacion_promedio": 1, "total_resenas": 1, "porcentaje_con_respuesta": 1, "porcentaje_destacadas": 1, "promedio_ciudad": 1, "bajo_promedio_ciudad": 1}}
    ]
    return jsonify({"hoteles_consultados": hotel_ids, "resultados": list(resenas.aggregate(pipeline))})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
