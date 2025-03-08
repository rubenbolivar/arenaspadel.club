from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Payment, ExchangeRate
from .forms import PaymentForm, PaymentValidationForm
from django.contrib import messages
from django.utils import timezone

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentForm
    list_display = ['id', 'user', 'get_reservation_id', 'reservation', 'amount', 'payment_method', 'status', 'is_cash_payment', 'view_proof_image', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['id', 'user__username', 'user__email', 'reservation__id', 'reservation__court__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['approve_payments', 'reject_payments']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'reservation', 'amount')
        }),
        (_('Payment Details'), {
            'fields': ('payment_method', 'status', 'proof_image', 'notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'APPROVED'
            payment.save()
            
            # Actualizar el estado de la reserva
            if payment.reservation:
                payment.reservation.status = 'confirmed'
                payment.reservation.save()
    approve_payments.short_description = _("Aprobar pagos seleccionados")

    def reject_payments(self, request, queryset):
        for payment in queryset:
            payment.status = 'REJECTED'
            payment.save()
    reject_payments.short_description = _("Rechazar pagos seleccionados")

    def view_proof_image(self, obj):
        if obj.proof_image:
            # Cambiar el enlace para abrir un modal en lugar de una nueva ventana
            return format_html(
                '<a href="javascript:void(0);" onclick="showImageModal(\'{}\', \'{}\')" class="view-proof-link">View Proof</a>',
                obj.proof_image.url,
                f"Comprobante de pago #{obj.id}"
            )
        return "-"
    view_proof_image.short_description = _('Proof of Payment')
    
    def get_reservation_id(self, obj):
        """Mostrar el ID de la reserva de forma destacada"""
        if obj.reservation:
            return f"#{obj.reservation.id}"
        return "-"
    get_reservation_id.short_description = _('Reserva #')
    
    def is_cash_payment(self, obj):
        """Indicador visual para pagos en efectivo"""
        if obj.payment_method == 'CASH':
            if obj.status == 'PENDING':
                return format_html('<span style="color:red;"><i class="fas fa-money-bill"></i> Efectivo pendiente</span>')
            elif obj.status == 'APPROVED':
                return format_html('<span style="color:green;"><i class="fas fa-money-bill"></i> Efectivo pagado</span>')
            return format_html('<span><i class="fas fa-money-bill"></i> Efectivo</span>')
        return ""
    is_cash_payment.short_description = _('Efectivo')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'reservation', 'amount', 'payment_method')
        return self.readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        if obj and obj.status in ['pending', 'in_review']:
            kwargs['form'] = PaymentValidationForm
        return super().get_form(request, obj, **kwargs)

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }
        js = ('js/admin_custom.js',)

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['rate', 'source', 'is_active', 'obtained_automatically', 'created_at']
    list_filter = ['source', 'is_active', 'obtained_automatically', 'created_at']
    search_fields = ['source']
    readonly_fields = ['created_at', 'updated_at', 'obtained_automatically']
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['activate_rates', 'update_rate_from_bcv']
    
    fieldsets = (
        (None, {
            'fields': ('rate', 'source', 'source_url', 'is_active')
        }),
        (_('Información adicional'), {
            'fields': ('obtained_automatically', 'created_at', 'updated_at')
        }),
    )
    
    def activate_rates(self, request, queryset):
        """
        Activa las tasas seleccionadas y desactiva todas las demás
        """
        if queryset.count() > 1:
            self.message_user(request, _("Solo puede activar una tasa a la vez"), level=messages.ERROR)
            return
            
        rate = queryset.first()
        # Desactivar todas las tasas activas
        ExchangeRate.objects.filter(is_active=True).update(is_active=False)
        # Activar la tasa seleccionada
        rate.is_active = True
        rate.save()
        
        self.message_user(request, _("La tasa ha sido activada exitosamente"), level=messages.SUCCESS)
    
    activate_rates.short_description = _("Activar tasas seleccionadas")
    
    def update_rate_from_bcv(self, request, queryset):
        """
        Actualiza la tasa desde el BCV mediante web scraping
        """
        from .exchange_rates import get_bcv_exchange_rate_direct
        
        try:
            rate_value = get_bcv_exchange_rate_direct()
            if rate_value:
                # Desactivar todas las tasas activas
                ExchangeRate.objects.filter(is_active=True).update(is_active=False)
                
                # Crear una nueva tasa con el valor obtenido
                new_rate = ExchangeRate.objects.create(
                    rate=rate_value,
                    source='BCV (Web)',
                    source_url='https://www.bcv.org.ve/',
                    is_active=True,
                    obtained_automatically=True
                )
                
                self.message_user(
                    request, 
                    _("Tasa actualizada exitosamente desde el BCV: %(rate)s") % {'rate': new_rate.rate},
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request, 
                    _("No se pudo obtener la tasa desde el BCV. Intente ingresarla manualmente."), 
                    level=messages.ERROR
                )
        except Exception as e:
            self.message_user(
                request, 
                _("Error al obtener la tasa: %(error)s") % {'error': str(e)},
                level=messages.ERROR
            )
    
    update_rate_from_bcv.short_description = _("Actualizar tasa desde el BCV")
