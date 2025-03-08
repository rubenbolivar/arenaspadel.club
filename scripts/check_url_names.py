#!/usr/bin/env python3
"""
Script para verificar que los nombres de URL sigan la convención establecida.
"""

import os
import re
import sys
from pathlib import Path

# Patrones válidos para nombres de URL
VALID_PATTERNS = [
    # Páginas principales
    r'^home$',
    r'^about$',
    r'^contact$',
    r'^terms$',
    
    # Autenticación
    r'^login$',
    r'^logout$',
    r'^register$',
    r'^password_reset$',
    r'^password_change$',
    
    # Perfil
    r'^profile$',
    r'^profile_edit$',
    
    # Recursos principales
    r'^[a-z]+_list$',           # court_list, reservation_list
    r'^[a-z]+_detail$',         # court_detail, reservation_detail
    r'^[a-z]+_create$',         # reservation_create
    r'^[a-z]+_edit$',           # reservation_edit
    r'^[a-z]+_delete$',         # reservation_delete
    r'^[a-z]+_cancel$',         # reservation_cancel
    r'^[a-z]+_confirm$',        # payment_confirm
    r'^[a-z]+_success$',        # payment_success
]

def is_valid_url_name(name):
    """Verifica si un nombre de URL sigue la convención."""
    return any(re.match(pattern, name) for pattern in VALID_PATTERNS)

def check_urls_py(file_path):
    """Revisa los nombres de URL en un archivo urls.py."""
    errors = []
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Buscar patrones name='algo' en las URLs
    url_names = re.finditer(r"name=['\"]([^'\"]+)['\"]", content)
    
    for match in url_names:
        name = match.group(1)
        if not is_valid_url_name(name):
            errors.append(f"URL name '{name}' en {file_path} no sigue la convención")
    
    return errors

def check_templates(template_dir):
    """Revisa los nombres de URL en archivos de plantillas."""
    errors = []
    
    for root, _, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Buscar patrones {% url 'algo' %} en las plantillas
                url_names = re.finditer(r"{%\s*url\s+['\"]([^'\"]+)['\"]", content)
                
                for match in url_names:
                    name = match.group(1)
                    # Ignorar nombres con ':' que son de otras apps
                    if ':' not in name and not is_valid_url_name(name):
                        errors.append(f"URL name '{name}' en {file_path} no sigue la convención")
    
    return errors

def main():
    """Función principal."""
    # Obtener el directorio base del proyecto
    base_dir = Path(__file__).resolve().parent.parent
    
    all_errors = []
    
    # Revisar todos los archivos urls.py
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == 'urls.py':
                file_path = os.path.join(root, file)
                all_errors.extend(check_urls_py(file_path))
    
    # Revisar las plantillas
    template_dir = base_dir / 'templates'
    if template_dir.exists():
        all_errors.extend(check_templates(template_dir))
    
    # Mostrar resultados
    if all_errors:
        print("Se encontraron los siguientes errores:")
        for error in all_errors:
            print(f"- {error}")
        sys.exit(1)
    else:
        print("¡Todas las URLs siguen la convención!")
        sys.exit(0)

if __name__ == '__main__':
    main()
