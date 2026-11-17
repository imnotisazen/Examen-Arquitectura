# Ordenes de venta - Arquitectura de 3 contenedores

Examen practico 2P - Arquitectura de Computadoras. Django (web) + Flask (api) + SQL Server 2022 (db) con Docker Compose.

## Integrantes
| Nombre completo | Numero de cuenta |
|---|---|
| RUTH LIZETH PALACIOS ORDOÑEZ | 202410110195 |


## Arquitectura
```
Navegador --:8000--> web (Django) --http://api:5000--> api (Flask) --db:1433--> db (SQL Server 2022)
                                                                                   |
                                                                      volumen mssql_data (/var/opt/mssql)
        Todos en la red bridge "ordenes-net"
```
| Servicio | Imagen | Puerto | Limites |
|---|---|---|---|
| db | mcr.microsoft.com/mssql/server:2022-latest | (interno 1433) | 2 CPU / 2 GB |
| db-init | misma imagen, ejecuta `db/init.sql` y termina | - | 0.25 CPU / 128 MB |
| api | `ruth2005/ordenes-api:v1.0` | 5002 | 0.5 CPU / 256 MB |
| web | `ruth2005/ordenes-web:v1.0` | 8000 | 0.5 CPU / 256 MB |

`api` y `web` corren con usuario sin privilegios (`appuser`). Solo `api` se conecta a la base de datos.

## Ejecutar desde cero
```bash
git clone [https://github.com/palaciosruth52-alt/Examen-Arquitectura.git](https://github.com/palaciosruth52-alt/Examen-Arquitectura.git) && cd Examen-Arquitectura 
cp .env.example .env        # editar MSSQL_SA_PASSWORD y DOCKERHUB_USER
docker compose up -d --build
docker compose ps            # esperar a que db, api y web esten "healthy"
```
- Frontend: http://localhost:8000
- API: http://localhost:5000/api/ordenes y http://localhost:5000/health

**Inicializacion de la BD:** el servicio `db-init` ejecuta `db/init.sql` con `sqlcmd` cuando `db` esta sano (crea `OrdenesDB`, las tablas y 5 ordenes de prueba; es idempotente). `api` espera a que termine con `service_completed_successfully`.

## Probar la API (curl)
```bash
curl localhost:5000/api/ordenes
curl localhost:5000/api/ordenes/1
curl -X POST localhost:5000/api/ordenes -H "Content-Type: application/json" -d '{"cliente":"Pulperia El Sol","estado":"Pendiente"}'
curl -X POST localhost:5000/api/ordenes/6/detalles -H "Content-Type: application/json" -d '{"producto":"Cafe Marcala","cantidad":3,"precio_unitario":95}'
curl -X PUT localhost:5000/api/ordenes/6 -H "Content-Type: application/json" -d '{"estado":"Pagada"}'
curl -X PUT localhost:5000/api/detalles/17 -H "Content-Type: application/json" -d '{"cantidad":5}'
curl -X DELETE localhost:5000/api/detalles/17
curl -X DELETE localhost:5000/api/ordenes/6
```
(Ajustar los ids segun lo que devuelva cada llamada.)

## Persistencia
```bash
docker compose down      # NO usar -v
docker compose up -d
```
Los datos siguen ahi porque estan en el volumen `ordenes_mssql_data`.

## Publicar en Docker Hub
```bash
docker login
docker compose build
docker compose push api web     # usa DOCKERHUB_USER e IMAGE_TAG del .env
```
Enlaces: `https://hub.docker.com/r/<usuario>/ordenes-api` y `.../ordenes-web`

## Evidencias (carpeta `evidencias/`)
- [ ] `docker compose ps` con los 3 servicios sanos
- [ ] CRUD funcionando en el navegador
- [ ] Pruebas de la API (curl / Postman)
- [ ] Datos que persisten tras `down` y `up`
- [ ] `docker stats --no-stream` con los limites
