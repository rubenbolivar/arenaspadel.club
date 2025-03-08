from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import pytz

# Create your models here.

class Court(models.Model):
    name = models.CharField(_('name'), max_length=50)
    number = models.IntegerField(_('court number'), unique=True)
    is_active = models.BooleanField(_('active'), default=True)
    hourly_rate = models.DecimalField(_('hourly rate'), max_digits=10, decimal_places=2, default=15.00)
    
    class Meta:
        verbose_name = _('court')
        verbose_name_plural = _('courts')
        ordering = ['number']
    
    def __str__(self):
        return self.name

class RentalItem(models.Model):
    """
    Modelo para los artículos disponibles para alquiler (palas y pelotas).
    """
    ITEM_TYPES = [
        ('PADDLE', _('Pala')),
        ('BALLS', _('Pack de Pelotas')),
    ]
    
    name = models.CharField(_('nombre'), max_length=100)
    item_type = models.CharField(_('tipo'), max_length=20, choices=ITEM_TYPES)
    price = models.DecimalField(_('precio'), max_digits=10, decimal_places=2)
    description = models.TextField(_('descripción'), blank=True, null=True)
    image = models.ImageField(_('imagen'), upload_to='rental_items/', blank=True, null=True)
    available = models.BooleanField(_('disponible'), default=True)
    
    class Meta:
        verbose_name = _('artículo de alquiler')
        verbose_name_plural = _('artículos de alquiler')
        ordering = ['item_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()}) - ${self.price}"

class ReservationRental(models.Model):
    """
    Modelo para relacionar los artículos alquilados con una reserva.
    """
    reservation = models.ForeignKey(
        'Reservation',
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name=_('reserva')
    )
    item = models.ForeignKey(
        RentalItem,
        on_delete=models.PROTECT,
        verbose_name=_('artículo')
    )
    quantity = models.PositiveIntegerField(_('cantidad'), default=1)
    unit_price = models.DecimalField(_('precio unitario'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('alquiler')
        verbose_name_plural = _('alquileres')
    
    def __str__(self):
        return f"{self.reservation.id} - {self.item.name} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.unit_price * Decimal(str(self.quantity))
    
    def save(self, *args, **kwargs):
        # Si no se ha establecido el precio unitario, usar el precio actual del artículo
        if not self.unit_price:
            self.unit_price = self.item.price
        super().save(*args, **kwargs)

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', _('Pending Payment')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('user')
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('court')
    )
    start_time = models.DateTimeField(_('start time'))
    end_time = models.DateTimeField(_('end time'))
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_payment'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('reservation')
        verbose_name_plural = _('reservations')
        ordering = ['-start_time']
        
    def __str__(self):
        return f"{self.court.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        if self.start_time and self.end_time:
            # Check if end time is after start time
            if self.end_time <= self.start_time:
                raise ValidationError(_('End time must be after start time'))
            
            # Check if start time is in the future
            # Add a small buffer (1 minute) to prevent validation errors due to processing time
            now = timezone.now()
            if self.start_time < now - timezone.timedelta(minutes=1):
                raise ValidationError(_('Start time must be in the future'))
            
            # Check if reservation is within operating hours (7:00 AM - 11:00 PM)
            # Convertir a la zona horaria local (America/Caracas)
            local_tz = pytz.timezone('America/Caracas')
            local_start_time = self.start_time.astimezone(local_tz)
            local_end_time = self.end_time.astimezone(local_tz)
            
            if local_start_time.hour < 7 or local_end_time.hour > 23 or (local_end_time.hour == 23 and local_end_time.minute > 0):
                raise ValidationError(_('Reservations are only available between 7:00 AM and 11:00 PM'))
            
            # Check for overlapping reservations
            overlapping = Reservation.objects.filter(
                court=self.court,
                status__in=['confirmed', 'pending_payment'],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError(_('This time slot is already reserved'))
    
    @property
    def total_price(self):
        # Precio base por el alquiler de la cancha
        court_price = Decimal(str((self.end_time - self.start_time).total_seconds())) / Decimal('3600') * self.court.hourly_rate
        
        # Sumar el precio de los artículos alquilados
        rental_price = sum(rental.total_price for rental in self.rentals.all())
        
        return court_price + rental_price
    
    @property
    def total_rental_price(self):
        """
        Calcula el precio total de los artículos alquilados para esta reserva.
        """
        return sum(rental.total_price for rental in self.rentals.all())

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
