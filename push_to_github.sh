#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Preparando para subir cambios a GitHub...${NC}"

# Verificar si hay cambios sin confirmar
if [[ -z $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️ No hay cambios para subir.${NC}"
    exit 0
fi

# Crear una rama temporal para los cambios
TEMP_BRANCH="temp_github_push_$(date +%Y%m%d%H%M%S)"
echo -e "${GREEN}📌 Creando rama temporal ${TEMP_BRANCH}...${NC}"
git checkout -b $TEMP_BRANCH

# Crear una copia de seguridad de los archivos sensibles
echo -e "${GREEN}📦 Creando copia de seguridad de archivos sensibles...${NC}"
if [[ -f .env ]]; then
    cp .env .env.temp
fi
if [[ -f .env.backup ]]; then
    cp .env.backup .env.backup.temp
fi

# Eliminar archivos sensibles del seguimiento de Git
echo -e "${GREEN}🔒 Eliminando archivos sensibles del seguimiento de Git...${NC}"
if [[ -f .env ]]; then
    git rm --cached .env 2>/dev/null || true
fi
if [[ -f .env.backup ]]; then
    git rm --cached .env.backup 2>/dev/null || true
fi

# Añadir todos los cambios
echo -e "${GREEN}➕ Añadiendo cambios...${NC}"
git add .

# Solicitar mensaje de commit
echo -e "${YELLOW}📝 Ingresa un mensaje para el commit:${NC}"
read -p "> " COMMIT_MESSAGE

if [[ -z "$COMMIT_MESSAGE" ]]; then
    COMMIT_MESSAGE="Actualización: $(date +%Y-%m-%d)"
fi

# Hacer commit
echo -e "${GREEN}💾 Haciendo commit: $COMMIT_MESSAGE${NC}"
git commit -m "$COMMIT_MESSAGE"

# Subir a GitHub
echo -e "${GREEN}⬆️ Subiendo a GitHub...${NC}"
git push github $TEMP_BRANCH:main

# Volver a la rama original
echo -e "${GREEN}🔙 Volviendo a la rama principal...${NC}"
git checkout main

# Eliminar la rama temporal
echo -e "${GREEN}🗑️ Eliminando rama temporal...${NC}"
git branch -D $TEMP_BRANCH

# Restaurar archivos sensibles
echo -e "${GREEN}🔄 Restaurando archivos sensibles...${NC}"
if [[ -f .env.temp ]]; then
    mv .env.temp .env
fi
if [[ -f .env.backup.temp ]]; then
    mv .env.backup.temp .env.backup
fi

echo -e "${GREEN}✅ Cambios subidos exitosamente a GitHub${NC}" 