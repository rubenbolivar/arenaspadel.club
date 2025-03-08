from django.utils import timezone
from datetime import timedelta
from reservations.models import Reservation
from .whatsapp import WhatsAppNotifier

def send_reservation_reminders():
    """
    Envía recordatorios para las reservas que comenzarán en una hora.
    Esta tarea debería ejecutarse cada hora.
    """
    # Calculamos el rango de tiempo para las próximas reservas
    one_hour_from_now = timezone.now() + timedelta(hours=1)
    start_time = one_hour_from_now.replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    # Buscamos reservas que empiecen en la próxima hora
    reservations = Reservation.objects.filter(
        start_time__gte=start_time,
        start_time__lt=end_time,
        status='confirmed',
        user__whatsapp__isnull=False  # Aseguramos que el usuario tenga WhatsApp
    ).select_related('user', 'court')
    
    notifier = WhatsAppNotifier()
    results = []
    
    for reservation in reservations:
        success, message = notifier.send_reservation_reminder(reservation)
        results.append({
            'reservation_id': reservation.id,
            'success': success,
            'message': message,
            'scheduled_time': reservation.start_time.strftime('%H:%M'),
            'whatsapp': reservation.user.whatsapp  # Para debugging
        })
    
    return results
