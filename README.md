# ArenaPadel.club

Sistema de reservas para canchas de pádel desarrollado con Django.

## Características

- Sistema de autenticación de usuarios
- Gestión de canchas de pádel
- Sistema de reservas con confirmación
- Panel de usuario con historial de reservas
- Capacidad para cancelar reservas
- Interfaz responsive y amigable

## Requisitos

- Python 3.8+
- Django 4.2.18
- Otras dependencias en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone <URL_DEL_REPOSITORIO>
cd arenapadel
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Aplicar migraciones:
```bash
python manage.py migrate
```

5. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

6. Ejecutar servidor de desarrollo:
```bash
python manage.py runserver
```

## Uso

1. Acceder a http://localhost:8000
2. Registrarse o iniciar sesión
3. Navegar a la lista de canchas
4. Seleccionar una cancha y realizar una reserva

## Desarrollo

El proyecto sigue una estructura modular con las siguientes apps:

- `users`: Gestión de usuarios y autenticación
- `reservations`: Sistema de reservas
- `payments`: Sistema de pagos (en desarrollo)

## Licencia

MIT
