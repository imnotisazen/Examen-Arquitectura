from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista, name="lista"),
    path("ordenes/nueva/", views.orden_form, name="orden_nueva"),
    path("ordenes/<int:pk>/", views.orden_ver, name="orden_ver"),
    path("ordenes/<int:pk>/editar/", views.orden_form, name="orden_editar"),
    path("ordenes/<int:pk>/eliminar/", views.orden_eliminar, name="orden_eliminar"),
    path("ordenes/<int:orden_id>/detalles/nuevo/", views.detalle_form, name="detalle_nuevo"),
    path("ordenes/<int:orden_id>/detalles/<int:pk>/editar/", views.detalle_form, name="detalle_editar"),
    path("ordenes/<int:orden_id>/detalles/<int:pk>/eliminar/", views.detalle_eliminar, name="detalle_eliminar"),
]
