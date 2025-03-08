#!/bin/bash

# Configuración
BACKUP_DIR="/root/backups"
DAILY_DIR="${BACKUP_DIR}/daily"
WEEKLY_DIR="${BACKUP_DIR}/weekly"
APP_PATH="/var/www/arenapadel/app"
DB_NAME="arenapadel"
DB_USER="arenapadel"

# Función para listar backups disponibles
list_backups() {
    echo -e "\n📋 Backups diarios disponibles:"
    ls -lh "${DAILY_DIR}"/*_daily.tar.gz 2>/dev/null || echo "No hay backups diarios"
    echo -e "\n📋 Backups semanales disponibles:"
    ls -lh "${WEEKLY_DIR}"/*_weekly.tar.gz 2>/dev/null || echo "No hay backups semanales"
}

# Si no se proporciona argumento, mostrar backups disponibles
if [ -z "$1" ]; then
    echo "❌ Debe especificar el archivo de backup a restaurar"
    echo "Uso: ./restore_arenapadel.sh nombre_del_backup.tar.gz"
    list_backups
    exit 1
fi

BACKUP_FILE="$1"
if [[ $BACKUP_FILE != /* ]]; then
    # Si no es ruta absoluta, buscar en los directorios de backup
    if [ -f "${DAILY_DIR}/${BACKUP_FILE}" ]; then
        BACKUP_FILE="${DAILY_DIR}/${BACKUP_FILE}"
    elif [ -f "${WEEKLY_DIR}/${BACKUP_FILE}" ]; then
        BACKUP_FILE="${WEEKLY_DIR}/${BACKUP_FILE}"
    fi
fi

# Verificar que el archivo existe
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ El archivo de backup no existe: ${BACKUP_FILE}"
    list_backups
    exit 1
fi

echo "🔄 Iniciando restauración del sistema..."

# Crear backup de seguridad del estado actual
echo "📦 Creando backup de seguridad del estado actual..."
SAFETY_BACKUP="pre_restore_$(date +%Y%m%d_%H%M%S)"
/root/backup_arenapadel.sh "${SAFETY_BACKUP}"

# Detener servicios
echo "🛑 Deteniendo servicios..."
systemctl stop gunicorn
systemctl stop nginx

# Crear directorio temporal para la restauración
TEMP_DIR=$(mktemp -d)
cd "${TEMP_DIR}"

# Extraer backup
echo "📂 Extrayendo backup..."
tar -xzf "${BACKUP_FILE}"

# Restaurar base de datos
echo "💾 Restaurando base de datos..."
psql -U ${DB_USER} -d ${DB_NAME} -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U ${DB_USER} ${DB_NAME} < arenapadel_backup_*.sql

# Restaurar archivos
echo "📂 Restaurando archivos de la aplicación..."
rm -rf ${APP_PATH}/*
cp -r * ${APP_PATH}/

# Configurar permisos
echo "🔒 Configurando permisos..."
chown -R www-data:www-data ${APP_PATH}
chmod -R 755 ${APP_PATH}
chmod 600 ${APP_PATH}/.env

# Crear directorios necesarios
echo "📁 Asegurando directorios necesarios..."
mkdir -p ${APP_PATH}/{media,staticfiles,run}
chown -R www-data:www-data ${APP_PATH}/{media,staticfiles,run}

# Limpiar
cd /root
rm -rf "${TEMP_DIR}"

# Reiniciar servicios
echo "🚀 Reiniciando servicios..."
systemctl start nginx
systemctl start gunicorn

# Verificar estado
echo "🔍 Verificando servicios..."
systemctl status nginx --no-pager
systemctl status gunicorn --no-pager

echo "✅ Restauración completada exitosamente"
