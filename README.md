# Semana 5 — Administrador con Django

Desarrollo de Aplicaciones Empresariales (4-C24-A). Laboratorio de la semana 5:
configuración del panel de administración de Django para un catálogo de películas
con relaciones muchos-a-muchos y uno-a-muchos.

## Estructura

```
semana5/            proyecto (settings, urls, wsgi, asgi)
movies/             aplicación
├── admin.py        ModelAdmin, inline de valoraciones y gestión de grupos
├── models.py       Genre, Person, Movie, Rating
├── views.py        catálogo público y recomendación por género
├── urls.py
├── tests.py        19 pruebas del panel, los permisos y la vista pública
├── static/         hoja de estilos del sitio público
├── management/commands/seed_movies.py
└── migrations/
templates/          plantillas del sitio público y del login
```

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env         # configurar el SECRET_KEY
python manage.py migrate
python manage.py seed_movies   # 10 películas, 4 géneros, 20 personas, 14 valoraciones
python manage.py createsuperuser
python manage.py runserver
```

Cuentas de prueba que crea `seed_movies`:

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| superusuario | la que se defina en `createsuperuser` | acceso total |
| `editor` | `editor12345` | grupo `editores`: añade y cambia, no elimina |

## Qué resuelve el panel

- `MovieAdmin` con `list_display` (título, año, géneros, media y número de
  valoraciones), `list_filter` por género y año, y `search_fields` por título,
  género y nombre de persona.
- `RatingInline` como bloque tabular: las valoraciones se dan de alta sin salir
  de la película.
- `created_at` y `updated_at` en `readonly_fields`, dentro de un fieldset
  «Audit», para que el panel ya no permita editarlos.
- `RoleGroupAdmin` sustituye al `GroupAdmin` por defecto para crear y revisar
  el grupo `editores` desde el propio panel.

## La vista que el panel no da

El panel sirve para gestionar filas; no para mostrarlas ordenadas por la nota
media. `MovieDetailView` calcula las recomendaciones con
`Movie.recommended_movies()`: películas que comparten al menos un género con la
actual, promediadas con `Avg("ratings__score")` y ordenadas de mayor a menor,
excluyendo la propia película y las que no tienen valoraciones.

## Reparto de roles

> Completar con los nombres reales del equipo antes de entregar.

| Integrante | Desarrollo | Por qué |
| --- | --- | --- |
| Nombre | Modelos y migraciones | Define las relaciones de las que dependen el inline y los permisos. |
| Nombre | `admin.py` y grupo `editores` | Es el núcleo de la rúbrica: listado, filtros, búsqueda y control de acceso. |
| Nombre | Vistas públicas, plantillas y CSS | Contrasta qué resuelve el panel y qué exige una vista propia. |
| Nombre | Pruebas y comando `seed_movies` | Deja evidencia reproducible de los permisos y de la recomendación. |

## Observaciones

- **Permisos frente a vistas.** Ocultar el botón de eliminar no es lo mismo que
  impedirlo: el editor recibe un 403 en la vista de borrado. La prueba
  `test_editor_cannot_reach_the_delete_view` lo comprueba.
- **Anotar y no acumular.** `MovieQuerySet.with_scores()` centraliza
  `avg_score` y `rating_count`; el contador usa `distinct=True` porque al
  combinar el filtro por género con la agregación la consulta multiplica las
  filas. Es también la razón por la que `avg_score` no puede ser una propiedad
  con el mismo nombre que la anotación.
- **Auditoría.** `auto_now_add` y `auto_now` ya impiden escribir esos campos;
  `readonly_fields` solo evita que se muestren como editables.
- **Secretos.** `settings.py` lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
  `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` del entorno, con un
  `.env` opcional; no hay credenciales escritas a mano en el código.

## Pruebas

```bash
python manage.py test
```

Cubre el registro de los cuatro modelos, las opciones de `ModelAdmin`, el inline
de valoraciones, los campos de solo lectura, la recomendación por género, el
contenido exigido por el laboratorio (10 películas, 4 géneros, valoraciones en al
menos cinco) y la diferencia entre lo que ve el superusuario y el usuario del
grupo `editores`.
