from django.utils import timezone
from celery import shared_task
import logging
from .exchange_rates import get_bcv_exchange_rate_direct
from .models import ExchangeRate

logger = logging.getLogger(__name__)

@shared_task
def update_bcv_exchange_rate():
    """
    Tarea programada para actualizar la tasa de cambio del BCV
    Se ejecutará automáticamente según la configuración en settings.py
    """
    try:
        # Obtenemos la tasa directamente del BCV
        rate = get_bcv_exchange_rate_direct()
        if rate:
            # Desactivamos todas las tasas activas primero
            ExchangeRate.objects.filter(is_active=True).update(is_active=False)
            
            # Creamos una nueva tasa con el valor obtenido
            ExchangeRate.objects.create(
                rate=rate,
                source='BCV (Automático)',
                source_url='https://www.bcv.org.ve/',
                is_active=True,
                obtained_automatically=True
            )
            
            logger.info(f"Tasa de cambio BCV actualizada exitosamente: {rate}")
            return True
        else:
            logger.warning("No se pudo obtener la tasa de cambio del BCV")
            return False
    except Exception as e:
        logger.error(f"Error actualizando tasa de cambio BCV: {str(e)}")
        return False
