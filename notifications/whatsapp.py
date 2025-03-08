from twilio.rest import Client
from django.conf import settings
from django.template.loader import render_to_string

class WhatsAppNotifier:
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        # Asegurarnos que el número de Twilio tenga el formato correcto
        twilio_number = settings.TWILIO_WHATSAPP_NUMBER.strip()
        if not twilio_number.startswith('+'):
            twilio_number = f"+{twilio_number}"
        if not twilio_number.startswith('whatsapp:'):
            twilio_number = f"whatsapp:{twilio_number}"
        self.from_number = twilio_number

    def _format_phone(self, whatsapp):
        """Asegura que el número de teléfono tenga el formato correcto para WhatsApp."""
        whatsapp = str(whatsapp).strip()
        if not whatsapp.startswith('+'):
            whatsapp = f"+{whatsapp}"
        if not whatsapp.startswith('whatsapp:'):
            whatsapp = f"whatsapp:{whatsapp}"
        return whatsapp

    def send_message(self, to_whatsapp, template_name, context):
        """Método base para enviar mensajes."""
        try:
            message_body = render_to_string(
                f'notifications/whatsapp/{template_name}.txt',
                context
            )
            
            # Imprimir información de debug
            print(f"Sending message:")
            print(f"From: {self.from_number}")
            print(f"To: {self._format_phone(to_whatsapp)}")
            print(f"Body: {message_body}")
            
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self._format_phone(to_whatsapp)
            )
            return True, message.sid
        except Exception as e:
            return False, str(e)

    def send_reservation_confirmation(self, reservation):
        """Envía confirmación de reserva por WhatsApp."""
        if not reservation.user.whatsapp:
            return False, "No WhatsApp number provided"
            
        context = {
            'court_name': reservation.court.name,
            'date': reservation.start_time.strftime('%d/%m/%Y'),
            'time': reservation.start_time.strftime('%H:%M'),
            'price': reservation.total_price,
        }
        return self.send_message(
            reservation.user.whatsapp,
            'reservation_confirmation',
            context
        )

    def send_reservation_reminder(self, reservation):
        """Envía recordatorio de reserva por WhatsApp."""
        if not reservation.user.whatsapp:
            return False, "No WhatsApp number provided"
            
        context = {
            'court_name': reservation.court.name,
            'time': reservation.start_time.strftime('%H:%M')
        }
        return self.send_message(
            reservation.user.whatsapp,
            'reservation_reminder',
            context
        )
