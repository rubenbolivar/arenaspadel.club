from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('reservation/<int:reservation_id>/payment/', 
         views.payment_method_selection, 
         name='payment_select'),
    
    path('create/<int:reservation_id>/', views.payment_create, name='payment_create'),
    
    path('reservation/<int:reservation_id>/confirm/',
         views.manual_payment_confirmation,
         name='payment_confirm'),
    
    path('webhook/stripe/',
         views.stripe_webhook,
         name='payment_webhook'),
    
    path('reservation/<int:reservation_id>/success/',
         views.payment_success,
         name='payment_success'),
    
    path('reservation/<int:reservation_id>/cancel/',
         views.payment_cancel,
         name='payment_cancel'),
    
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('validate/<int:payment_id>/', views.payment_validate, name='payment_validate'),
    
    # Rutas para notificaciones por WhatsApp
    path('reservation/<int:reservation_id>/whatsapp/', 
         views.whatsapp_notification, 
         name='whatsapp_notification'),
    
    # Nueva ruta para notificar pagos por WhatsApp
    path('reservation/<int:reservation_id>/notify-payment-whatsapp/',
         views.notify_payment_whatsapp,
         name='notify_payment_whatsapp'),
]
