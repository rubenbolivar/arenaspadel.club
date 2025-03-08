#!/bin/bash
# Script para monitorear el servidor durante pruebas de carga

echo "Iniciando monitoreo del servidor..."
echo "Presiona Ctrl+C para detener."

while true; do
    clear
    echo "=== FECHA Y HORA ==="
    date
    
    echo -e "\n=== USO DE CPU ==="
    top -bn1 | head -15
    
    echo -e "\n=== MEMORIA ==="
    free -h
    
    echo -e "\n=== CARGA DEL SISTEMA ==="
    uptime
    
    echo -e "\n=== PROCESOS GUNICORN ==="
    ps aux | grep gunicorn | grep -v grep
    
    echo -e "\n=== CONEXIONES ACTIVAS ==="
    netstat -an | grep ESTABLISHED | wc -l
    
    echo -e "\n=== DISCO ==="
    df -h /
    
    sleep 5
done
