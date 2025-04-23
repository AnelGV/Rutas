from flask import Flask, request, render_template
from flask_cors import CORS
import math
from operator import itemgetter

app = Flask(__name__)
CORS(app)

# Coordenadas de las ciudades
coord = {
    'EDO.MEX': (19.29, -99.65),
    'QRO': (20.59, -100.39),
    'CDMX': (19.43, -99.13),
    'SLP': (22.15, -100.97),
    'MTY': (25.67, -100.29),
    'PUE': (19.06, -98.30),
    'GDL': (20.67, -103.34),
    'MICH': (19.70, -101.19),
    'SON': (29.07, -110.95)
}

def distancia(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2) * 111

def en_ruta(rutas, ciudad):
    """Verifica si una ciudad ya está en alguna ruta existente."""
    for ruta in rutas:
        if ciudad in ruta:
            return ruta
    return None

def peso_ruta(ruta, pedidos):
    """Calcula el peso total de la carga en una ruta."""
    return sum(pedidos[ciudad] for ciudad in ruta)

def vrp_voraz(coord, pedidos, almacen, max_carga):
    s = {}
    for c1 in coord:
        for c2 in coord:
            if c1 != c2 and (c2, c1) not in s:
                d = distancia(coord[c1], coord[c2])
                s[c1, c2] = d
    s = sorted(s.items(), key=itemgetter(1))

    rutas = []
    for (c1, c2), _ in s:
        if c1 not in pedidos or c2 not in pedidos:
            continue
        rc1 = en_ruta(rutas, c1)
        rc2 = en_ruta(rutas, c2)
        if rc1 is None and rc2 is None:
            if pedidos[c1] + pedidos[c2] <= max_carga:
                rutas.append([c1, c2])
        elif rc1 and rc2 is None:
            if peso_ruta(rc1, pedidos) + pedidos[c2] <= max_carga:
                rc1.append(c2)
        elif rc1 is None and rc2:
            if peso_ruta(rc2, pedidos) + pedidos[c1] <= max_carga:
                rc2.insert(0, c1)
        elif rc1 != rc2:
            if peso_ruta(rc1, pedidos) + peso_ruta(rc2, pedidos) <= max_carga:
                rc1.extend(rc2)
                rutas.remove(rc2)
    return rutas

def resumen_ruta(ruta, coord, almacen, pedidos):
    """Genera un resumen para una ruta de entregas."""
    total_peso = sum(pedidos[ciudad] for ciudad in ruta)
    distancia_total = 0
    casetas = 0
    gasolina_total = 0
    tiempo_estimado = 0
    velocidad_promedio = 80  # km/h
    consumo_gasolina = 0.12  # Litros por km
    costo_caseta = 50  # Costo por caseta cruzada

    for i in range(len(ruta) - 1):
        c1, c2 = ruta[i], ruta[i + 1]
        distancia_total += distancia(coord[c1], coord[c2])

        # Suponemos que en cada tramo se pasa por una caseta.
        casetas += 1

    # Agregar distancia desde el almacén a la primera ciudad y de vuelta al almacén al final
    distancia_total += distancia(coord[almacen], coord[ruta[0]])  # Desde el almacén a la primera ciudad
    distancia_total += distancia(coord[ruta[-1]], coord[almacen])  # De la última ciudad al almacén

    # Calculamos el tiempo estimado (en horas) y la gasolina (en litros)
    tiempo_estimado = distancia_total / velocidad_promedio
    gasolina_total = distancia_total * consumo_gasolina

    # Cálculo de costo de casetas
    casetas = casetas * costo_caseta

    resumen = {
        "ruta": ruta,
        "distancia_total": distancia_total,
        "total_peso": total_peso,
        "gasolina_l": gasolina_total,
        "casetas": casetas,
        "tiempo_h": tiempo_estimado
    }
    return resumen

@app.route("/", methods=["GET", "POST"])
def index_general():
    ciudades = list(coord.keys())
    if request.method == "POST":
        almacen = request.form['almacen']
        origen = request.form['origen']
        
        # Verificar si la ciudad de origen y la ciudad de almacén son diferentes
        if almacen == origen:
            return render_template("index.html", ciudades=ciudades, error="La ciudad de origen y la ciudad de almacén no pueden ser la misma.")

        pedidos = {}
        for ciudad in request.form.getlist("ciudades"):
            clave = f"paquetes_{ciudad}"
            valor = request.form.get(clave, '0').strip()
            paquetes = int(valor) if valor.isdigit() else 0
            pedidos[ciudad] = paquetes

        max_carga = 40
        rutas = vrp_voraz(coord, pedidos, almacen, max_carga)
        resumenes = [resumen_ruta(r, coord, almacen, pedidos) for r in rutas]
        return render_template("ruta.html", resumenes=resumenes, rutas=rutas, coord=coord)

    return render_template("index.html", ciudades=ciudades)

if __name__ == '__main__':
    app.run(debug=True)
