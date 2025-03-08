from django import template
from decimal import Decimal
from payments.exchange_rates import calculate_bolivares_amount, get_bcv_exchange_rate, get_last_update_time

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def format_price(value):
    """
    Formatea el precio con formato venezolano ($45,00)
    """
    if value is None:
        return "0,00"
    
    try:
        # Convertir a string y formatear
        value_str = str(value)
        if '.' in value_str:
            whole, decimal = value_str.split('.')
            if len(decimal) == 1:
                decimal += '0'
            elif len(decimal) > 2:
                decimal = decimal[:2]
            return f"{whole},{decimal}"
        else:
            return f"{value_str},00"
    except Exception:
        return "0,00"

@register.filter
def to_bolivares(price):
    """
    Convierte un precio en dólares a bolívares usando la tasa del BCV
    """
    if price is None:
        return None
    try:
        price_decimal = Decimal(str(price))
        bolivares = calculate_bolivares_amount(price_decimal)
        return bolivares
    except Exception:
        return None

@register.simple_tag
def get_bcv_rate():
    """
    Obtiene la tasa de cambio actual del BCV
    """
    return get_bcv_exchange_rate()

@register.simple_tag
def get_bcv_last_update():
    """
    Obtiene la última fecha de actualización de la tasa del BCV
    """
    return get_last_update_time()
