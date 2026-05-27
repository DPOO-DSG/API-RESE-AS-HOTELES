import requests
import random
import time

API_URL = "https://api-resenas-hoteles.onrender.com/resenas"

HOTELES = [f"H{str(i).zfill(3)}" for i in range(1, 16)]       # H001 - H015
USUARIOS = [f"U{str(i).zfill(4)}" for i in range(1, 301)]     # U0001 - U0300
RESERVAS = [f"R{str(i).zfill(4)}" for i in range(1, 301)]     # R0001 - R0300

TEXTOS_BUENOS = [
    "Excelente hotel, el servicio fue impecable y las instalaciones muy limpias.",
    "Muy buena experiencia, el personal siempre atento y amable.",
    "Las habitaciones son amplias y cómodas, definitivamente volvería.",
    "Ubicación perfecta, fácil acceso a todo. Muy recomendado.",
    "El desayuno estaba delicioso y la atención fue de primera.",
    "Todo estuvo a la altura de las expectativas, muy satisfecho.",
    "Habitación limpia, cama cómoda y buen precio. No tengo quejas.",
    "El spa fue increíble, salí completamente relajado. Volveré pronto.",
]

TEXTOS_MEDIOS = [
    "El hotel está bien, aunque el ruido por las noches molestó un poco.",
    "Buena relación calidad-precio, aunque hay detalles por mejorar.",
    "Aceptable en general, el servicio fue un poco lento pero correcto.",
    "Las instalaciones son buenas aunque algo antiguas. Cumplen su función.",
    "La habitación era correcta pero el wifi fallaba constantemente.",
    "Experiencia normal, nada especial pero tampoco hubo problemas graves.",
]

TEXTOS_MALOS = [
    "El servicio fue muy lento y el personal poco amable. Decepcionante.",
    "La habitación no estaba limpia al llegar, tuvimos que esperar mucho.",
    "No volvería, la experiencia estuvo por debajo de lo esperado.",
    "Muchos problemas con la reserva y nadie se hizo responsable.",
    "El precio no justifica la calidad del servicio ofrecido.",
    "Pésima atención, la habitación tenía humedad y olor desagradable.",
]

def texto_para_calificacion(cal):
    if cal >= 4:
        return random.choice(TEXTOS_BUENOS)
    elif cal == 3:
        return random.choice(TEXTOS_MEDIOS)
    else:
        return random.choice(TEXTOS_MALOS)

def crear_resena(hotel_id, usuario_id, reserva_id, calificacion, texto):
    payload = {
        "hotelID": hotel_id,
        "usuarioID": usuario_id,
        "reservaID": reserva_id,
        "calificacion": calificacion,
        "texto": texto
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        return r.status_code == 201
    except Exception as e:
        print(f"  Error de conexion: {e}")
        return False

def main():
    total = 150
    exitosas = 0
    fallidas = 0

    print(f"Iniciando poblacion de {total} resenas...")
    print(f"API: {API_URL}\n")

    # Distribucion de calificaciones: 40% altas (4-5), 35% medias (3), 25% bajas (1-2)
    calificaciones_pool = (
        [5] * 30 + [4] * 30 +   # 40% buenas
        [3] * 52 +               # 35% medias
        [2] * 23 + [1] * 15      # 25% malas
    )
    random.shuffle(calificaciones_pool)

    usados = set()

    for i in range(total):
        hotel_id  = random.choice(HOTELES)
        usuario_id = random.choice(USUARIOS)
        reserva_id = random.choice(RESERVAS)

        # Evitar misma combinacion hotel+usuario repetida
        clave = (hotel_id, usuario_id)
        intentos = 0
        while clave in usados and intentos < 10:
            usuario_id = random.choice(USUARIOS)
            clave = (hotel_id, usuario_id)
            intentos += 1
        usados.add(clave)

        calificacion = calificaciones_pool[i % len(calificaciones_pool)]
        texto = texto_para_calificacion(calificacion)

        ok = crear_resena(hotel_id, usuario_id, reserva_id, calificacion, texto)

        if ok:
            exitosas += 1
            print(f"[{i+1:>3}/{total}] OK   | Hotel: {hotel_id} | Usuario: {usuario_id} | Cal: {calificacion}")
        else:
            fallidas += 1
            print(f"[{i+1:>3}/{total}] FAIL | Hotel: {hotel_id} | Usuario: {usuario_id} | Cal: {calificacion}")

        # Pausa pequeña para no saturar la API (Render tiene cold starts)
        time.sleep(0.3)

    print(f"\nListo! Exitosas: {exitosas} | Fallidas: {fallidas} | Total: {total}")

if __name__ == "__main__":
    main()
