# Pruebas de Carga para ArenasPadel.club

Este documento describe cómo realizar pruebas de carga en el sistema para determinar su capacidad y estabilidad bajo diferentes cargas de usuarios.

## Configuración Actual del Servidor

- **CPU**: 2 cores (QEMU Virtual CPU)
- **Memoria**: 1.9 GB RAM
- **Gunicorn**: 3 workers
- **Base de Datos**: PostgreSQL

## Ejecutar Pruebas de Carga con Locust

### Instalación

```bash
# Crear un entorno virtual para las pruebas (opcional pero recomendado)
python -m venv venv_test
source venv_test/bin/activate  # En Linux/Mac
# O en Windows:
# venv_test\Scripts\activate

# Instalar dependencias
pip install -r tests/requirements-test.txt
```

### Ejecutar las Pruebas

```bash
cd /path/to/arenapadel
locust -f tests/locustfile.py
```

Luego, abre un navegador y ve a http://localhost:8089 para iniciar y monitorear las pruebas.

### Parámetros Recomendados para Pruebas

1. **Prueba Inicial**:
   - Usuarios: 10 (iniciar con 1, incrementar hasta 10)
   - Tasa de Spawn: 1 usuario/segundo
   - Tiempo: 5 minutos

2. **Prueba Moderada**:
   - Usuarios: 50 (incremento gradual)
   - Tasa de Spawn: 2 usuarios/segundo
   - Tiempo: 10 minutos

3. **Prueba de Estrés**:
   - Usuarios: 100+
   - Tasa de Spawn: 5 usuarios/segundo
   - Tiempo: 15 minutos

## Interpretación de Resultados

- **Tiempo de Respuesta**: Menos de 200ms es excelente, 200-500ms es bueno, más de 1s indica problemas.
- **Tasa de Errores**: Debería ser cercana a 0%. Un incremento en errores indica sobrecarga.
- **Solicitudes por Segundo (RPS)**: Determina la capacidad máxima del sistema.

## Monitoreo Durante las Pruebas

Durante las pruebas, monitorea estos indicadores:

```bash
# En otra terminal SSH, ejecuta:
watch -n 1 "free -h && echo && uptime && echo && ps aux | grep gunicorn | grep -v grep"
```

Para monitorear la base de datos:

```sql
-- En PostgreSQL, monitorea conexiones activas:
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

## Estimación de Capacidad

Con la configuración actual (2 cores, 1.9GB RAM, 3 workers de Gunicorn), una estimación conservadora sería:

- **Usuarios Concurrentes**: ~50-100 usuarios navegando
- **Procesos de Reserva Simultáneos**: ~20-30

Para aumentar la capacidad, considere:

1. Aumentar workers de Gunicorn (workers = 2*núcleos + 1)
2. Implementar caché con Redis
3. Optimizar consultas de base de datos
4. Escalar verticalmente (más CPU/RAM)

## Recomendaciones para Escenarios de Alta Demanda

Para eventos especiales donde se espere un pico de demanda:

1. Aumentar temporalmente recursos del servidor
2. Implementar una sala de espera (queue) para regular el acceso
3. Establecer límites de tiempo para completar reservaciones
4. Implementar una estrategia de caché agresiva
