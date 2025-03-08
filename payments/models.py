from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from reservations.models import Reservation

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('PAGO_MOVIL', _('Pago Móvil')),
        ('ZELLE', _('Zelle')),
        ('CASH', _('Efectivo')),
        ('STRIPE', _('Stripe')),
        ('PAYPAL', _('PayPal')),
    ]

    PAYMENT_STATUS = [
        ('PENDING', _('Pendiente')),
        ('REVIEWING', _('En Revisión')),
        ('APPROVED', _('Aprobado')),
        ('REJECTED', _('Rechazado')),
        ('CANCELLED', _('Cancelado')),
    ]
    
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payment_set',
        verbose_name=_('reservation')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('user')
    )
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHODS
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )
    proof_image = models.ImageField(
        _('proof of payment'),
        upload_to='payment_proofs/',
        null=True,
        blank=True
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='validated_payments'
    )
    validated_at = models.DateTimeField(_('validated at'), null=True, blank=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.get_payment_method_display()} - {self.get_status_display()}"

class ExchangeRate(models.Model):
    """
    Modelo para almacenar las tasas de cambio del BCV (USD a VES)
    """
    rate = models.DecimalField(_('tasa'), max_digits=12, decimal_places=4, 
                                help_text=_('Tasa de cambio USD/VES del BCV'))
    source = models.CharField(_('fuente'), max_length=100, default='BCV',
                              help_text=_('Fuente de la tasa de cambio'))
    source_url = models.URLField(_('URL fuente'), blank=True, null=True,
                                help_text=_('URL de la fuente de donde se obtuvo la tasa'))
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    is_active = models.BooleanField(_('activa'), default=True,
                                    help_text=_('Indica si es la tasa activa actual'))
    obtained_automatically = models.BooleanField(_('obtenida automáticamente'), default=True,
                                               help_text=_('Indica si la tasa fue obtenida automáticamente o ingresada manualmente'))
    
    class Meta:
        verbose_name = _('Tasa de Cambio')
        verbose_name_plural = _('Tasas de Cambio')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.rate} - {self.source} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Si esta tasa se está marcando como activa, desactivamos todas las demás
        if self.is_active:
            ExchangeRate.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_latest_rate(cls):
        """
        Obtiene la tasa de cambio activa más reciente
        """
        return cls.objects.filter(is_active=True).order_by('-created_at').first()
