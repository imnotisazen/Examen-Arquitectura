import os
import datetime
import decimal
from contextlib import contextmanager

import pymssql
from flask import Flask, jsonify, request

app = Flask(__name__)
ESTADOS = {"Pendiente", "Pagada", "Anulada"}


class ApiError(Exception):
    def __init__(self, code, msg):
        self.code, self.msg = code, msg


@app.errorhandler(ApiError)
def handle_api_error(e):
    return jsonify({"error": e.msg}), e.code


@app.errorhandler(404)
def handle_404(_):
    return jsonify({"error": "Ruta no encontrada"}), 404


@app.errorhandler(405)
def handle_405(_):
    return jsonify({"error": "Metodo no permitido"}), 405


@app.errorhandler(Exception)
def handle_500(e):
    app.logger.exception(e)
    return jsonify({"error": "Error interno del servidor"}), 500


def get_conn():
    return pymssql.connect(
        server=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "1433")),
        user=os.environ.get("DB_USER", "sa"),
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "OrdenesDB"),
        login_timeout=10,
    )


@contextmanager
def db():
    conn = get_conn()
    try:
        cur = conn.cursor(as_dict=True)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ser(row):
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, decimal.Decimal):
            v = float(v)
        elif isinstance(v, (datetime.date, datetime.datetime)):
            v = v.isoformat()
        out[k] = v
    return out


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Se esperaba un cuerpo JSON valido")
    return data


def p_fecha(v):
    if v in (None, ""):
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(str(v))
    except ValueError:
        raise ApiError(400, "La fecha debe tener formato YYYY-MM-DD")


def p_estado(v):
    if v is None:
        return "Pendiente"
    if v not in ESTADOS:
        raise ApiError(400, "Estado invalido. Use: " + ", ".join(sorted(ESTADOS)))
    return v


def p_texto(data, key, required=True, default=None):
    v = data.get(key, default)
    if v is None or str(v).strip() == "":
        if required:
            raise ApiError(400, f"El campo '{key}' es obligatorio")
        return default
    return str(v).strip()[:100]


def p_num(v, name, integer=False, minimum=0, strict=False):
    try:
        n = decimal.Decimal(str(v))
    except (decimal.InvalidOperation, ValueError):
        raise ApiError(400, f"'{name}' debe ser numerico")
    if integer and n != n.to_integral_value():
        raise ApiError(400, f"'{name}' debe ser un entero")
    if (strict and n <= minimum) or (not strict and n < minimum):
        raise ApiError(400, f"'{name}' debe ser {'mayor que' if strict else 'mayor o igual a'} {minimum}")
    return int(n) if integer else n


def recalcular_total(cur, orden_id):
    cur.execute(
        "UPDATE ordenes SET total = ISNULL((SELECT SUM(subtotal) FROM orden_detalle "
        "WHERE orden_id = %s), 0) WHERE id = %s",
        (orden_id, orden_id),
    )


def orden_existe(cur, orden_id):
    cur.execute("SELECT * FROM ordenes WHERE id = %s", (orden_id,))
    row = cur.fetchone()
    if not row:
        raise ApiError(404, f"La orden {orden_id} no existe")
    return row


def insertar_detalle(cur, orden_id, d):
    producto = p_texto(d, "producto")
    cantidad = p_num(d.get("cantidad"), "cantidad", integer=True, minimum=0, strict=True)
    precio = p_num(d.get("precio_unitario"), "precio_unitario")
    cur.execute(
        "INSERT INTO orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) "
        "OUTPUT INSERTED.id VALUES (%s, %s, %s, %s, %s)",
        (orden_id, producto, cantidad, precio, cantidad * precio),
    )
    return cur.fetchone()["id"]


@app.get("/health")
def health():
    try:
        with db() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        return jsonify({"status": "ok", "db": "ok"}), 200
    except Exception as e:
        app.logger.error("health: %s", e)
        return jsonify({"status": "error", "db": "no disponible"}), 503


# ---------- Ordenes ----------
@app.get("/api/ordenes")
def listar_ordenes():
    with db() as cur:
        cur.execute("SELECT * FROM ordenes ORDER BY id")
        return jsonify([ser(r) for r in cur.fetchall()]), 200


@app.get("/api/ordenes/<int:oid>")
def ver_orden(oid):
    with db() as cur:
        orden = ser(orden_existe(cur, oid))
        cur.execute("SELECT * FROM orden_detalle WHERE orden_id = %s ORDER BY id", (oid,))
        orden["detalles"] = [ser(r) for r in cur.fetchall()]
        return jsonify(orden), 200


