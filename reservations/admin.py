from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from .models import Court, Reservation, RentalItem, ReservationRental

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'hourly_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'number')
    ordering = ('number',)

@admin.register(RentalItem)
class RentalItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'price', 'available')
    list_filter = ('item_type', 'available')
    search_fields = ('name', 'description')
    ordering = ('item_type', 'name')
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" height="150" />')
        return _("No hay imagen")
    image_preview.short_description = _("Vista previa de imagen")

class ReservationRentalInline(admin.TabularInline):
    model = ReservationRental
    extra = 0
    fields = ('item', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'court', 'user', 'start_time', 'end_time', 'status', 'get_total_price')
    list_filter = ('status', 'court', 'start_time')
    search_fields = ('id', 'user__username', 'user__first_name', 'user__last_name', 'court__name')
    ordering = ('-start_time',)
    date_hierarchy = 'start_time'
    inlines = [ReservationRentalInline]
    
    fieldsets = (
        (None, {
            'fields': ('id', 'court', 'user')
        }),
        (_('Reservation Details'), {
            'fields': ('start_time', 'end_time', 'status')
        }),
    )
    
    readonly_fields = ('id',)
    
    def get_total_price(self, obj):
        return obj.total_price
    get_total_price.short_description = _('Total Price')

@admin.register(ReservationRental)
class ReservationRentalAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'item', 'quantity', 'unit_price', 'total_price')
    list_filter = ('item', 'reservation__status')
    search_fields = ('reservation__id', 'item__name')
    readonly_fields = ('total_price',)
