import multiprocessing

# Configuración básica
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Configuración del proceso
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (configurar si se usa HTTPS directamente con Gunicorn)
# keyfile = "/etc/letsencrypt/live/arenaspadel.club/privkey.pem"
# certfile = "/etc/letsencrypt/live/arenaspadel.club/fullchain.pem"
