from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .api_client import ApiError, call

ESTADOS = ["Pendiente", "Pagada", "Anulada"]


def lista(request):
    ordenes = []
    try:
        ordenes = call("GET", "/api/ordenes")
    except ApiError as e:
        messages.error(request, str(e))
    return render(request, "ordenes/lista.html", {"ordenes": ordenes})


def orden_ver(request, pk):
    try:
        orden = call("GET", f"/api/ordenes/{pk}")
    except ApiError as e:
        messages.error(request, str(e))
        return redirect("lista")
    return render(request, "ordenes/orden.html", {"orden": orden})


def orden_form(request, pk=None):
    orden = {}
    if pk:
        try:
            orden = call("GET", f"/api/ordenes/{pk}")
        except ApiError as e:
            messages.error(request, str(e))
            return redirect("lista")
    if request.method == "POST":
        payload = {k: request.POST.get(k, "") for k in ("cliente", "fecha", "estado")}
        try:
            if pk:
                call("PUT", f"/api/ordenes/{pk}", payload)
                messages.success(request, "Orden actualizada")
                return redirect("orden_ver", pk=pk)
            nueva = call("POST", "/api/ordenes", payload)
            messages.success(request, "Orden creada")
            return redirect("orden_ver", pk=nueva["id"])
        except ApiError as e:
            messages.error(request, str(e))
            orden = {**orden, **payload}
    return render(request, "ordenes/orden_form.html", {"orden": orden, "estados": ESTADOS, "editando": bool(pk)})


@require_POST
def orden_eliminar(request, pk):
    try:
        call("DELETE", f"/api/ordenes/{pk}")
        messages.success(request, "Orden eliminada")
    except ApiError as e:
        messages.error(request, str(e))
    return redirect("lista")


def detalle_form(request, orden_id, pk=None):
    detalle = {}
    if pk:
        try:
            orden = call("GET", f"/api/ordenes/{orden_id}")
            detalle = next((d for d in orden["detalles"] if d["id"] == pk), None)
        except ApiError as e:
            messages.error(request, str(e))
            return redirect("lista")
        if detalle is None:
            messages.error(request, f"El detalle {pk} no existe")
            return redirect("orden_ver", pk=orden_id)
    if request.method == "POST":
        payload = {k: request.POST.get(k, "") for k in ("producto", "cantidad", "precio_unitario")}
        try:
            if pk:
                call("PUT", f"/api/detalles/{pk}", payload)
                messages.success(request, "Detalle actualizado")
            else:
                call("POST", f"/api/ordenes/{orden_id}/detalles", payload)
                messages.success(request, "Detalle agregado")
            return redirect("orden_ver", pk=orden_id)
        except ApiError as e:
            messages.error(request, str(e))
            detalle = {**detalle, **payload}
    return render(request, "ordenes/detalle_form.html", {"detalle": detalle, "orden_id": orden_id, "editando": bool(pk)})


@require_POST
def detalle_eliminar(request, orden_id, pk):
    try:
        call("DELETE", f"/api/detalles/{pk}")
        messages.success(request, "Detalle eliminado")
    except ApiError as e:
        messages.error(request, str(e))
    return redirect("orden_ver", pk=orden_id)