@app.post("/api/ordenes")
def crear_orden():
    data = body()
    cliente = p_texto(data, "cliente")
    fecha = p_fecha(data.get("fecha"))
    estado = p_estado(data.get("estado"))
    detalles = data.get("detalles") or []
    if not isinstance(detalles, list):
        raise ApiError(400, "'detalles' debe ser una lista")
    with db() as cur:
        cur.execute(
            "INSERT INTO ordenes (cliente, fecha, estado, total) OUTPUT INSERTED.id VALUES (%s, %s, %s, 0)",
            (cliente, fecha, estado),
        )
        oid = cur.fetchone()["id"]
        for d in detalles:
            if not isinstance(d, dict):
                raise ApiError(400, "Cada detalle debe ser un objeto")
            insertar_detalle(cur, oid, d)
        recalcular_total(cur, oid)
        cur.execute("SELECT * FROM ordenes WHERE id = %s", (oid,))
        return jsonify(ser(cur.fetchone())), 201


@app.put("/api/ordenes/<int:oid>")
def actualizar_orden(oid):
    data = body()
    with db() as cur:
        actual = orden_existe(cur, oid)
        cliente = p_texto(data, "cliente", default=actual["cliente"])
        fecha = p_fecha(data["fecha"]) if "fecha" in data else actual["fecha"]
        estado = p_estado(data["estado"]) if "estado" in data else actual["estado"]
        cur.execute(
            "UPDATE ordenes SET cliente = %s, fecha = %s, estado = %s WHERE id = %s",
            (cliente, fecha, estado, oid),
        )
        cur.execute("SELECT * FROM ordenes WHERE id = %s", (oid,))
        return jsonify(ser(cur.fetchone())), 200


@app.delete("/api/ordenes/<int:oid>")
def eliminar_orden(oid):
    with db() as cur:
        orden_existe(cur, oid)
        cur.execute("DELETE FROM orden_detalle WHERE orden_id = %s", (oid,))
        cur.execute("DELETE FROM ordenes WHERE id = %s", (oid,))
        return jsonify({"mensaje": f"Orden {oid} eliminada"}), 200


# ---------- Detalles ----------
@app.get("/api/ordenes/<int:oid>/detalles")
def listar_detalles(oid):
    with db() as cur:
        orden_existe(cur, oid)
        cur.execute("SELECT * FROM orden_detalle WHERE orden_id = %s ORDER BY id", (oid,))
        return jsonify([ser(r) for r in cur.fetchall()]), 200


@app.post("/api/ordenes/<int:oid>/detalles")
def agregar_detalle(oid):
    data = body()
    with db() as cur:
        orden_existe(cur, oid)
        did = insertar_detalle(cur, oid, data)
        recalcular_total(cur, oid)
        cur.execute("SELECT * FROM orden_detalle WHERE id = %s", (did,))
        return jsonify(ser(cur.fetchone())), 201


@app.put("/api/detalles/<int:did>")
def actualizar_detalle(did):
    data = body()
    with db() as cur:
        cur.execute("SELECT * FROM orden_detalle WHERE id = %s", (did,))
        actual = cur.fetchone()
        if not actual:
            raise ApiError(404, f"El detalle {did} no existe")
        producto = p_texto(data, "producto", default=actual["producto"])
        cantidad = p_num(data.get("cantidad", actual["cantidad"]), "cantidad", integer=True, minimum=0, strict=True)
        precio = p_num(data.get("precio_unitario", actual["precio_unitario"]), "precio_unitario")
        cur.execute(
            "UPDATE orden_detalle SET producto = %s, cantidad = %s, precio_unitario = %s, subtotal = %s WHERE id = %s",
            (producto, cantidad, precio, cantidad * precio, did),
        )
        recalcular_total(cur, actual["orden_id"])
        cur.execute("SELECT * FROM orden_detalle WHERE id = %s", (did,))
        return jsonify(ser(cur.fetchone())), 200


@app.delete("/api/detalles/<int:did>")
def eliminar_detalle(did):
    with db() as cur:
        cur.execute("SELECT orden_id FROM orden_detalle WHERE id = %s", (did,))
        actual = cur.fetchone()
        if not actual:
            raise ApiError(404, f"El detalle {did} no existe")
        cur.execute("DELETE FROM orden_detalle WHERE id = %s", (did,))
        recalcular_total(cur, actual["orden_id"])
        return jsonify({"mensaje": f"Detalle {did} eliminado"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
