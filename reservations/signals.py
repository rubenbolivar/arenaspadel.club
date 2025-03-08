"""
Signal handlers for Reservation model.

This module contains the signal handlers that trigger notifications
when reservations are created or modified.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reservation
from notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Reservation)
def notify_reservation_status(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications when a reservation is created or modified.
    
    Args:
        sender: The model class (Reservation)
        instance: The actual reservation instance
        created: Boolean indicating if this is a new instance
        kwargs: Additional keyword arguments
    """
    try:
        notification_service = NotificationService()
        notification_service.notify_reservation_status(instance, created)
    except Exception as e:
        logger.error(f"Error in reservation notification signal: {str(e)}")
