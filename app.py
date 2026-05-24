from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
# Configuración explícita de CORS para permitir peticiones desde cualquier origen
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------------------------------------------
# Conexión a MongoDB
# -------------------------------------------------------------
client = MongoClient("mongodb://ISIS2304I01202610:rCWDuzcLRkE6@157.253.236.88:8087/")
db = client["ISIS2304I01202610"]
resenas = db["reseñas"]

# =============================================================
# RF1 — Crear reseña
# =============================================================
@app.route("/resenas", methods=["POST"])
def rf1_crear_resena():
    data = request.get_json()
    campos = ["hotelID", "usuarioID", "reservaID", "calificacion", "texto"]
    
    if not all(c in data for c in campos):
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    nuevo = {
        "hotelID": str(data["hotelID"]),
        "usuarioID": str(data["usuarioID"]),
        "reservaID": str(data["reservaID"]),
        "calificacion": int(data["calificacion"]),
        "texto": data["texto"],
        "fecha_creacion": datetime.now(),
        "estado": "publicada",
        "destacada": False,
        "respuesta_admin": None,
        "votos_utiles": [],
        "total_votos": 0
    }

    try:
        resultado = resenas.insert_one(nuevo)
        return jsonify({"mensaje": "Reseña creada", "_id": str(resultado.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": "Error al guardar", "detalle": str(e)}), 500

# =============================================================
# GET Todas (Corregido para manejar fechas sin error)
# =============================================================
@app.route("/resenas", methods=["GET"])
def get_todas_resenas():
    resultado = list(resenas.find({}))
    for r in resultado:
        r["_id"] = str(r["_id"])
        if "fecha_creacion" in r and isinstance(r["fecha_creacion"], datetime):
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
    return jsonify(resultado)

# =============================================================
# RF6 — Historial de reseñas propias (Corregido)
# =============================================================
@app.route("/resenas/usuario/<usuario_id>", methods=["GET"])
def rf6_historial_usuario(usuario_id):
    # Aseguramos que el usuario_id se trate como string
    cursor = resenas.find({"usuarioID": str(usuario_id)}).sort("fecha_creacion", -1)
    
    resultado = list(cursor)
    for r in resultado:
        r["_id"] = str(r["_id"])
        if "fecha_creacion" in r and isinstance(r["fecha_creacion"], datetime):
            r["fecha_creacion"] = r["fecha_creacion"].isoformat()
            
    return jsonify({
        "usuarioID": usuario_id,
        "total": len(resultado),
        "resenas": resultado
    })

# ... (El resto de tus rutas RF2 a RFC3 se mantienen iguales, 
#      solo asegúrate de que usen str(data["usuarioID"]) si aplica)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
