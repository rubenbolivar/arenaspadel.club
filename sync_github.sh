#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Sincronizando con GitHub...${NC}"

# Verificar si hay cambios sin confirmar
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️ Hay cambios sin confirmar. Por favor, confirma o descarta estos cambios antes de sincronizar.${NC}"
    git status
    exit 1
fi

# Crear una copia de seguridad de los archivos sensibles
echo -e "${GREEN}📦 Creando copia de seguridad de archivos sensibles...${NC}"
if [[ -f .env ]]; then
    cp .env .env.bak
fi

# Actualizar desde GitHub
echo -e "${GREEN}⬇️ Actualizando desde GitHub...${NC}"
git pull github main

# Restaurar archivos sensibles
echo -e "${GREEN}🔄 Restaurando archivos sensibles...${NC}"
if [[ -f .env.bak ]]; then
    mv .env.bak .env
fi

echo -e "${GREEN}✅ Sincronización completada exitosamente${NC}" 