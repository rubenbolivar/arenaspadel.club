import os
from celery import Celery

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arenapadel.settings')

app = Celery('arenapadel')

# Usar configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas automáticamente
app.autodiscover_tasks()
