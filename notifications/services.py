"""
Notification Service for ArenaPadel

This module provides a unified notification service that handles both email and WhatsApp
notifications for the ArenaPadel platform. It centralizes all notification logic and
provides a single interface for sending different types of notifications.

Usage:
    notification_service = NotificationService()
    
    # Send notifications for a reservation
    notification_service.notify_reservation_status(reservation, created=True)
    
    # Send a reminder
    notification_service.send_reservation_reminder(reservation)

Dependencies:
    - Django's email backend
    - Twilio WhatsApp API (via WhatsAppNotifier)
    - Django Settings (EMAIL and TWILIO configurations)
"""

from django.core.mail import send_mail
from django.conf import settings
from .whatsapp import WhatsAppNotifier
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Unified service for handling all types of notifications in ArenaPadel.
    
    This service handles:
    - Email notifications to users and admins
    - WhatsApp notifications for reservations and reminders
    
    Attributes:
        whatsapp (WhatsAppNotifier): Instance of WhatsApp notification handler
    """

    def __init__(self):
        """Initialize the notification service with WhatsApp capability."""
        self.whatsapp = WhatsAppNotifier()

    def notify_reservation_status(self, reservation, created=False):
        """
        Send notifications when a reservation is created or its status changes.
        
        Args:
            reservation (Reservation): The reservation instance that triggered the notification
            created (bool): Whether this is a new reservation
        
        Returns:
            bool: True if all notifications were sent successfully, False otherwise
        """
        try:
            subject = None
            message = None
            user_name = reservation.user.get_full_name() or reservation.user.email
            
            if created:
                subject = f'Nueva Reserva - {user_name} - {reservation.court.name}'
                message = f'''Se ha creado una nueva reserva:
                
Usuario: {user_name}
Cancha: {reservation.court.name}
Fecha: {reservation.start_time.strftime('%d/%m/%Y')}
Hora: {reservation.start_time.strftime('%H:%M')} - {reservation.end_time.strftime('%H:%M')}
Estado: {reservation.get_status_display()}
Monto: ${reservation.total_price}'''
            
            elif reservation.status == 'confirmed':
                subject = f'Reserva Confirmada - {user_name} - {reservation.court.name}'
                message = f'''Tu reserva ha sido confirmada:
                
Usuario: {user_name}
Cancha: {reservation.court.name}
Fecha: {reservation.start_time.strftime('%d/%m/%Y')}
Hora: {reservation.start_time.strftime('%H:%M')} - {reservation.end_time.strftime('%H:%M')}
Estado: Confirmada
Monto: ${reservation.total_price}'''

                # Send WhatsApp confirmation
                whatsapp_sent = self.whatsapp.send_reservation_confirmation(reservation)
                if not whatsapp_sent[0]:
                    logger.error(f"WhatsApp confirmation failed: {whatsapp_sent[1]}")
            
            elif reservation.status == 'cancelled':
                subject = f'Reserva Cancelada - {user_name} - {reservation.court.name}'
                message = f'''Tu reserva ha sido cancelada:
                
Usuario: {user_name}
Cancha: {reservation.court.name}
Fecha: {reservation.start_time.strftime('%d/%m/%Y')}
Hora: {reservation.start_time.strftime('%H:%M')} - {reservation.end_time.strftime('%H:%M')}'''

            if subject and message:
                return self._send_email_notifications(subject, message, reservation)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in notify_reservation_status: {str(e)}")
            return False

    def send_reservation_reminder(self, reservation):
        """
        Send reminder notifications via both WhatsApp and email.
        
        Args:
            reservation (Reservation): The reservation to send reminders for
        
        Returns:
            tuple: (bool, str) indicating success/failure and any error message
        """
        try:
            # Send WhatsApp reminder
            whatsapp_sent = self.whatsapp.send_reservation_reminder(reservation)
            if not whatsapp_sent[0]:
                logger.error(f"WhatsApp reminder failed: {whatsapp_sent[1]}")
            
            # Send email reminder
            user_name = reservation.user.get_full_name() or reservation.user.email
            subject = f'Recordatorio de Reserva - {reservation.court.name}'
            message = f'''Recordatorio de tu reserva para hoy:
            
Cancha: {reservation.court.name}
Hora: {reservation.start_time.strftime('%H:%M')}

¡Te esperamos!'''

            email_sent = self._send_email_notifications(subject, message, reservation)
            
            return whatsapp_sent[0] and email_sent, "Notifications sent"
            
        except Exception as e:
            error_msg = f"Error in send_reservation_reminder: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _send_email_notifications(self, subject, message, reservation):
        """
        Private method to handle email notifications to both admin and user.
        
        Args:
            subject (str): Email subject
            message (str): Email body
            reservation (Reservation): The reservation instance
        
        Returns:
            bool: True if emails were sent successfully, False otherwise
        """
        try:
            # Send to admin
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True
            )
            
            # Send to user
            if reservation.user.email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [reservation.user.email],
                    fail_silently=True
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notifications: {str(e)}")
            return False
