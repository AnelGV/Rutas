from flask import Flask, render_template
import math
from operator import itemgetter

app = Flask(__name__)

# --- Función para calcular distancia euclidiana aproximada en km ---
def distancia(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2) * 111

# --- Verifica si una ciudad ya está en una ruta ---
def en_ruta(rutas, c):
    for r in rutas:
        if c in r:
            return r
    return None

# --- Calcula el peso total de una ruta ---
def peso_ruta(ruta):
    return sum(pedidos[c] for c in ruta)

# --- Algoritmo voraz para el problema de ruteo ---
def vrp_voraz(coord, pedidos, almacen, max_carga):
    s = {}
    for c1 in coord:
        for c2 in coord:
            if c1 != c2 and (c2, c1) not in s:
                d_c1_c2 = distancia(coord[c1], coord[c2])
                d_c1_almacen = distancia(coord[c1], almacen)
                d_c2_almacen = distancia(coord[c2], almacen)
                s[c1, c2] = d_c1_almacen + d_c2_almacen - d_c1_c2

    s = sorted(s.items(), key=itemgetter(1), reverse=True)

    rutas = []
    for (c1, c2), _ in s:
        rc1 = en_ruta(rutas, c1)
        rc2 = en_ruta(rutas, c2)
        if rc1 is None and rc2 is None:
            if pedidos[c1] + pedidos[c2] <= max_carga:
                rutas.append([c1, c2])
        elif rc1 and rc2 is None:
            if rc1[0] == c1:
                if peso_ruta(rc1) + pedidos[c2] <= max_carga:
                    rc1.insert(0, c2)
            elif rc1[-1] == c1:
                if peso_ruta(rc1) + pedidos[c2] <= max_carga:
                    rc1.append(c2)
        elif rc1 is None and rc2:
            if rc2[0] == c2:
                if peso_ruta(rc2) + pedidos[c1] <= max_carga:
                    rc2.insert(0, c1)
            elif rc2[-1] == c2:
                if peso_ruta(rc2) + pedidos[c1] <= max_carga:
                    rc2.append(c1)
        elif rc1 != rc2:
            if rc1[0] == c1 and rc2[-1] == c2:
                if peso_ruta(rc1) + peso_ruta(rc2) <= max_carga:
                    rc2.extend(rc1)
                    rutas.remove(rc1)
            elif rc1[-1] == c1 and rc2[0] == c2:
                if peso_ruta(rc1) + peso_ruta(rc2) <= max_carga:
                    rc1.extend(rc2)
                    rutas.remove(rc2)
    return rutas

# --- Calcula el resumen de cada ruta (distancia, gasolina, etc.) ---
def resumen_ruta(ruta, coord, almacen):
    distancia_total = 0
    puntos = [almacen] + [coord[ciudad] for ciudad in ruta] + [almacen]
    for i in range(len(puntos) - 1):
        distancia_total += distancia(puntos[i], puntos[i + 1])

    tiempo_estimado = distancia_total / 80  # 80 km/h promedio
    gasolina = distancia_total / 10         # 10 km/l
    casetas = distancia_total * 0.3         # $0.30 por km

    return {
        "ruta": " → ".join(ruta),
        "distancia_km": round(distancia_total, 2),
        "gasolina_l": round(gasolina, 2),
        "casetas": round(casetas, 2),
        "tiempo_h": round(tiempo_estimado, 2),
        "paquetes": peso_ruta(ruta)
    }

# --- Ruta principal ---
@app.route("/")
def mostrar_rutas():
    coord = {
        'EDO.MEX': (19.2938258568844, -99.65366252023884),
        'QRO': (20.593537489366717, -100.39004057702225),
        'CDMX': (19.432854452264177, -99.13330004822943),
        'SLP': (22.151725492903953, -100.97657666103268),
        'MTY': (25.673156272083876, -100.2974200019319),
        'PUE': (19.063532268065185, -98.30729139446866),
        'GDL': (20.67714565083998, -103.34696388920293),
        'MICH': (19.702614895389996, -101.19228631929688),
        'SON': (29.075273188617818, -110.95962477655333)
    }

    global pedidos
    pedidos = {
        'EDO.MEX': 10,
        'QRO': 13,
        'CDMX': 7,
        'SLP': 11,
        'MTY': 15,
        'PUE': 8,
        'GDL': 6,
        'MICH': 7,
        'SON': 8
    }

    almacen = (19.432854452264177, -99.13330004822943)  # CDMX como almacén
    max_carga = 40

    rutas = vrp_voraz(coord, pedidos, almacen, max_carga)
    resumenes = [resumen_ruta(r, coord, almacen) for r in rutas]

    return render_template("ruta.html", resumenes=resumenes)
# --- Iniciar la aplicación ---
if __name__ == "__main__":
    app.run(debug=True)
