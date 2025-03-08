# Convención de Nombres para URLs en ArenaPadel.club

Este documento establece las convenciones de nomenclatura para las URLs en el proyecto ArenaPadel.club. Seguir estas convenciones es obligatorio para mantener la consistencia y facilitar el mantenimiento del código.

## Principios Generales

1. **Simplicidad**: Los nombres deben ser simples y autoexplicativos
2. **Consistencia**: Usar el mismo patrón en toda la aplicación
3. **Descriptividad**: Los nombres deben describir claramente la acción o recurso
4. **Minúsculas**: Usar solo letras minúsculas y guiones bajos
5. **Sin prefijos**: No usar prefijos de aplicación ni namespaces

## Estructura de Nombres

### Páginas Principales
```python
'home'                  # Página de inicio
'about'                 # Acerca de
'contact'              # Contacto
'terms'                # Términos y condiciones
```

### Autenticación
```python
'login'                # Iniciar sesión
'logout'               # Cerrar sesión
'register'             # Registro
'password_reset'       # Restablecer contraseña
'password_change'      # Cambiar contraseña
```

### Perfil de Usuario
```python
'profile'              # Ver perfil
'profile_edit'         # Editar perfil
```

### Canchas
```python
'court_list'           # Lista de canchas
'court_detail'         # Detalle de cancha
```

### Reservas
```python
'reservation_create'   # Crear reserva
'reservation_list'     # Lista de reservas
'reservation_detail'   # Detalle de reserva
'reservation_cancel'   # Cancelar reserva
```

### Pagos
```python
'payment_create'       # Crear pago
'payment_confirm'      # Confirmar pago
'payment_success'      # Pago exitoso
'payment_cancel'       # Cancelar pago
```

## Reglas de Nombrado

1. **Recursos**
   - Usar sustantivos para recursos (`court`, `profile`, `reservation`)
   - Siempre en singular (`court` no `courts`)
   - Descriptivos y concisos

2. **Acciones**
   - Usar verbos para acciones (`create`, `edit`, `cancel`)
   - Colocar el verbo después del recurso (`reservation_cancel`)
   - Usar verbos comunes: `create`, `edit`, `delete`, `cancel`

3. **Listas y Detalles**
   - Para listas usar el sufijo `_list` (`court_list`)
   - Para detalles usar el sufijo `_detail` (`court_detail`)
   - Para acciones usar el verbo como sufijo (`reservation_cancel`)

## Implementación en URLs

### En urls.py
```python
# web_urls.py
urlpatterns = [
    path('', views.home, name='home'),
    path('courts/', views.court_list, name='court_list'),
    path('courts/<int:id>/', views.court_detail, name='court_detail'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/<int:id>/', views.reservation_detail, name='reservation_detail'),
]
```

### En Plantillas
```html
{# Correcto #}
{% url 'home' %}
{% url 'court_list' %}
{% url 'reservation_detail' id=1 %}

{# Incorrecto #}
{% url 'courts' %}                   {# Muy vago #}
{% url 'list_courts' %}             {# Orden incorrecto #}
{% url 'web:web_court_list' %}      {# No usar namespace ni prefijos #}
```

## Verificación

Para asegurar que todas las URLs sigan esta convención:

1. Revisar los archivos `urls.py` de cada aplicación
2. Verificar las plantillas en busca de nombres de URL
3. Ejecutar el script de verificación antes de cada commit

## Ejemplos de Uso

### Correcto
```python
# URLs
path('courts/', views.court_list, name='court_list')
path('reservations/create/', views.reservation_create, name='reservation_create')

# Plantillas
{% url 'court_list' %}
{% url 'reservation_create' %}
```

### Incorrecto
```python
# URLs
path('courts/', views.court_list, name='courts')              # Muy vago
path('list-courts/', views.court_list, name='list_courts')    # Orden incorrecto
path('new-reservation/', views.create, name='new_reservation') # Inconsistente

# Plantillas
{% url 'courts' %}                   # Muy vago
{% url 'web:web_court_list' %}      # No usar namespace
```

## Mantenimiento

1. Este documento debe ser revisado y actualizado cuando sea necesario
2. Cualquier excepción a estas reglas debe ser documentada y justificada
3. Las nuevas características deben seguir estas convenciones
4. Las URLs existentes deben ser refactorizadas para seguir estas convenciones cuando sea posible
