import requests
import logging
from decimal import Decimal, InvalidOperation
from django.core.cache import cache
from django.utils import timezone
import datetime
from bs4 import BeautifulSoup
import re
import urllib3

# Suprimir advertencias de seguridad para las solicitudes sin verificación SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Tiempo de expiración del caché en segundos (30 minutos)
CACHE_TIMEOUT = 30 * 60

def get_bcv_exchange_rate():
    """
    Obtiene la tasa de cambio oficial del BCV (Banco Central de Venezuela).
    Primero busca en la base de datos, luego en caché y finalmente intenta obtenerla vía web scraping.
    
    Returns:
        Decimal: La tasa de cambio actual BCV USD/VES o None si hay un error
    """
    # Primero intentamos obtener de la base de datos
    from .models import ExchangeRate
    db_rate = ExchangeRate.get_latest_rate()
    if db_rate:
        return db_rate.rate
    
    # Si no hay en la base de datos, intentamos obtener del caché
    cached_rate = cache.get('bcv_exchange_rate')
    if cached_rate is not None:
        return cached_rate
    
    # Si no está en caché, obtenemos a través de web scraping
    rate = get_bcv_exchange_rate_direct()
    if rate:
        # Guardamos en la base de datos y en caché
        try:
            ExchangeRate.objects.create(
                rate=rate,
                source='BCV (Web)',
                source_url='https://www.bcv.org.ve/',
                is_active=True,
                obtained_automatically=True
            )
        except Exception as e:
            logger.error(f"Error guardando tasa en la base de datos: {str(e)}")
        
        # También guardamos en caché como respaldo
        cache.set('bcv_exchange_rate', rate, CACHE_TIMEOUT)
        cache.set('bcv_exchange_rate_updated', timezone.now(), CACHE_TIMEOUT)
        
        return rate
    
    # Si no se pudo obtener la tasa, retornamos None
    return None

def get_bcv_exchange_rate_direct():
    """
    Obtiene la tasa de cambio oficial del BCV directamente mediante web scraping.
    
    Returns:
        Decimal: La tasa de cambio actual BCV USD/VES o None si hay un error
    """
    try:
        # Hacemos una solicitud a la página principal del BCV
        # Deshabilitamos la verificación de SSL debido a problemas con el certificado del BCV
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        response = requests.get('https://www.bcv.org.ve/', headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        # Utilizamos BeautifulSoup para analizar el HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Nueva estrategia: Buscar el símbolo 'USD' y extraer su valor asociado
        # El formato actual en la web del BCV muestra USD con el símbolo de dólar y luego el valor
        
        # Buscar elementos que contengan el texto 'USD'
        usd_elements = soup.find_all(string=re.compile('USD'))
        for element in usd_elements:
            # Para cada elemento encontrado, buscar números cercanos
            parent = element.parent
            if not parent:
                continue
                
            # Buscar en el elemento padre y sus hermanos
            container = parent.parent if parent.parent else parent
            
            # Buscar un número grande en todo el contenedor que probablemente sea la tasa
            rate_match = re.search(r'(\d+[,\.]\d+)', container.get_text())
            if rate_match:
                rate_str = rate_match.group(1).replace(',', '.')
                try:
                    rate = Decimal(rate_str)
                    if rate > 10:  # Las tasas de BCV USD/VES son generalmente mayores que 10
                        logger.info(f"Tasa BCV obtenida exitosamente: {rate}")
                        return rate
                except Exception as e:
                    logger.warning(f"Error convirtiendo valor encontrado: {rate_str}. Error: {str(e)}")
        
        # Buscar específicamente por el símbolo del dólar ($) y su valor asociado
        dollar_symbols = soup.find_all(string=re.compile('[\$]'))
        for element in dollar_symbols:
            container = element.parent.parent if element.parent and element.parent.parent else element.parent if element.parent else None
            if container:
                text = container.get_text()
                # Buscar un número grande que sería la tasa
                rate_match = re.search(r'(\d+[,\.]\d+)', text)
                if rate_match:
                    rate_str = rate_match.group(1).replace(',', '.')
                    try:
                        rate = Decimal(rate_str)
                        if rate > 10:  # Las tasas de BCV USD/VES son generalmente mayores que 10
                            logger.info(f"Tasa BCV obtenida a partir de símbolo dólar: {rate}")
                            return rate
                    except Exception as e:
                        logger.warning(f"Error convirtiendo valor encontrado con símbolo dólar: {rate_str}. Error: {str(e)}")
        
        # Si no encontramos la tasa, retornamos None
        logger.warning("No se pudo extraer la tasa de cambio del BCV")
        return None
            
    except Exception as e:
        logger.error(f"Error obteniendo tasa de cambio del BCV: {str(e)}")
        return None

def get_last_update_time():
    """
    Obtiene la última vez que se actualizó la tasa de cambio
    
    Returns:
        datetime: La última fecha/hora de actualización o None
    """
    # Intentamos obtener de la base de datos primero
    from .models import ExchangeRate
    db_rate = ExchangeRate.get_latest_rate()
    if db_rate:
        return db_rate.created_at
    
    # Si no hay en la base de datos, usamos el valor en caché
    return cache.get('bcv_exchange_rate_updated')

def calculate_bolivares_amount(usd_amount):
    """
    Calcula el monto en Bolívares utilizando la tasa de cambio del BCV
    
    Args:
        usd_amount (Decimal): Monto en dólares
    
    Returns:
        Decimal: Monto calculado en Bolívares o None si no se puede calcular
    """
    rate = get_bcv_exchange_rate()
    if rate is None or usd_amount is None:
        return None
    
    try:
        return usd_amount * rate
    except Exception as e:
        logger.error(f"Error calculando monto en Bolívares: {str(e)}")
        return None