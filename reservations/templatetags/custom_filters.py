from django import template
import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filter to get an item from a dictionary using a key
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplies the value by the argument
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='spanish_day')
def spanish_day(date):
    """
    Returns the day of the week in Spanish
    Usage: {{ date|spanish_day }}
    """
    if not isinstance(date, datetime.date):
        return ""
        
    days = {
        0: 'Lun',
        1: 'Mar',
        2: 'Mié',
        3: 'Jue',
        4: 'Vie',
        5: 'Sáb',
        6: 'Dom',
    }
    
    return days[date.weekday()]

@register.filter(name='spanish_month')
def spanish_month(date):
    """
    Returns the month name in Spanish
    Usage: {{ date|spanish_month }}
    """
    if not isinstance(date, datetime.date):
        return ""
        
    months = {
        1: 'Ene',
        2: 'Feb',
        3: 'Mar',
        4: 'Abr',
        5: 'May',
        6: 'Jun',
        7: 'Jul',
        8: 'Ago',
        9: 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dic',
    }
    
    return months[date.month]

@register.filter(name='format_price')
def format_price(value):
    """
    Formats a decimal number as price with comma as decimal separator
    Usage: {{ value|format_price }}
    Example: 45000 -> 45,00
    """
    try:
        # Convertir a float y asegurar 2 decimales
        value = float(value)
        # Formatear con coma como separador decimal y 2 decimales
        return f"{value:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return value
